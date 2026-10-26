import * as fs from "fs";
import * as path from "path";

const LOCALES_DIR = path.join(__dirname, "..", "locales");
const SUPPORTED = ["en", "fr", "ru", "zh-CN", "ja", "ar"];

function loadJson(locale: string): Record<string, any> {
  return JSON.parse(fs.readFileSync(path.join(LOCALES_DIR, locale + ".json"), "utf-8"));
}

function flattenKeys(obj: Record<string, any>, prefix: string): string[] {
  const keys: string[] = [];
  for (const [k, v] of Object.entries(obj)) {
    const fullKey = prefix ? prefix + "." + k : k;
    if (typeof v === "object" && v !== null && !Array.isArray(v)) {
      keys.push(...flattenKeys(v, fullKey));
    } else {
      keys.push(fullKey);
    }
  }
  return keys;
}

describe("i18n catalogues", () => {
  it("all locale files are valid JSON", () => {
    for (const locale of SUPPORTED) {
      expect(() => loadJson(locale)).not.toThrow();
    }
  });

  it("all locales have the same keys as English", () => {
    const enKeys = new Set(flattenKeys(loadJson("en"), ""));
    for (const locale of SUPPORTED) {
      if (locale === "en") continue;
      const localeKeys = new Set(flattenKeys(loadJson(locale), ""));
      const missing = [...enKeys].filter((k) => !localeKeys.has(k));
      expect(missing).toEqual([]);
    }
  });

  it("no translation value is an empty string", () => {
    for (const locale of SUPPORTED) {
      const keys = flattenKeys(loadJson(locale), "");
      const messages = loadJson(locale);
      for (const key of keys) {
        const parts = key.split(".");
        let val: any = messages;
        for (const p of parts) val = val?.[p];
        expect(String(val).trim()).not.toBe("");
      }
    }
  });
});
