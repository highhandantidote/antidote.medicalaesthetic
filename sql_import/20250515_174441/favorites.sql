-- SQL for table: favorites
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "favorites" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    "procedure_id" INTEGER NULL,
    "doctor_id" INTEGER NULL,
    "created_at" TIMESTAMP NULL
);

