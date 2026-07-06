"use client";

export function useExport() {
  const exportCSV = (filename: string, rows: Record<string, unknown>[]) => {
    if (!rows.length) return;
    const keys = Object.keys(rows[0]);
    const csv = [
      keys.join(","),
      ...rows.map((r) =>
        keys
          .map((k) => {
            const v = r[k];
            if (v === null || v === undefined) return "";
            const s = String(v);
            return s.includes(",") || s.includes('"') || s.includes("\n")
              ? `"${s.replace(/"/g, '""')}"`
              : s;
          })
          .join(",")
      ),
    ].join("\n");
    download(`${filename}.csv`, csv, "text/csv");
  };

  const exportJSON = (filename: string, data: unknown) => {
    const json = JSON.stringify(data, null, 2);
    download(`${filename}.json`, json, "application/json");
  };

  return { exportCSV, exportJSON };
}

function download(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}