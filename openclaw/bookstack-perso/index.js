import { buildTools } from "./lib/tools.js";
import { buildCommentTool } from "./lib/tool-comments.js";

export default {
  id: "bookstack-perso",
  name: "BookStack Perso",
  description: "Gestion documentaire BookStack pour l'agent Perso (activités, rubriques, pages, pièces jointes, import/OCR).",
  configSchema: {
    type: "object",
    additionalProperties: false,
    properties: {
      baseUrl: { type: "string" },
      apiToken: { type: "object" },
    },
  },
  register(api) {
    const stateDir = api.runtime?.stateDir ?? process.env.OPENCLAW_STATE_DIR ?? `${process.env.HOME}/.openclaw`;
    const tools = [...buildTools(api), buildCommentTool(api, stateDir)];
    for (const tool of tools) {
      api.registerTool((ctx) => ({
        name: tool.name,
        label: tool.label,
        description: tool.description,
        parameters: tool.parameters,
        async execute(_toolCallId, params) {
          return tool.run(params ?? {}, ctx);
        },
      }), { names: [tool.name] });
    }
  },
};
