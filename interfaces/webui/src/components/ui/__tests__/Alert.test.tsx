import React from "react";
import { render, screen } from "@testing-library/react";
import { Alert, AlertTitle, AlertDescription } from "../alert";

describe("Alert", () => {
  it("renders alert content", () => {
    render(
      <Alert>
        <AlertTitle>Title</AlertTitle>
        <AlertDescription>Description</AlertDescription>
      </Alert>
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText("Title")).toBeInTheDocument();
    expect(screen.getByText("Description")).toBeInTheDocument();
  });
});