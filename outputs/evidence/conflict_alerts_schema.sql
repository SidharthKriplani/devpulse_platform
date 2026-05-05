-- EA-11 conflict_alerts_schema
CREATE TABLE conflict_alerts (
  id TEXT PRIMARY KEY,
  query_id TEXT NOT NULL,
  conflict_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  chunk_ids TEXT,
  description TEXT NOT NULL,
  auto_resolved BOOLEAN DEFAULT FALSE,
  resolved_by TEXT,
  resolved_at TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
