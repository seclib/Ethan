use chrono::Utc;
use clap::Parser;
use serde::Serialize;
use std::net::SocketAddr;
use std::io::{Read, Write};
use std::net::TcpListener;
use tracing::{error, info, warn};

#[derive(Parser, Debug, Clone)]
#[command(name = "ethan-health", version, about = "ETHAN Rust health/diagnostics prototype")]
pub struct Config {
    #[arg(long, env = "ETHAN_HEALTH_BIND", default_value = "127.0.0.1")]
    bind: String,

    #[arg(long, env = "ETHAN_HEALTH_PORT", default_value_t = 18081)]
    port: u16,

    #[arg(long, env = "ETHAN_HEALTH_LOG_LEVEL", default_value = "info")]
    log_level: String,

    #[arg(long, env = "ETHAN_HEALTH_SERVICE_NAME", default_value = "ethan-health")]
    service_name: String,
}

#[derive(Serialize)]
struct HealthResponse {
    status: &'static str,
    service: String,
    version: &'static str,
    timestamp: String,
    ready: bool,
}

#[derive(Serialize)]
struct ErrorResponse {
    code: &'static str,
    message: String,
    details: serde_json::Value,
    request_id: String,
    retryable: bool,
}

#[derive(Serialize)]
struct DiagnosticsResponse {
    service: String,
    version: &'static str,
    contract: &'static str,
    mode: &'static str,
    bind: String,
    port: u16,
}

fn uuid_simple() -> String {
    format!("{}-{}", Utc::now().timestamp_millis(), std::process::id())
}

fn validate_config(config: &Config) -> Result<SocketAddr, String> {
    if config.bind.trim().is_empty() {
        return Err("bind address must not be empty".to_string());
    }
    if config.port == 0 {
        return Err("port must be non-zero".to_string());
    }
    format!("{}:{}", config.bind, config.port)
        .parse()
        .map_err(|e| format!("invalid socket address '{}:{}': {}", config.bind, config.port, e))
}

fn json_body<T: Serialize>(value: &T) -> String {
    serde_json::to_string(value).unwrap_or_else(|_| "{}".to_string())
}

fn http_response(status: u16, reason: &str, body: String) -> String {
    format!(
        "HTTP/1.1 {} {}\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{}",
        status,
        reason,
        body.len(),
        body
    )
}

fn error_body(code: &'static str, message: impl Into<String>, retryable: bool) -> String {
    let body = ErrorResponse {
        code,
        message: message.into(),
        details: serde_json::Value::Object(Default::default()),
        request_id: uuid_simple(),
        retryable,
    };
    json_body(&body)
}

// Fonction pure testable: retourne le statut et le corps pour une route.
pub fn route_response(config: &Config, method: &str, path: &str) -> (u16, String) {
    match (method, path) {
        ("GET", "/health") | ("GET", "/health/live") => {
            let body = HealthResponse {
                status: "ok",
                service: config.service_name.clone(),
                version: env!("CARGO_PKG_VERSION"),
                timestamp: Utc::now().to_rfc3339(),
                ready: true,
            };
            (200, json_body(&body))
        }
        ("GET", "/health/ready") => {
            let body = HealthResponse {
                status: "ready",
                service: config.service_name.clone(),
                version: env!("CARGO_PKG_VERSION"),
                timestamp: Utc::now().to_rfc3339(),
                ready: true,
            };
            (200, json_body(&body))
        }
        ("GET", "/v1/diagnostics/version") => {
            let body = DiagnosticsResponse {
                service: config.service_name.clone(),
                version: env!("CARGO_PKG_VERSION"),
                contract: "ethan.p3.health.v1",
                mode: "isolated-prototype",
                bind: config.bind.clone(),
                port: config.port,
            };
            (200, json_body(&body))
        }
        ("GET", "/v1/diagnostics/timeout") => {
            // L'attente est simulée côté appelant/tests; ici réponse directe et déterministe.
            (200, json_body(&serde_json::json!({"status":"completed","delay_ms":50})))
        }
        _ => {
            let body = error_body("ETHAN_NOT_FOUND", format!("unknown route: {} {}", method, path), false);
            (404, body)
        }
    }
}

fn init_tracing(config: &Config) {
    let env_filter = tracing_subscriber::EnvFilter::try_from_default_env()
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new(config.log_level.clone()));
    tracing_subscriber::fmt()
        .with_env_filter(env_filter)
        .with_target(true)
        .init();
}

