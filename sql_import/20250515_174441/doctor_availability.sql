-- SQL for table: doctor_availability
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "doctor_availability" (
    "id" SERIAL PRIMARY KEY,
    "doctor_id" INTEGER NOT NULL,
    "day_of_week" VARCHAR NULL,
    "start_time" TIMESTAMP NULL,
    "end_time" TIMESTAMP NULL,
    "date" TIMESTAMP NULL,
    "slots" JSON NULL,
    "booked_slots" JSON NULL,
    "created_at" TIMESTAMP NULL
);

