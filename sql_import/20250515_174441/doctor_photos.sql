-- SQL for table: doctor_photos
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "doctor_photos" (
    "id" SERIAL PRIMARY KEY,
    "doctor_id" INTEGER NOT NULL,
    "photo_url" TEXT NULL,
    "description" TEXT NULL,
    "created_at" TIMESTAMP NULL
);

