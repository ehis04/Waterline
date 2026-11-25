import { render, screen } from "@testing-library/react";
import { FrequencyStatement } from "@/components/FrequencyStatement";

describe("FrequencyStatement", () => {
  it("renders seconds for intervals under a minute", () => {
    render(<FrequencyStatement intervalMs={30000} />);
    expect(screen.getByText("Updated every 30 seconds")).toBeInTheDocument();
  });

  it("renders singular unit for 1 minute", () => {
    render(<FrequencyStatement intervalMs={60000} />);
    expect(screen.getByText("Updated every 1 minute")).toBeInTheDocument();
  });

  it("renders plural minutes for 5 minutes", () => {
    render(<FrequencyStatement intervalMs={300000} />);
    expect(screen.getByText("Updated every 5 minutes")).toBeInTheDocument();
  });

  it("renders hours for intervals >= 1 hour", () => {
    render(<FrequencyStatement intervalMs={7200000} />);
    expect(screen.getByText("Updated every 2 hours")).toBeInTheDocument();
  });
});
