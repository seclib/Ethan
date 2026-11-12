import fs from "fs";
import path from "path";

describe("service worker cache strategy", () => {
  const swPath = path.resolve(process.cwd(), "public", "sw.js");

  it("keeps navigation requests network-first", () => {
    const source = fs.readFileSync(swPath, "utf8");

    expect(source).toContain('req.mode === "navigate"');
    expect(source).toContain("fetch(req)");
    expect(source).toContain("caches.match");
  });

  it("does not cache-first the application shell", () => {
    const source = fs.readFileSync(swPath, "utf8");

    expect(source).not.toContain('cache.addAll(["/", "/agents", "/config"');
  });
});
