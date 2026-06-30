ALTER TABLE applications ADD COLUMN interview_contact_method TEXT;

ALTER TABLE applications ADD COLUMN interview_preferred_times TEXT;

ALTER TABLE applications ADD COLUMN interviewer_id INTEGER
    REFERENCES users(id) ON DELETE SET NULL;

ALTER TABLE applications ADD COLUMN interview_status TEXT NOT NULL
    DEFAULT 'not_scheduled'
    CHECK (interview_status IN (
        'not_scheduled',
        'scheduled',
        'completed',
        'cancelled'
    ));

CREATE INDEX IF NOT EXISTS idx_applications_interview_status
ON applications(interview_status, updated_at);

CREATE INDEX IF NOT EXISTS idx_applications_interviewer
ON applications(interviewer_id);

CREATE TABLE IF NOT EXISTS interview_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL
        REFERENCES applications(id) ON DELETE CASCADE,
    author_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    category TEXT NOT NULL CHECK (category IN (
        'motivation',
        'fit',
        'risks',
        'follow_up'
    )),
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE INDEX IF NOT EXISTS idx_interview_notes_application
ON interview_notes(application_id, created_at);

CREATE INDEX IF NOT EXISTS idx_interview_notes_category
ON interview_notes(category);