fn handle_connection(config: Config, mut stream: std::net::TcpStream) {
    let mut buf = [0_u8; 4096];
    let n = match stream.read(&mut buf) {
        Ok(0) => return,
        Ok(n) => n,
        Err(e) => {
            warn!(error = %e, "lecture connexion échouée");
            return;
        }
    };
    let request = String::from_utf8_lossy(&buf[..n]);
    let mut lines = request.lines();
    let request_line = lines.next().unwrap_or("");
    let mut parts = request_line.split_whitespace();
    let method = parts.next().unwrap_or("");
    let path = parts.next().unwrap_or("");

    let (status, body) = if path == "/v1/diagnostics/timeout" {
        std::thread::sleep(std::time::Duration::from_millis(50));
        (200, json_body(&serde_json::json!({"status":"completed","delay_ms":50})))
    } else {
        route_response(&config, method, path)
    };

    let reason = match status {
        200 => "OK",
        404 => "Not Found",
        _ => "Error",
    };
    let response = http_response(status, reason, body);
    let _ = stream.write_all(response.as_bytes());
    let _ = stream.flush();
}

fn main() {
    let config = Config::parse();
    init_tracing(&config);

    let addr = match validate_config(&config) {
        Ok(a) => a,
        Err(e) => {
            error!(error = %e, "configuration invalide");
            std::process::exit(2);
        }
    };

    info!(bind = %config.bind, port = config.port, service = %config.service_name, "démarrage ethan-health");
    info!(route = "/health", "endpoint santé disponible");
    info!(route = "/health/ready", "endpoint readiness disponible");
    info!(route = "/v1/diagnostics/version", "diagnostic non destructif disponible");

    let listener = match TcpListener::bind(addr) {
        Ok(l) => l,
        Err(e) => {
            error!(error = %e, addr = %addr, "impossible d'écouter");
            std::process::exit(1);
        }
    };

    for incoming in listener.incoming() {
        match incoming {
            Ok(stream) => {
                let peer = stream.peer_addr().ok();
                let config = config.clone();
                std::thread::spawn(move || {
                    if let Some(p) = peer {
                        info!(peer = %p, "connexion entrante");
                    }
                    handle_connection(config, stream);
                });
            }
            Err(e) => warn!(error = %e, "accept échoué"),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_config() -> Config {
        Config {
            bind: "127.0.0.1".to_string(),
            port: 18081,
            log_level: "info".to_string(),
            service_name: "ethan-health-test".to_string(),
        }
    }

    #[test]
    fn validates_zero_port() {
        let mut c = test_config();
        c.port = 0;
        assert!(validate_config(&c).is_err());
    }

    #[test]
    fn validates_empty_bind() {
        let mut c = test_config();
        c.bind = "   ".to_string();
        assert!(validate_config(&c).is_err());
    }

    #[test]
    fn health_route_returns_json_contract() {
        let (status, body) = route_response(&test_config(), "GET", "/health");
        assert_eq!(status, 200);
        let value: serde_json::Value = serde_json::from_str(&body).unwrap();
        assert_eq!(value["status"], "ok");
        assert_eq!(value["service"], "ethan-health-test");
        assert!(value["timestamp"].is_string());
        assert_eq!(value["ready"], true);
    }

    #[test]
    fn readiness_route() {
        let (status, body) = route_response(&test_config(), "GET", "/health/ready");
        assert_eq!(status, 200);
        let value: serde_json::Value = serde_json::from_str(&body).unwrap();
        assert_eq!(value["status"], "ready");
    }

    #[test]
    fn diagnostics_version_route() {
        let (status, body) = route_response(&test_config(), "GET", "/v1/diagnostics/version");
        assert_eq!(status, 200);
        let value: serde_json::Value = serde_json::from_str(&body).unwrap();
        assert_eq!(value["contract"], "ethan.p3.health.v1");
        assert_eq!(value["port"], 18081);
    }

    #[test]
    fn unknown_route_returns_404_contract() {
        let (status, body) = route_response(&test_config(), "GET", "/nope");
        assert_eq!(status, 404);
        let value: serde_json::Value = serde_json::from_str(&body).unwrap();
        assert_eq!(value["code"], "ETHAN_NOT_FOUND");
        assert_eq!(value["retryable"], false);
    }
}
