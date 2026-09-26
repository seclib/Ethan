/**
 * Tests WebUI — pont de vocabulaire des capacités (source : ETHAN Core).
 *
 * Invariants : les valeurs canoniques connues sont traduites pour l'affichage,
 * TOUTE valeur inconnue est rendue brute (le frontend ne décide jamais quelles
 * capacités existent).
 */

import {
	capabilityLabel,
	capabilityVariant,
	uniqueModelCapabilities,
} from "@/lib/llm/capabilities";

describe("capabilityLabel", () => {
	it("traduit le vocabulaire provider canonique", () => {
		expect(capabilityLabel("llm")).toBe("LLM");
		expect(capabilityLabel("vision")).toBe("Vision");
		expect(capabilityLabel("embedding")).toBe("Embeddings");
		expect(capabilityLabel("speech_to_text")).toBe("Speech-to-Text");
		expect(capabilityLabel("transcription")).toBe("Transcription");
	});

	it("traduit le vocabulaire modèle connu", () => {
		expect(capabilityLabel("chat")).toBe("Chat");
		expect(capabilityLabel("code")).toBe("Code");
		expect(capabilityLabel("reasoning")).toBe("Reasoning");
	});

	it("valeur inconnue rendue brute (jamais renommée ni masquée)", () => {
		expect(capabilityLabel("tool_calling")).toBe("tool_calling");
		expect(capabilityLabel("")).toBe("");
	});
});

describe("capabilityVariant", () => {
	it("variantes connues", () => {
		expect(capabilityVariant("llm")).toBe("info");
		expect(capabilityVariant("reasoning")).toBe("accent");
		expect(capabilityVariant("vision")).toBe("purple");
		expect(capabilityVariant("embedding")).toBe("success");
		expect(capabilityVariant("speech_to_text")).toBe("gold");
	});

	it("valeur inconnue → variante discrète", () => {
		expect(capabilityVariant("quantum")).toBe("dim");
	});
});

describe("uniqueModelCapabilities", () => {
	it("union triée, sans doublon, sans valeurs vides", () => {
		expect(
			uniqueModelCapabilities([
				{ capabilities: ["vision", "chat"] },
				{ capabilities: ["chat", "code"] },
				{ capabilities: ["", "vision"] },
			]),
		).toEqual(["chat", "code", "vision"]);
	});

	it("modèles sans capabilities ignorés", () => {
		expect(
			uniqueModelCapabilities([{ capabilities: [] }, {}, { capabilities: undefined }]),
		).toEqual([]);
	});
});
