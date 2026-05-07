/**
 * SettingsPage — placeholder.
 *
 * Per-agent LLM configuration is not yet exposed by the backend.
 */
export default function SettingsPage() {
  return (
    <section className="rounded-lg border border-border bg-card p-6">
      <h2 className="text-xl font-semibold">Settings</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        LLM provider and model are configured via the server <code>.env</code> file
        (<code>OPENAI_API_KEY</code>, <code>DEFAULT_MODEL_NAME</code>). A UI for
        per-agent overrides will land in a later phase.
      </p>
    </section>
  );
}
