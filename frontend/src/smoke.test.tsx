import { act } from "react";
import { createRoot } from "react-dom/client";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "./App";

let container: HTMLDivElement | null = null;

afterEach(() => {
  if (container) {
    container.remove();
    container = null;
  }
});

describe("frontend smoke", () => {
  it("renders the foundation shell", () => {
    container = document.createElement("div");
    document.body.appendChild(container);

    act(() => {
      createRoot(container as HTMLDivElement).render(<App />);
    });

    expect(container.textContent).toContain("DLE-SaaS");
    expect(container.textContent).toContain("Platform foundation ready");
  });
});
