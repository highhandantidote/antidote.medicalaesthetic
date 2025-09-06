-- SQL for table: face_scan_recommendations
-- Generated: 2025-05-15 17:44:41
-- Row count: 5

CREATE TABLE IF NOT EXISTS "face_scan_recommendations" (
    "id" SERIAL PRIMARY KEY,
    "analysis_id" INTEGER NOT NULL,
    "procedure_id" INTEGER NULL,
    "relevance_score" DOUBLE PRECISION NOT NULL,
    "area_of_concern" TEXT NULL,
    "recommendation_reason" TEXT NULL,
    "recommendation_type" TEXT NULL,
    "created_at" TIMESTAMP NULL
);

INSERT INTO "face_scan_recommendations" ("id", "analysis_id", "procedure_id", "relevance_score", "area_of_concern", "recommendation_reason", "recommendation_type", "created_at") VALUES
(1, 1, NULL, 0.7, 'Chin Augmentation', 'Based on the limited information provided, the most prominent area for potential cosmetic improvement is the chin projection.  Both surgical chin augmentation and non-surgical dermal filler injections are viable options, depending on the patient’s preferences and risk tolerance.  Addressing any under-eye concerns could involve topical skincare or makeup application.', 'procedure', '2025-05-14 13:34:58.021997'),
(2, 1, NULL, 0.6, 'Dermal Fillers', 'Based on the limited information provided, the most prominent area for potential cosmetic improvement is the chin projection.  Both surgical chin augmentation and non-surgical dermal filler injections are viable options, depending on the patient’s preferences and risk tolerance.  Addressing any under-eye concerns could involve topical skincare or makeup application.', 'treatment', '2025-05-14 13:34:58.022483'),
(3, 1, NULL, 0.6, 'Chemical Peel', '* **Treatment Options:**
    * **Non-surgical (for potential under-eye darkness):**  Topical treatments (e.g., retinoids, vitamin C serums), chemical peels, microdermabrasion, and/or professional strength concealer for improved coverage.  If darkness is related to underlying dark circles, fillers can be considered but are generally only used in more mature patients.', 'treatment', '2025-05-14 13:34:58.022618'),
(4, 1, NULL, 0.6, 'Microdermabrasion', '* **Treatment Options:**
    * **Non-surgical (for potential under-eye darkness):**  Topical treatments (e.g., retinoids, vitamin C serums), chemical peels, microdermabrasion, and/or professional strength concealer for improved coverage.  If darkness is related to underlying dark circles, fillers can be considered but are generally only used in more mature patients.', 'treatment', '2025-05-14 13:34:58.022717'),
(5, 1, NULL, 0.6, 'Vitamin C Treatment', '* **Treatment Options:**
    * **Non-surgical (for potential under-eye darkness):**  Topical treatments (e.g., retinoids, vitamin C serums), chemical peels, microdermabrasion, and/or professional strength concealer for improved coverage.  If darkness is related to underlying dark circles, fillers can be considered but are generally only used in more mature patients.', 'treatment', '2025-05-14 13:34:58.022823');

SELECT setval(pg_get_serial_sequence('face_scan_recommendations', 'id'), 5, true);

