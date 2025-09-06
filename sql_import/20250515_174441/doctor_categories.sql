-- SQL for table: doctor_categories
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "doctor_categories" (
    "id" SERIAL PRIMARY KEY,
    "doctor_id" INTEGER NOT NULL,
    "category_id" INTEGER NOT NULL,
    "created_at" TIMESTAMP NULL,
    "is_verified" BOOLEAN NULL
);

