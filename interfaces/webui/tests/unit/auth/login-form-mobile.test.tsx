import * as React from "react";
import { render, screen } from "@testing-library/react";

import { LoginForm } from "@/app/(auth)/login/components/login-form";

describe("LoginForm mobile input hardening", () => {
  it("disables automatic capitalization and correction on credentials", () => {
    render(<LoginForm onSubmit={jest.fn()} isLoading={false} error={null} />);
    expect(screen.getByLabelText(/Operator ID/i)).toHaveAttribute("autocapitalize", "none");
    expect(screen.getByLabelText(/Operator ID/i)).toHaveAttribute("autocorrect", "off");
    expect(screen.getByLabelText(/Password/i)).toHaveAttribute("autocapitalize", "none");
    expect(screen.getByLabelText(/Password/i)).toHaveAttribute("autocorrect", "off");
  });
});
