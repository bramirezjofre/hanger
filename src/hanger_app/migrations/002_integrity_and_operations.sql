ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user';

ALTER TABLE jobs ADD COLUMN lease_id TEXT;
ALTER TABLE jobs ADD COLUMN locked_at INTEGER;

CREATE INDEX IF NOT EXISTS idx_jobs_available
ON jobs(status, available_at, locked_at);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    actor_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    target TEXT,
    created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

ALTER TABLE messages RENAME TO messages_legacy;
ALTER TABLE attachments RENAME TO attachments_legacy;

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    receiver_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    message_id INTEGER NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    stored_name TEXT NOT NULL UNIQUE,
    original_name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size INTEGER NOT NULL
);

INSERT INTO messages (id, sender_id, receiver_id, content, created_at)
SELECT message.id, sender.id, receiver.id, message.content, message.created_at
FROM messages_legacy AS message
JOIN users AS sender ON sender.username = message.sender
JOIN users AS receiver ON receiver.username = message.receiver;

INSERT INTO attachments (id, message_id, stored_name, original_name, mime_type, size)
SELECT attachment.id, attachment.message_id, attachment.stored_name,
       attachment.original_name, attachment.mime_type, attachment.size
FROM attachments_legacy AS attachment
JOIN messages ON messages.id = attachment.message_id;

DROP TABLE attachments_legacy;
DROP TABLE messages_legacy;

ALTER TABLE posts RENAME TO posts_legacy;
ALTER TABLE comments RENAME TO comments_legacy;
ALTER TABLE post_likes RENAME TO post_likes_legacy;

CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    content TEXT NOT NULL,
    created_at INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE post_likes (
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
    PRIMARY KEY(post_id, user_id)
);

INSERT INTO posts (id, author_id, content, created_at)
SELECT post.id, author.id, post.content, post.created_at
FROM posts_legacy AS post
JOIN users AS author ON author.username = post.author;

INSERT INTO comments (id, post_id, author_id, content, created_at)
SELECT comment.id, comment.post_id, author.id, comment.content, comment.created_at
FROM comments_legacy AS comment
JOIN posts ON posts.id = comment.post_id
JOIN users AS author ON author.username = comment.author;

INSERT INTO post_likes (post_id, user_id, created_at)
SELECT old_like.post_id, user.id, old_like.created_at
FROM post_likes_legacy AS old_like
JOIN posts ON posts.id = old_like.post_id
JOIN users AS user ON user.username = old_like.username;

DROP TABLE post_likes_legacy;
DROP TABLE comments_legacy;
DROP TABLE posts_legacy;
