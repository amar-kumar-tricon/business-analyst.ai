/**
 * SettingsPage — Admin LLM configuration per agent.
 *
 * TODO:
 *  - Fetch current per-agent LLM config from GET /settings/llm-config.
 *  - Render a row per agent with provider + model_name + temperature + max_tokens.
 *  - PUT updates to /settings/llm-config/{agent_id}.
 */
import { useEffect, useState } from "react";
import { settingsApi } from "../api/settings";

export default function SettingsPage() {
  const [config, setConfig] = useState<any[]>([]);

  useEffect(() => {
    settingsApi.getLlmConfig().then(setConfig);
  }, []);

  return (
    <section className="card">
      <h2>Settings — Per-Agent LLM Configuration</h2>
      <pre>{JSON.stringify(config, null, 2)}</pre>
    </section>
  );
}
