use clap::Parser;
use serde_json::{json, Value};
use std::io::{self, Read};

#[derive(Parser, Debug, Clone)]
struct Config {
    #[arg(long)]
    input: Option<String>,
    #[arg(long)]
    validate_only: bool,
}

fn read_input(path: Option<&str>) -> String {
    match path {
        Some(p) => std::fs::read_to_string(p).unwrap_or_default(),
        None => {
            let mut buf = String::new();
            let _ = io::stdin().read_to_string(&mut buf);
            buf
        }
    }
}

fn is_executable(path: &str) -> bool {
    std::path::Path::new(path).is_file()
}

fn validate(payload: &Value) -> Value {
    let schema_ok = payload
        .get("schema_version")
        .and_then(Value::as_str)
        .map(|v| v == "ethan.capability.v1")
        .unwrap_or(false);
    let caps = payload
        .get("capabilities")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let mut errors = Vec::new();
    if !schema_ok {
        errors.push("invalid_schema_version");
    }
    if caps.is_empty() {
        errors.push("invalid_contract");
    }
    for cap in &caps {
        match cap.get("id").and_then(Value::as_str) {
            Some(id) if !id.is_empty() => {}
            _ => errors.push("invalid_contract"),
        }
    }
    if errors.is_empty() {
        json!({"ok": true, "total": caps.len(), "validation": "passed"})
    } else {
        json!({"ok": false, "error": errors[0], "errors": errors, "total": caps.len()})
    }
}

fn detect(payload: &Value) -> Value {
    let mut detection = Vec::new();
    let caps = payload
        .get("capabilities")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    if !caps.is_empty() {
        for cap in &caps {
            let id = cap.get("id").and_then(Value::as_str).unwrap_or("unknown");
            let executable = cap
                .get("python_executable")
                .or_else(|| cap.get("metadata").and_then(|m| m.get("python_executable")))
                .and_then(Value::as_str);
            let present = executable.map(is_executable).unwrap_or(false);
            detection.push(json!({
                "capability_id": id,
                "python_executable": executable,
                "interpreter_present": present,
                "status": if present { "INSTALLED" } else { "UNAVAILABLE" },
            }));
        }
    } else {
        if let Ok(entries) = std::fs::read_dir("/home/.ethan/isolated") {
            for entry in entries.into_iter().flatten() {
                let path = entry.path();
                if path.is_dir() {
                    let python = path.join("bin").join("python");
                    let python3 = path.join("bin").join("python3");
                    let executable = if python.is_file() { python } else if python3.is_file() { python3 } else { python };
                    let present = executable.is_file();
                    detection.push(json!({
                        "capability_id": entry.file_name().to_string_lossy(),
                        "python_executable": executable.display().to_string(),
                        "interpreter_present": present,
                        "status": if present { "INSTALLED" } else { "UNAVAILABLE" },
                    }));
                }
            }
        }
    }
    json!({"ok": true, "total": detection.len(), "detection": detection})
}

fn main() {
    let cfg = Config::parse();
    let input = read_input(cfg.input.as_deref());
    let payload: Value = serde_json::from_str(&input).unwrap_or(Value::Null);
    let result = if cfg.validate_only {
        validate(&payload)
    } else {
        detect(&payload)
    };
    println!("{}", serde_json::to_string(&result).unwrap());
}
