import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';
import { wrapStreamFn } from './normalize.js';
export default definePluginEntry({ id: 'litellm-compat', name: 'LiteLLM long reset evidence', register(api) {
  for (const id of ['litellm-free-pro', 'litellm-free-perso']) api.registerProvider({ id, label: id, auth: [], wrapStreamFn });
} });
