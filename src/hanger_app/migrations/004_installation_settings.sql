CREATE TABLE IF NOT EXISTS installation_settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    is_public INTEGER NOT NULL DEFAULT 0 CHECK (is_public IN (0, 1)),
    updated_at INTEGER NOT NULL DEFAULT (unixepoch())
);

INSERT INTO installation_settings (key, value_json, is_public)
VALUES
    ('branding.site_name', '"Hanger"', 1),
    ('branding.support_contact', '""', 1),
    ('branding.logo_url', '""', 1),
    ('eligibility.minimum_age', '18', 0),
    ('eligibility.allowed_contact_kinds', '["email", "mail", "phone", "sms", "tel"]', 0),
    ('eligibility.application_prompt', '""', 0)
ON CONFLICT(key) DO NOTHING;
