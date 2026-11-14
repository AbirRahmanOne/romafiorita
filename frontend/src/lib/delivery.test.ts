import { describe, expect, it } from "vitest";
import { classifyCap } from "./delivery";

describe("classifyCap", () => {
  it("routes Rome CAP 001xx to own riders", () => {
    expect(classifyCap("00187")).toBe("ROME");
    expect(classifyCap("00100")).toBe("ROME");
  });

  it("routes other Italian CAPs to courier", () => {
    expect(classifyCap("20121")).toBe("ITALY"); // Milan
    expect(classifyCap("80100")).toBe("ITALY"); // Naples
  });

  it("rejects non 5-digit input", () => {
    expect(classifyCap("7500")).toBe("UNSUPPORTED");
    expect(classifyCap("abcde")).toBe("UNSUPPORTED");
    expect(classifyCap("")).toBe("UNSUPPORTED");
  });

  it("trims surrounding whitespace", () => {
    expect(classifyCap("  00187 ")).toBe("ROME");
  });
});
