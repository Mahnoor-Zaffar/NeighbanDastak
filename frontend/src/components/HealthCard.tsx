import type { HealthResponse } from "../app/api";

interface HealthCardProps {
  health: HealthResponse | null;
  error: string | null;
}

export function HealthCard({ health, error }: HealthCardProps) {
  return (
    <section className="status-card">
      <h2>Environment status</h2>
      {!health && !error ? <p>Checking backend health...</p> : null}
      {error ? <p className="status-error">{error}</p> : null}
      {health ? (
        <dl className="status-grid">
          <div>
            <dt>Service</dt>
            <dd>{health.service}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{health.status}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{health.environment}</dd>
          </div>
          <div>
            <dt>Version</dt>
            <dd>{health.version}</dd>
          </div>
          <div>
            <dt>Database</dt>
            <dd>{health.database}</dd>
          </div>
        </dl>
      ) : null}
    </section>
  );
}
