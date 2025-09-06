-- SQL for table: body_parts
-- Generated: 2025-05-15 17:44:41
-- Row count: 25

CREATE TABLE IF NOT EXISTS "body_parts" (
    "id" SERIAL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "description" TEXT NULL,
    "icon_url" TEXT NULL,
    "created_at" TIMESTAMP NULL
);

INSERT INTO "body_parts" ("id", "name", "description", "icon_url", "created_at") VALUES
(23, 'Breasts', 'Procedures related to the breasts', '/static/images/body_parts/breasts.svg', '2025-05-14 07:09:37.475735'),
(24, 'Stomach', 'Procedures related to the stomach', '/static/images/body_parts/stomach.svg', '2025-05-14 07:09:38.375837'),
(25, 'Butt', 'Procedures related to the butt', '/static/images/body_parts/butt.svg', '2025-05-14 07:09:39.236156'),
(26, 'Nose', 'Procedures related to the nose', '/static/images/body_parts/nose.svg', '2025-05-14 07:09:40.095702'),
(27, 'Eyes', 'Procedures related to the eyes', '/static/images/body_parts/eyes.svg', '2025-05-14 07:09:42.439637'),
(28, 'Body', 'Procedures related to the body', '/static/images/body_parts/body.svg', '2025-05-14 07:09:43.296687'),
(30, 'Face', 'Procedures related to the face', '/static/images/body_parts/face.svg', '2025-05-14 09:07:39.082374'),
(31, 'Hair', 'Procedures related to the hair', '/static/images/body_parts/hair.svg', '2025-05-14 09:07:42.345042'),
(32, 'Female Genitals', 'Procedures related to the female genitals', '/static/images/body_parts/female_genitals.svg', '2025-05-14 09:07:43.216883'),
(39, 'Lips', 'Procedures for the lips', '/static/images/body_parts/lips.svg', '2025-05-14 09:18:42.736665'),
(40, 'Teeth & Gums', 'Procedures for the teeth & gums', '/static/images/body_parts/teeth_&_gums.svg', '2025-05-14 09:19:06.150184'),
(41, 'Chin', 'Procedures for the chin', '/static/images/body_parts/chin.svg', '2025-05-14 09:19:08.877832'),
(43, 'Skin', 'Procedures for the skin', '/static/images/body_parts/skin.svg', '2025-05-14 09:20:32.163902'),
(44, 'Ears', 'Procedures for the ears', '/static/images/body_parts/ears.svg', '2025-05-14 09:22:33.236742'),
(45, 'Legs', 'Procedures for the legs', '/static/images/body_parts/legs.svg', '2025-05-14 09:23:17.501053'),
(46, 'Eyebrows', 'Procedures for the eyebrows', '/static/images/body_parts/eyebrows.svg', '2025-05-14 09:29:32.044652'),
(47, 'Chest', 'Procedures for the chest', '/static/images/body_parts/chest.svg', '2025-05-14 09:29:36.164966'),
(48, 'Jawline', 'Procedures for the jawline', '/static/images/body_parts/jawline.svg', '2025-05-14 09:30:00.099763'),
(49, 'Male Genitals', 'Procedures for the male genitals', '/static/images/body_parts/male_genitals.svg', '2025-05-14 09:36:50.535826'),
(50, 'Back', 'Procedures for the back', '/static/images/body_parts/back.svg', '2025-05-14 09:45:46.941803'),
(51, 'Hands', 'Procedures for the hands', '/static/images/body_parts/hands.svg', '2025-05-14 10:07:22.991867'),
(52, 'Neck', 'Procedures for the neck', '/static/images/body_parts/neck.svg', '2025-05-14 10:08:07.319522'),
(53, 'Hips', 'Procedures for the hips', '/static/images/body_parts/hips.svg', '2025-05-14 10:10:59.722469'),
(54, 'Feet', 'Procedures for the feet', '/static/images/body_parts/feet.svg', '2025-05-14 10:25:06.537865'),
(55, 'Arms', NULL, NULL, '2025-05-14 11:49:16.450173');

SELECT setval(pg_get_serial_sequence('body_parts', 'id'), 55, true);

