import { render, screen } from "@testing-library/react";

import EngineeringMemoryPage from "@/app/engineering-memory/page";

global.fetch = jest.fn(() =>
	Promise.resolve({
		ok: true,
		status: 200,
		json: async () => ({
			status: "ok",
			results: [{ id: "EVT-1", title: "test event", status: "recorded" }],
		}),
	} as unknown as Response),
);

describe("EngineeringMemoryPage", () => {
	it("renders real module labels", () => {
		render(<EngineeringMemoryPage />);
		expect(screen.getByText("Engineering Memory")).toBeInTheDocument();
		expect(screen.getByText("Événements")).toBeInTheDocument();
	});
});
