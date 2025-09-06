-- SQL for table: community_tagging
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "community_tagging" (
    "id" SERIAL PRIMARY KEY,
    "community_id" INTEGER NOT NULL,
    "category_id" INTEGER NULL,
    "procedure_id" INTEGER NULL,
    "confidence_score" DOUBLE PRECISION NULL,
    "user_confirmed" BOOLEAN NULL,
    "created_at" TIMESTAMP NULL
);

