declare module "@testing-library/react" {
  export * from "@testing-library/react";
  export const screen: typeof import("@testing-library/react").screen;
  export const render: typeof import("@testing-library/react").render;
  export const fireEvent: typeof import("@testing-library/react").fireEvent;
}