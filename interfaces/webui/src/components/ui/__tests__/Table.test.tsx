import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "@jest/globals";
import { Table } from "../table";

describe("Table", () => {
  it("renders table element", () => {
    render(
      <Table>
        <tbody>
          <tr>
            <td>Cell</td>
          </tr>
        </tbody>
      </Table>
    );
    expect(screen.getByText("Cell")).toBeTruthy();
  });
});