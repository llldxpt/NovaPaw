import type { AgentBackend } from "../api/types/agents";
import type { HarnessCapabilities } from "../api/modules/harness";

export function requiresNovaPawModel(backend: AgentBackend): boolean {
  return backend === "novapaw";
}

export function supportsAgentAttachments(
  backend: AgentBackend,
  capabilities?: Partial<HarnessCapabilities>,
): boolean {
  return requiresNovaPawModel(backend) || Boolean(capabilities?.attachments);
}
