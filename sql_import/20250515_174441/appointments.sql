-- SQL for table: appointments
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "appointments" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    "doctor_id" INTEGER NOT NULL,
    "procedure_name" TEXT NOT NULL,
    "appointment_date" TIMESTAMP NOT NULL,
    "appointment_time" TEXT NOT NULL,
    "status" TEXT NULL,
    "notes" TEXT NULL,
    "created_at" TIMESTAMP NULL,
    "updated_at" TIMESTAMP NULL
);

