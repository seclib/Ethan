import { render, screen, fireEvent } from "@testing-library/react";
import { TasksWidget } from "@/components/shared/tasks-widget";
import type { Task } from "@/types";

const mockTasks: Task[] = [
  {
    id: "task-1",
    goal_id: "goal-1",
    title: "Test task 1",
    description: "Description 1",
    status: "pending",
    depends_on: [],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
  {
    id: "task-2",
    goal_id: "goal-1",
    title: "Test task 2",
    status: "completed",
    depends_on: ["task-1"],
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

describe("TasksWidget", () => {
  it("renders tasks without crashing", () => {
    render(<TasksWidget tasks={[]} />);
    expect(screen.getByText("Tasks")).toBeInTheDocument();
  });

  it("displays task count", () => {
    render(<TasksWidget tasks={mockTasks} />);
    expect(screen.getByText("1/2")).toBeInTheDocument();
  });

  it("shows progress bar", () => {
    render(<TasksWidget tasks={mockTasks} />);
    const progressBar = screen.getByRole("progressbar");
    expect(progressBar).toBeInTheDocument();
  });

  it("calls onTaskClick when task is clicked", () => {
    const handleClick = jest.fn();
    render(<TasksWidget tasks={mockTasks} onTaskClick={handleClick} />);
    
    const taskElement = screen.getByText("Test task 1");
    fireEvent.click(taskElement.closest("div")!);
    
    expect(handleClick).toHaveBeenCalledWith(mockTasks[0]);
  });

  it("respects maxItems prop", () => {
    render(<TasksWidget tasks={mockTasks} maxItems={1} />);
    expect(screen.getByText("Test task 1")).toBeInTheDocument();
    expect(screen.getByText("Test task 2")).not.toBeInTheDocument();
  });
});