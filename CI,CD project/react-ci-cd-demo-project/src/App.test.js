import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders marwiz link", () => {
  render(<App />);

  const linkElement = screen.getByText(/visit our website/i);
  expect(linkElement).toBeInTheDocument();
});
