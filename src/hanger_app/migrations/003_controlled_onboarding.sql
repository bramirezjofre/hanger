CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    contact_address TEXT NOT NULL,
    contact_kind TEXT NOT NULL,
    answers_json TEXT NOT NULL DEFAULT '{}',
    reviewer_notes TEXT,
    reviewer_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    status TEXT NOT NULL DEFAULT 'submitted'
        CHECK (status IN (
            'submitted',
            'screening',
            'interview',
            'accepted',
            'rejected',
            'invited'
        )),
    decided_at INTEGER,
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
    UNIQUE(contact_address, contact_kind)
);

CREATE INDEX IF NOT EXISTS idx_applications_status
ON applications(status, created_at);

ALTER TABLE invitations ADD COLUMN application_id INTEGER
    REFERENCES applications(id) ON DELETE SET NULL;

ALTER TABLE invitations ADD COLUMN token_hash TEXT;

ALTER TABLE invitations ADD COLUMN expires_at INTEGER;

ALTER TABLE invitations ADD COLUMN used_at INTEGER;

CREATE UNIQUE INDEX IF NOT EXISTS idx_invitations_token_hash
ON invitations(token_hash)
WHERE token_hash IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_invitations_application
ON invitations(application_id);
