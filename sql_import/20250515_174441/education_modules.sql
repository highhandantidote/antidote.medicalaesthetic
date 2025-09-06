-- SQL for table: education_modules
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "education_modules" (
    "id" SERIAL PRIMARY KEY,
    "title" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "category_id" INTEGER NULL,
    "procedure_id" INTEGER NULL,
    "level" INTEGER NULL,
    "points" INTEGER NULL,
    "estimated_minutes" INTEGER NULL,
    "created_at" TIMESTAMP NULL,
    "updated_at" TIMESTAMP NULL,
    "is_active" BOOLEAN NULL
);

