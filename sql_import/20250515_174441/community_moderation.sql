-- SQL for table: community_moderation
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "community_moderation" (
    "id" SERIAL PRIMARY KEY,
    "community_id" INTEGER NULL,
    "reply_id" INTEGER NULL,
    "moderator_id" INTEGER NOT NULL,
    "action" TEXT NOT NULL,
    "reason" TEXT NULL,
    "created_at" TIMESTAMP NULL
);

