import { statusFromThreshold } from "../../src/components/dashboard/dashboard-card";

describe("statusFromThreshold", () => {
  it("returns normal when value is below warning threshold", () => {
    expect(statusFromThreshold(30, { warning: 50, critical: 80 })).toBe("normal");
  });

  it("returns warning when value is between warning and critical", () => {
    expect(statusFromThreshold(65, { warning: 50, critical: 80 })).toBe("warning");
  });

  it("returns critical when value exceeds critical threshold", () => {
    expect(statusFromThreshold(90, { warning: 50, critical: 80 })).toBe("critical");
  });

  it("inverts thresholds when invert=true (lower is worse)", () => {
    expect(statusFromThreshold(60, { warning: 85, critical: 70 }, true)).toBe("critical");
    expect(statusFromThreshold(80, { warning: 85, critical: 70 }, true)).toBe("warning");
    expect(statusFromThreshold(90, { warning: 85, critical: 70 }, true)).toBe("normal");
  });
});
