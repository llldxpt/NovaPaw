import { describe, expect, it } from "vitest";

import { requiresNovaPawModel, supportsAgentAttachments } from "./agentBackend";

describe("requiresNovaPawModel", () => {
  it("requires a configured model for native NovaPaw agents", () => {
    expect(requiresNovaPawModel("novapaw")).toBe(true);
  });

  it("does not inspect NovaPaw models for Codex agents", () => {
    expect(requiresNovaPawModel("codex")).toBe(false);
  });
});

describe("supportsAgentAttachments", () => {
  it("keeps attachments enabled for native agents", () => {
    expect(supportsAgentAttachments("novapaw")).toBe(true);
  });

  it("enables sender drop handling when Codex declares attachments", () => {
    expect(
      supportsAgentAttachments("codex", {
        attachments: true,
      }),
    ).toBe(true);
  });

  it("enables sender drop handling when Qoder declares attachments", () => {
    expect(
      supportsAgentAttachments("qoder", {
        attachments: true,
      }),
    ).toBe(true);
  });

  it("keeps attachments hidden for backends without the capability", () => {
    expect(supportsAgentAttachments("qoder", {})).toBe(false);
  });
});
