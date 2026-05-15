import { Pool, type QueryResultRow } from "pg";

const DEFAULT_DATABASE_URL = "postgresql://finahunt:finahunt_local@127.0.0.1:54329/finahunt";

declare global {
  // eslint-disable-next-line no-var
  var __finahuntAdminPool: Pool | undefined;
  // eslint-disable-next-line no-var
  var __finahuntAdminSchemaReady: Promise<void> | undefined;
}

export function normalizeDatabaseUrl(value: string | undefined): string {
  const url = (value || process.env.FINAHUNT_LOCAL_DATABASE_URL || DEFAULT_DATABASE_URL).trim();
  return url.replace(/^postgresql\+psycopg:\/\//, "postgresql://");
}

export function getAdminPool(): Pool {
  if (!globalThis.__finahuntAdminPool) {
    globalThis.__finahuntAdminPool = new Pool({
      connectionString: normalizeDatabaseUrl(process.env.DATABASE_URL),
      connectionTimeoutMillis: 5000,
      max: 4,
    });
  }
  return globalThis.__finahuntAdminPool;
}

export async function adminQuery<T extends QueryResultRow = QueryResultRow>(sql: string, values: unknown[] = []): Promise<T[]> {
  await ensureAdminSchema();
  const result = await getAdminPool().query<T>(sql, values);
  return result.rows;
}

export async function ensureAdminSchema(): Promise<void> {
  if (!globalThis.__finahuntAdminSchemaReady) {
    globalThis.__finahuntAdminSchemaReady = createAdminSchema();
  }
  return globalThis.__finahuntAdminSchemaReady;
}

async function createAdminSchema(): Promise<void> {
  const pool = getAdminPool();
  await pool.query(`
    CREATE TABLE IF NOT EXISTS raw_contents (
      document_id VARCHAR(160) PRIMARY KEY,
      run_id VARCHAR(80) DEFAULT '',
      source_id VARCHAR(120) DEFAULT '',
      source_hash VARCHAR(128) DEFAULT '',
      source_name TEXT DEFAULT '',
      title TEXT DEFAULT '',
      url TEXT DEFAULT '',
      published_at VARCHAR(80) DEFAULT '',
      content_text TEXT DEFAULT '',
      http_status INTEGER,
      content_length INTEGER DEFAULT 0,
      license_status VARCHAR(40) DEFAULT 'unknown',
      truth_score INTEGER DEFAULT 0,
      authenticity_status VARCHAR(40) DEFAULT 'unchecked',
      review_status VARCHAR(40) DEFAULT 'unreviewed',
      reviewer_note TEXT DEFAULT '',
      payload JSONB DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ DEFAULT now()
    )
  `);
  const rawColumns = [
    ["source_hash", "VARCHAR(128) DEFAULT ''"],
    ["http_status", "INTEGER"],
    ["content_length", "INTEGER DEFAULT 0"],
    ["license_status", "VARCHAR(40) DEFAULT 'unknown'"],
    ["truth_score", "INTEGER DEFAULT 0"],
    ["authenticity_status", "VARCHAR(40) DEFAULT 'unchecked'"],
    ["review_status", "VARCHAR(40) DEFAULT 'unreviewed'"],
    ["reviewer_note", "TEXT DEFAULT ''"],
  ];
  for (const [name, definition] of rawColumns) {
    await pool.query(`ALTER TABLE raw_contents ADD COLUMN IF NOT EXISTS ${name} ${definition}`);
  }
  await pool.query("CREATE INDEX IF NOT EXISTS ix_raw_contents_source_hash ON raw_contents (source_hash)");
  await pool.query(`
    CREATE TABLE IF NOT EXISTS crawl_runs (
      run_id VARCHAR(80) PRIMARY KEY,
      source_id VARCHAR(120) DEFAULT 'all',
      status VARCHAR(40) DEFAULT 'running',
      started_at TIMESTAMPTZ DEFAULT now(),
      finished_at TIMESTAMPTZ,
      fetched_count INTEGER DEFAULT 0,
      inserted_count INTEGER DEFAULT 0,
      duplicate_count INTEGER DEFAULT 0,
      failed_count INTEGER DEFAULT 0,
      error_message TEXT DEFAULT '',
      payload JSONB DEFAULT '{}'::jsonb
    )
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS admin_crawler_settings (
      id INTEGER PRIMARY KEY,
      enabled BOOLEAN DEFAULT false,
      schedule_time VARCHAR(20) DEFAULT '09:00',
      source_id VARCHAR(120) DEFAULT 'all',
      updated_at TIMESTAMPTZ DEFAULT now()
    )
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS admin_review_logs (
      id SERIAL PRIMARY KEY,
      target_type VARCHAR(40) DEFAULT 'raw_content',
      target_id VARCHAR(160) DEFAULT '',
      action VARCHAR(40) DEFAULT '',
      reviewer_note TEXT DEFAULT '',
      payload JSONB DEFAULT '{}'::jsonb,
      created_at TIMESTAMPTZ DEFAULT now()
    )
  `);
  await pool.query(`
    INSERT INTO admin_crawler_settings (id, enabled, schedule_time, source_id)
    VALUES (1, false, '09:00', 'all')
    ON CONFLICT (id) DO NOTHING
  `);
}

export function toIso(value: unknown): string {
  if (value instanceof Date) {
    return value.toISOString();
  }
  return typeof value === "string" ? value : "";
}
