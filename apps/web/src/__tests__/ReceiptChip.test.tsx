import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { ReceiptChip } from "@/components/ReceiptChip";

describe("ReceiptChip", () => {
  const fullHash = "a1b2c3d4e5f6a1b2c3d4";

  beforeEach(() => {
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn().mockResolvedValue(undefined),
      },
    });
  });

  it("displays the first 8 characters of the hash with accessible label", () => {
    render(<ReceiptChip hash={fullHash} />);
    const button = screen.getByRole("button", {
      name: `Receipt hash ${fullHash}`,
    });
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent("a1b2c3d4");
  });

  it("copies the full hash to clipboard on click", async () => {
    render(<ReceiptChip hash={fullHash} />);
    const button = screen.getByRole("button", {
      name: `Receipt hash ${fullHash}`,
    });
    fireEvent.click(button);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(fullHash);
    });
  });
});
