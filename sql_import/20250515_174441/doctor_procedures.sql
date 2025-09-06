-- SQL for table: doctor_procedures
-- Generated: 2025-05-15 17:44:41
-- Row count: 15

CREATE TABLE IF NOT EXISTS "doctor_procedures" (
    "id" SERIAL PRIMARY KEY,
    "doctor_id" INTEGER NOT NULL,
    "procedure_id" INTEGER NOT NULL,
    "created_at" TIMESTAMP NULL
);

INSERT INTO "doctor_procedures" ("id", "doctor_id", "procedure_id", "created_at") VALUES
(102, 13, 1, NULL),
(103, 13, 2, NULL),
(104, 13, 3, NULL),
(105, 13, 4, NULL),
(106, 13, 5, NULL),
(107, 14, 1, NULL),
(108, 14, 2, NULL),
(109, 14, 3, NULL),
(110, 14, 4, NULL),
(111, 14, 5, NULL),
(116, 16, 1, NULL),
(117, 16, 2, NULL),
(118, 16, 3, NULL),
(119, 16, 4, NULL),
(120, 16, 5, NULL);

SELECT setval(pg_get_serial_sequence('doctor_procedures', 'id'), 120, true);

