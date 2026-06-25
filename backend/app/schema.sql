-- Per-number whitelist / routing state
CREATE TABLE IF NOT EXISTS numbers (
  phone           TEXT PRIMARY KEY,              -- E.164 digits only, e.g. 6281234567890
  mode            TEXT NOT NULL DEFAULT 'human'  -- 'agent' = agent auto-replies, 'human' = taken over, agent silent
                  CHECK (mode IN ('agent','human')),
  display_name    TEXT,
  created_at      INTEGER NOT NULL DEFAULT (unixepoch()),
  updated_at      INTEGER NOT NULL DEFAULT (unixepoch()),
  last_in_at      INTEGER,                       -- ts of last inbound message (for sorting)
  last_msg_preview TEXT                          -- last inbound body (truncated)
);
CREATE INDEX IF NOT EXISTS idx_numbers_mode ON numbers(mode);

-- Conversation / message log (inbound + outbound)
CREATE TABLE IF NOT EXISTS messages (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  waha_msg_id   TEXT UNIQUE,                     -- message id for idempotent dedup
  phone         TEXT NOT NULL,
  chat_id       TEXT NOT NULL,
  direction     TEXT NOT NULL CHECK (direction IN ('in','out')),
  source        TEXT NOT NULL CHECK (source IN ('agent','staff','system')),
  body          TEXT,
  has_media     INTEGER NOT NULL DEFAULT 0,
  media_url     TEXT,
  raw_event     TEXT,
  created_at    INTEGER NOT NULL DEFAULT (unixepoch())
);
CREATE INDEX IF NOT EXISTS idx_messages_phone_time ON messages(phone, created_at DESC);

-- Audit log for ALL webhook events (message & non-message)
CREATE TABLE IF NOT EXISTS webhook_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id    TEXT,
  event_type  TEXT NOT NULL,
  session     TEXT,
  received_at INTEGER NOT NULL DEFAULT (unixepoch()),
  payload     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_events_type_time ON webhook_events(event_type, received_at DESC);
