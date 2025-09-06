-- SQL for table: banners
-- Generated: 2025-05-15 17:44:41
-- Row count: 4

CREATE TABLE IF NOT EXISTS "banners" (
    "id" SERIAL PRIMARY KEY,
    "name" VARCHAR NOT NULL,
    "position" VARCHAR NOT NULL,
    "is_active" BOOLEAN NULL,
    "created_at" TIMESTAMP NULL,
    "updated_at" TIMESTAMP NULL
);

INSERT INTO "banners" ("id", "name", "position", "is_active", "created_at", "updated_at") VALUES
(1, 'Banner for between_hero_stats', 'between_hero_stats', True, '2025-05-14 09:56:06.024652', '2025-05-14 09:56:06.024656'),
(2, 'Banner for between_procedures_specialists', 'between_procedures_specialists', True, '2025-05-14 09:56:07.157250', '2025-05-14 09:56:07.157253'),
(3, 'Banner for between_categories_community', 'between_categories_community', True, '2025-05-14 09:56:08.270684', '2025-05-14 09:56:08.270687'),
(4, 'Banner for before_footer', 'before_footer', True, '2025-05-14 09:56:09.378185', '2025-05-14 09:56:09.378188');

SELECT setval(pg_get_serial_sequence('banners', 'id'), 4, true);

