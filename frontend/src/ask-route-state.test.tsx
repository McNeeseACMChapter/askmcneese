import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, Link } from "react-router-dom";
import { useState } from "react";
import { describe, expect, it } from "vitest";

function ShellWithAskState() {
  const [messages] = useState(["Where is the registrar?"]);
  return (
    <div>
      <nav>
        <Link to="/ask">Ask</Link>
        <Link to="/about">About</Link>
      </nav>
      <Routes>
        <Route path="/ask" element={<div data-testid="ask">{messages[0]}</div>} />
        <Route path="/about" element={<div data-testid="about">About page</div>} />
      </Routes>
    </div>
  );
}

describe("Ask conversation preservation across routes", () => {
  it("keeps Ask messages in parent state while navigating away and back", async () => {
    const user = userEvent.setup();
    render(
      <MemoryRouter initialEntries={["/ask"]}>
        <ShellWithAskState />
      </MemoryRouter>,
    );

    expect(screen.getByTestId("ask")).toHaveTextContent("Where is the registrar?");
    await user.click(screen.getByRole("link", { name: "About" }));
    expect(screen.getByTestId("about")).toBeInTheDocument();
    await user.click(screen.getByRole("link", { name: "Ask" }));
    expect(screen.getByTestId("ask")).toHaveTextContent("Where is the registrar?");
  });
});
