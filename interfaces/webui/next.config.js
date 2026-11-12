/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: { useTypeScriptCli: false },
  output: "standalone",
  turbopack: {
    root: process.cwd(),
  },
  // NOTE: le proxying /api/* → ETHAN API est assuré par le route handler
  // src/app/api/[...path]/route.ts (conversion cookie JWT → Bearer, SSE,
  // uploads binaires). Aucun rewrite ici : une destination malformée
  // casse le serveur ("Can not repeat path without a prefix and suffix").
  async redirects() {
    return [
      {
        source: "/gods-eye-view",
        destination: "/odin",
        permanent: true,
      },
      {
        source: "/workspace",
        destination: "/skills",
        permanent: false,
      },
    ];
  },
  async headers() {
    return [
      {
        // Le service worker doit toujours être revalidé pour que les
        // nouvelles versions du frontend soient détectées sans reboot.
        source: "/sw.js",
        headers: [
          {
            key: "Cache-Control",
            value: "no-cache, no-store, max-age=0, must-revalidate",
          },
          {
            key: "Service-Worker-Allowed",
            value: "/",
          },
        ],
      },
      {
        source: "/(.*)",
        headers: [
          {
            key: "X-Frame-Options",
            value: "DENY",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "X-XSS-Protection",
            value: "1; mode=block",
          },
          {
            key: "Referrer-Policy",
            value: "strict-origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
          {
            key: "Content-Security-Policy",
            value: "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' data:; connect-src 'self' ws: wss: http://localhost:8000 https://*; frame-ancestors 'none';",
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
