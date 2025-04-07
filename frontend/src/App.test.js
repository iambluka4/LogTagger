import { render, screen } from "@testing-library/react";
import App from "./App";

test("renders LogTagger app", () => {
  render(<App />);
  
  // Перевіряємо наявність тексту у футері, який точно є в додатку
  const footerElement = screen.getByText(/LogTagger - Automated Security Log Tagging Tool/i);
  expect(footerElement).toBeInTheDocument();
});
