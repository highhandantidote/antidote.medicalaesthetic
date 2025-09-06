-- SQL for table: banner_slides
-- Generated: 2025-05-15 17:44:41
-- Row count: 4

CREATE TABLE IF NOT EXISTS "banner_slides" (
    "id" SERIAL PRIMARY KEY,
    "banner_id" INTEGER NOT NULL,
    "title" VARCHAR NOT NULL,
    "subtitle" TEXT NULL,
    "image_url" VARCHAR NOT NULL,
    "redirect_url" VARCHAR NOT NULL,
    "display_order" INTEGER NULL,
    "is_active" BOOLEAN NULL,
    "created_at" TIMESTAMP NULL,
    "updated_at" TIMESTAMP NULL,
    "click_count" INTEGER NULL,
    "impression_count" INTEGER NULL
);

INSERT INTO "banner_slides" ("id", "banner_id", "title", "subtitle", "image_url", "redirect_url", "display_order", "is_active", "created_at", "updated_at", "click_count", "impression_count") VALUES
(2, 2, 'Test Slide for between_procedures_specialists', 'This is a test slide for banner position between_procedures_specialists', 'https://placehold.co/600x200/9053b8/ffffff?text=Banner+2', '#', 1, True, '2025-05-14 09:56:07.380015', '2025-05-15 17:41:09.971279', NULL, 131),
(4, 4, 'Test Slide for before_footer', 'This is a test slide for banner position before_footer', 'https://placehold.co/600x200/9053b8/ffffff?text=Banner+4', '#', 1, True, '2025-05-14 09:56:09.598905', '2025-05-15 17:41:12.389276', NULL, 131),
(3, 3, 'Test Slide for between_categories_community', 'This is a test slide for banner position between_categories_community', 'https://placehold.co/600x200/9053b8/ffffff?text=Banner+3', '#', 1, True, '2025-05-14 09:56:08.492415', '2025-05-15 17:41:14.771353', NULL, 132),
(1, 1, 'Test Slide for between_hero_stats', 'This is a test slide for banner position between_hero_stats', 'https://placehold.co/600x200/9053b8/ffffff?text=Banner+1', '#', 1, True, '2025-05-14 09:56:06.256343', '2025-05-15 17:41:17.146238', NULL, 130);

SELECT setval(pg_get_serial_sequence('banner_slides', 'id'), 4, true);

