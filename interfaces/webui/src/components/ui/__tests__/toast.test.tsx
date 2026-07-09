import { render, screen } from "@testing-library/react";
import { ToastProvider, useToast } from "../toast";

function ToastConsumer() {
  const { addToast } = useToast();
  return <button onClick={() => addToast({ title: "Test", message: "Message", type: "success" })}>Show</button>;
}

describe("Toast", () => {
  it("renders toast when addToast is called", () => {
    render(
      <ToastProvider>
        <ToastConsumer />
      </ToastProvider>
    );
    screen.getByText("Show").click();
    expect(screen.getByText("Test")).toBeInTheDocument();
    expect(screen.getByText("Message")).toBeInTheDocument();
  });
});