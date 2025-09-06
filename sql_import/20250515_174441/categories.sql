-- SQL for table: categories
-- Generated: 2025-05-15 17:44:41
-- Row count: 44

CREATE TABLE IF NOT EXISTS "categories" (
    "id" SERIAL PRIMARY KEY,
    "name" TEXT NOT NULL,
    "body_part_id" INTEGER NOT NULL,
    "description" TEXT NULL,
    "popularity_score" INTEGER NULL,
    "created_at" TIMESTAMP NULL
);

INSERT INTO "categories" ("id", "name", "body_part_id", "description", "popularity_score", "created_at") VALUES
(1, 'Breast Surgery', 23, 'Breast Surgery procedures for Breasts', 0, '2025-05-14 07:09:37.720484'),
(2, 'Abdominoplasty', 24, 'Abdominoplasty procedures for Stomach', 0, '2025-05-14 07:09:38.590454'),
(3, 'Hip & Butt Enhancement', 25, 'Hip & Butt Enhancement procedures for Butt', 0, '2025-05-14 07:09:39.455262'),
(4, 'Rhinoplasty And Nose Shaping', 26, 'Rhinoplasty And Nose Shaping procedures for Nose', 0, '2025-05-14 07:09:40.307164'),
(5, 'Post-Pregnancy Procedures', 24, 'Post-Pregnancy Procedures procedures for Stomach', 0, '2025-05-14 07:09:40.951665'),
(6, 'Eyelid Enhancement', 27, 'Eyelid Enhancement procedures for Eyes', 0, '2025-05-14 07:09:42.659790'),
(7, 'Body Contouring', 28, 'Body Contouring procedures for Body', 0, '2025-05-14 07:09:43.510375'),
(10, 'Face And Neck Lifts', 30, 'Face And Neck Lifts procedures for Face', 0, '2025-05-14 09:07:39.306192'),
(11, 'Fillers And Other Injectables', 30, 'Fillers And Other Injectables procedures for Face', 0, '2025-05-14 09:07:39.960595'),
(12, 'Hair Restoration', 31, 'Hair Restoration procedures for Hair', 0, '2025-05-14 09:07:42.562878'),
(13, 'Female Genital Aesthetic Surgery', 32, 'Female Genital Aesthetic Surgery procedures for Female Genitals', 0, '2025-05-14 09:07:43.436834'),
(19, 'Breast Reconstruction', 23, 'Breast Reconstruction procedures for Breasts', 0, '2025-05-14 09:18:10.681792'),
(20, 'Weight Loss Treatments', 24, 'Weight Loss Treatments procedures for Stomach', 0, '2025-05-14 09:18:13.895273'),
(21, 'Lip Enhancement', 39, 'Lip Enhancement procedures for Lips', 0, '2025-05-14 09:18:43.637486'),
(22, 'Cosmetic Dentistry', 40, 'Cosmetic Dentistry procedures for Teeth & Gums', 0, '2025-05-14 09:19:07.059129'),
(23, 'Cheek, Chin And Jawline Enhancement', 41, 'Cheek, Chin And Jawline Enhancement procedures for Chin', 0, '2025-05-14 09:19:09.782586'),
(24, 'Tattoo Removal', 43, 'Tattoo Removal procedures for Skin', 0, '2025-05-14 09:20:33.022035'),
(26, 'Skin Tightening', 43, 'Skin Tightening procedures for Skin', 0, '2025-05-14 09:21:06.233752'),
(27, 'Skin Rejuvenation And Resurfacing', 43, 'Skin Rejuvenation And Resurfacing procedures for Skin', 0, '2025-05-14 09:21:08.508296'),
(28, 'Ear Surgery', 44, 'Ear Surgery procedures for Ears', 0, '2025-05-14 09:22:34.391570'),
(29, 'Hair Removal', 28, 'Hair Removal procedures for Body', 0, '2025-05-14 09:22:38.417992'),
(30, 'Acne Treatments', 43, 'Acne Treatments procedures for Skin', 0, '2025-05-14 09:23:35.897178'),
(31, 'Scar Treatments', 43, 'Scar Treatments procedures for Skin', 0, '2025-05-14 09:24:59.779379'),
(32, 'Hyperhidrosis Treatments', 28, 'Hyperhidrosis Treatments procedures for Body', 0, '2025-05-14 09:25:04.945256'),
(33, 'Reconstructive Surgeries', 28, 'Reconstructive Surgeries procedures for Body', 0, '2025-05-14 09:26:02.068467'),
(34, 'Eyebrow And Lash Enhancement', 46, 'Eyebrow And Lash Enhancement procedures for Eyebrows', 0, '2025-05-14 09:29:33.141178'),
(35, 'Gender Confirmation Surgery', 47, 'Gender Confirmation Surgery procedures for Chest', 0, '2025-05-14 09:29:37.231523'),
(36, 'Vision Correction', 27, 'Vision Correction procedures for Eyes', 0, '2025-05-14 09:30:37.880711'),
(37, 'Facial Reconstructive Surgery', 30, 'Facial Reconstructive Surgery procedures for Face', 0, '2025-05-14 09:32:38.427965'),
(38, 'Vein Treatments', 28, 'Vein Treatments procedures for Body', 0, '2025-05-14 09:33:10.251661'),
(39, 'Medical Dermatology', 28, 'Medical Dermatology procedures for Body', 0, '2025-05-14 09:33:31.389121'),
(40, 'Vaginal Rejuvenation', 32, 'Vaginal Rejuvenation procedures for Female Genitals', 0, '2025-05-14 09:35:42.288611'),
(41, 'Skin Care Products', 43, 'Skin Care Products procedures for Skin', 0, '2025-05-14 09:36:03.431840'),
(42, 'Male Body Enhancement', 49, 'Male Body Enhancement procedures for Male Genitals', 0, '2025-05-14 09:36:51.606706'),
(43, 'Sexual Wellness', 32, 'Sexual Wellness procedures for Female Genitals', 0, '2025-05-14 09:45:22.954556'),
(44, 'Oral And Maxillofacial Surgeries', 26, 'Oral And Maxillofacial Surgeries procedures for Nose', 0, '2025-05-14 10:01:22.044343'),
(45, 'Urinary Incontinence Treatments', 32, 'Urinary Incontinence Treatments procedures for Female Genitals', 0, '2025-05-14 10:03:49.404124'),
(46, 'General Dentistry', 40, 'General Dentistry procedures for Teeth & Gums', 0, '2025-05-14 10:07:28.124689'),
(47, 'Podiatry', 54, 'Podiatry procedures for Feet', 0, '2025-05-14 10:25:07.657765'),
(51, 'Facial Treatments', 30, NULL, NULL, '2025-05-14 12:22:31.406408'),
(52, 'Skin Treatments', 28, NULL, NULL, '2025-05-14 12:51:09.501437'),
(59, 'Sexual Wellness (Male Genitals)', 49, NULL, NULL, NULL),
(60, 'Weight Loss Treatments (Body)', 28, NULL, NULL, NULL),
(61, 'Gender Confirmation Surgery (Male Genitals)', 49, NULL, NULL, NULL);

SELECT setval(pg_get_serial_sequence('categories', 'id'), 61, true);

