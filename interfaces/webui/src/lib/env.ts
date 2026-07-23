interface EnvConfig {
  NEXT_PUBLIC_API_URL: string;
  NEXT_PUBLIC_WS_URL: string;
  NEXT_PUBLIC_APP_NAME: string;
  NEXT_PUBLIC_ENV: "development" | "staging" | "production";
}

function validateUrl(value: string | undefined, name: string): string {
  if (!value) return name === "NEXT_PUBLIC_API_URL" ? "http://localhost:8000" : "ws://localhost:8000";
  return value;
}

function validateEnv(value: string | undefined): "development" | "staging" | "production" {
  if (value === "staging" || value === "production") return value;
  return "development";
}

export const env: EnvConfig = {
  NEXT_PUBLIC_API_URL: validateUrl(process.env.NEXT_PUBLIC_API_URL, "NEXT_PUBLIC_API_URL"),
  NEXT_PUBLIC_WS_URL: validateUrl(process.env.NEXT_PUBLIC_WS_URL, "NEXT_PUBLIC_WS_URL"),
  NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || "ETHAN",
  NEXT_PUBLIC_ENV: validateEnv(process.env.NEXT_PUBLIC_ENV),
};