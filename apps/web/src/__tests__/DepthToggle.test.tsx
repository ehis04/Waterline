import { render, screen, fireEvent } from "@testing-library/react";
import { DepthToggle } from "@/components/DepthToggle";

describe("DepthToggle", () => {
  it("renders depth options 1, 2, and 3+", () => {
    render(<DepthToggle onChange={jest.fn()} />);
    expect(screen.getByRole("button", { name: "1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "2" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "3+" })).toBeInTheDocument();
  });

  it("calls onChange with selected depth when clicked", () => {
    const handleChange = jest.fn();
    render(<DepthToggle onChange={handleChange} />);

    fireEvent.click(screen.getByRole("button", { name: "2" }));
    expect(handleChange).toHaveBeenCalledWith(2);

    fireEvent.click(screen.getByRole("button", { name: "3+" }));
    expect(handleChange).toHaveBeenCalledWith(3);

    fireEvent.click(screen.getByRole("button", { name: "1" }));
    expect(handleChange).toHaveBeenCalledWith(1);
  });
});
