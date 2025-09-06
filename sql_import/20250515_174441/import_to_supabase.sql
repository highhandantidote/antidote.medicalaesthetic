-- Supabase Import Script
-- Generated: 2025-05-15 17:44:41

-- Run this script in the Supabase SQL Editor to import all tables
-- Note: This script includes all SQL in the proper order

\echo 'Importing body_parts...'
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


\echo 'Importing categories...'
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


\echo 'Importing doctors...'
-- SQL for table: doctors
-- Generated: 2025-05-15 17:44:41
-- Row count: 117

CREATE TABLE IF NOT EXISTS "doctors" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    "name" TEXT NOT NULL,
    "specialty" TEXT NOT NULL,
    "experience" INTEGER NOT NULL,
    "city" TEXT NOT NULL,
    "state" TEXT NULL,
    "hospital" TEXT NULL,
    "consultation_fee" INTEGER NULL,
    "is_verified" BOOLEAN NULL,
    "rating" DOUBLE PRECISION NULL,
    "review_count" INTEGER NULL,
    "created_at" TIMESTAMP NULL,
    "bio" TEXT NULL,
    "certifications" JSON NULL,
    "video_url" TEXT NULL,
    "success_stories" INTEGER NULL,
    "education" JSON NULL,
    "medical_license_number" TEXT NULL,
    "qualification" TEXT NULL,
    "practice_location" TEXT NULL,
    "verification_status" TEXT NULL,
    "verification_date" TIMESTAMP NULL,
    "verification_notes" TEXT NULL,
    "credentials_url" TEXT NULL,
    "aadhaar_number" TEXT NULL,
    "profile_image" TEXT NULL,
    "image_url" TEXT NULL
);

INSERT INTO "doctors" ("id", "user_id", "name", "specialty", "experience", "city", "state", "hospital", "consultation_fee", "is_verified", "rating", "review_count", "created_at", "bio", "certifications", "video_url", "success_stories", "education", "medical_license_number", "qualification", "practice_location", "verification_status", "verification_date", "verification_notes", "credentials_url", "aadhaar_number", "profile_image", "image_url") VALUES
(23, 28, 'Dr. Priya Bansal', 'Plastic Surgeon', 11, 'New Delhi', 'Delhi', 'N-88, Block N', NULL, True, 4.913492346709875, 23, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MBBS'', ''MS'', ''DNB'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/f/1/d/11539470-4938090.png', 'https://fi.realself.com/300/f/1/d/11539470-4938090.png'),
(24, 29, 'Dr. Suneet Soni', 'Plastic Surgeon', 19, 'Jaipur', 'Rajasthan', 'D145, Opp. Inox', NULL, True, 3.872676308991102, 27, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MS'', ''MCh'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/f/4/1/1523876-3181936.jpg', 'https://fi.realself.com/300/f/4/1/1523876-3181936.jpg'),
(14, 15, 'Dr. R. K. Mishra', 'Plastic Surgeon', 25, 'Lucknow', 'Uttar Pradesh', '29 Shah Mina Rd.', 1000, True, 4.0, 0, NULL, 'Dr. Mishra is a Plastic Surgeon with 25 years of experience.', NULL, NULL, NULL, '{''degrees'': [''MCh'', ''DNB'']}', NULL, NULL, NULL, 'approved', '2025-05-14 08:08:46.569891', NULL, NULL, NULL, 'https://fi.realself.com/300/4/4/a/1134377-4683117.jpeg', 'https://fi.realself.com/300/4/4/a/1134377-4683117.jpeg'),
(96, 104, 'Dr. Mukesh Sharma', 'Plastic Surgeon', 14, 'Ghaziabad', 'Uttar Pradesh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:15.483274', '', NULL, NULL, NULL, '[''MBBS, MS, MCh, DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/4/c/1/2396275-2695574.JPG', 'https://fi.realself.com/300/4/c/1/2396275-2695574.JPG'),
(25, 31, 'Dr. Anup Dhir', 'Plastic Surgeon', 40, 'New Delhi', 'Delhi', '101 Ansal Tower', NULL, True, 4.279663445730826, 13, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MD'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/a/3/4/58207-6102265.png', 'https://fi.realself.com/300/a/3/4/58207-6102265.png'),
(18, 22, 'Dr. Karthik Ram', 'Plastic Surgeon', 26, 'Chennai', 'Tamil Nadu', 'Mc Nichols Road, 4th Lane, Chetpet', NULL, True, 3.763899872988762, 34, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MRCS'', ''DNB'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/0/a/5/1137827-4826472.jpeg', 'https://fi.realself.com/300/0/a/5/1137827-4826472.jpeg'),
(19, 23, 'Dr. Rajat Gupta', 'Plastic Surgeon', 14, 'Delhi', 'Delhi', 'Skinnovation Clinics', NULL, True, 3.8649852344958906, 30, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MD'', ''MS'', ''DNB'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/3/c/2/4530197-2962708-T1490299900.813.JPG', 'https://fi.realself.com/300/3/c/2/4530197-2962708-T1490299900.813.JPG'),
(26, 32, 'Dr. Sunil Arora', 'Plastic Surgeon', 16, 'Jaipur', 'Rajasthan', 'K-58, Behind Dana Pani Restaurant Kishan Nagar, Shyam Nagar', NULL, True, 4.826704233339218, 36, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MS'', ''MCh'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/c/5/0/5599201-5420639.png', 'https://fi.realself.com/300/c/5/0/5599201-5420639.png'),
(20, 24, 'Dr. Ajaya Kashyap', 'Plastic Surgeon', 39, 'New Delhi', 'Delhi', '4 Aradhana Enclave', NULL, True, 4.116154833138419, 11, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MD'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/8/5/6/731445-5068353.png', 'https://fi.realself.com/300/8/5/6/731445-5068353.png'),
(21, 26, 'Dr. Venkat Thota', 'Plastic Surgeon', 27, 'Hyderabad', 'Telangana', '4th Floor, Sri Tirumala Subhash Arcade, Gachibowli Miyapur Road', NULL, True, 3.7713079954840936, 10, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MCh'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/4/1/9/6086940-3328898.jpg', 'https://fi.realself.com/300/4/1/9/6086940-3328898.jpg'),
(22, 27, 'Dr. Milan Doshi', 'Plastic Surgeon', 23, 'Mumbai', 'Maharashtra', '201, Shri Krishna Complex, Opp to Laxmi industrial estate', NULL, True, 4.112148838052395, 26, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MS'', ''MCh'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/0/b/f/556833-4841510.jpeg', 'https://fi.realself.com/300/0/b/f/556833-4841510.jpeg'),
(16, 17, 'Dr. Ashutosh Shah', 'Plastic Surgeon', 20, 'Surat', 'Gujarat', 'Trinity Business Park', 1000, True, 4.0, 0, NULL, 'Dr. Shah is a Plastic Surgeon with 20 years of experience.', NULL, NULL, NULL, '[{''degree'': ''MB''}, {''degree'': ''MS''}, {''degree'': ''MCh''}]', NULL, NULL, NULL, 'approved', '2025-05-14 08:10:54.222992', NULL, NULL, NULL, 'https://fi.realself.com/300/3/b/1/4651392-2989300.png', 'https://fi.realself.com/300/3/b/1/4651392-2989300.png'),
(97, 105, 'Dr. Ankit Gupta', 'Plastic Surgeon', 12, 'Delhi', 'Delhi', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:42.073941', '', NULL, NULL, NULL, '[''MCh, MS, MBBS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/b/f/6/7554380-4083499.jpeg', 'https://fi.realself.com/300/b/f/6/7554380-4083499.jpeg'),
(28, 35, 'Dr. Rajesh Vasu Chokka', 'Plastic Surgeon', 25, 'Hyderabad', 'Telangana', 'Sri Parvatha plot-1285/A', 1500, False, 4.327814659811126, 13, '2025-05-14 11:50:57.296981', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MD'', ''institution'': '''', ''year'': ''''}]', NULL, 'MD', 'Sri Parvatha plot-1285/A, third floor Road no 1 & 64', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/d/5/9/241166-8044345.jpeg', 'https://fi.realself.com/300/d/5/9/241166-8044345.jpeg'),
(29, 36, 'Dr. Sandip Jain', 'Plastic Surgeon', 26, 'Mumbai', 'Maharashtra', 'August Kranti Marg', 1500, False, 4.731785226020114, 16, '2025-05-14 11:50:58.688483', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''FRCS'', ''institution'': '''', ''year'': ''''}]', NULL, 'FRCS', 'August Kranti Marg', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/8/7/6/1854957-2931726-T1493067517.937.jpg', 'https://fi.realself.com/300/8/7/6/1854957-2931726-T1493067517.937.jpg'),
(30, 37, 'Dr. Aniketh Venkataram', 'Plastic Surgeon', 15, 'Bangalore', 'Karnataka', 'No 3437', 1500, False, 4.576579866603919, 79, '2025-05-14 11:51:00.075915', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MCh'', ''institution'': '''', ''year'': ''''}]', NULL, 'MBBS, MS, MCh', 'No 3437, 1st G Cross, 7th Main, Subbanna Gardens', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/d/d/7/6844097-4606999.jpeg', 'https://fi.realself.com/300/d/d/7/6844097-4606999.jpeg'),
(98, 106, 'Dr. Swaroop Gambhir', 'Plastic Surgeon', 22, 'New Delhi', 'Delhi', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:43.143220', '', NULL, NULL, NULL, '[''MBBS, MS, DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/4/b/0/6769796-4832940.jpeg', 'https://fi.realself.com/300/4/b/0/6769796-4832940.jpeg'),
(100, 108, 'Dr. Parag Telang', 'Plastic Surgeon', 16, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:45.326789', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/4/1/5/3406531-2779903.JPG', 'https://fi.realself.com/300/4/1/5/3406531-2779903.JPG'),
(101, 109, 'Dr. Narendra Kaushik', 'Plastic Surgeon', 24, 'New Delhi', 'Delhi', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:46.408614', '', NULL, NULL, NULL, '[''MCh, MS, MBBS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/f/0/9/1810253-2928783-T1491946894.952.jpg', 'https://fi.realself.com/300/f/0/9/1810253-2928783-T1491946894.952.jpg'),
(99, 107, 'Dr. Jayanthy Ravindran', 'Plastic Surgeon', 27, 'Chennai', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:44.228944', '', NULL, NULL, NULL, '[''MS, DNB, MRCS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-122197.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-122197.jpg'),
(31, 38, 'Dr. Monisha Kapoor', 'Plastic Surgeon', 14, 'New Delhi', 'Delhi', '18', 1500, False, 4.660238564203412, 87, '2025-05-14 11:51:01.460627', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MCh'', ''institution'': '''', ''year'': ''''}]', NULL, 'MBBS, MS, MCh', '18, Block J', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/c/d/a/3130402-4522267.jpeg', 'https://fi.realself.com/300/c/d/a/3130402-4522267.jpeg'),
(32, 39, 'Dr. Satya Kumar Saraswat', 'Plastic Surgeon', 19, 'Agra', 'Uttar Pradesh', '55', 1500, False, 4.202474452300957, 21, '2025-05-14 11:51:02.851619', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MCh'', ''institution'': '''', ''year'': ''''}]', NULL, 'MBBS, MS, MCh', '55, Vimal Vihar', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/8/0/9/2615503-2595961.jpg', 'https://fi.realself.com/300/8/0/9/2615503-2595961.jpg'),
(33, 40, 'Dr. Biraj Naithani', 'Plastic Surgeon', 27, 'Noida', 'Uttar Pradesh', 'Max Hospital Noida A-364 Sector 19', 1500, False, 4.347207478800015, 11, '2025-05-14 11:59:29.277505', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MCh'', ''institution'': '''', ''year'': ''''}]', NULL, 'MBBS, MS, MCh', 'Max Hospital Noida A-364 Sector 19', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/4/c/a/1238724-1967388.jpg', 'https://fi.realself.com/300/4/c/a/1238724-1967388.jpg'),
(34, 41, 'Dr. Sukhbir Singh', 'Plastic Surgeon', 15, 'New Delhi', 'Delhi', 'R-9', 1500, False, 4.751382368114941, 82, '2025-05-14 11:59:30.555714', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''DNB'', ''institution'': '''', ''year'': ''''}]', NULL, 'MBBS, MS, DNB', 'R-9, Hansraj Gupta Rd.', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/9/c/0/11747782-5014231.png', 'https://fi.realself.com/300/9/c/0/11747782-5014231.png'),
(35, 42, 'Dr. Ramakant Bembde', 'Plastic Surgeon', 26, 'Aurangabad', 'Maharashtra', 'Bembde Hospital', 1500, False, 4.164435401847482, 31, '2025-05-14 11:59:31.856714', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MCh'', ''institution'': '''', ''year'': ''''}, {''degree'': ''DNB'', ''institution'': '''', ''year'': ''''}]', NULL, 'MCh, DNB', 'Bembde Hospital, Beed Bypass Rd, Satara Parisar', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/9/a/5/7919822-3944702.jpeg', 'https://fi.realself.com/300/9/a/5/7919822-3944702.jpeg'),
(36, 43, 'Dr. Thangavel Ayyappan', 'Plastic Surgeon', 30, 'Ahmedabad', 'Gujarat', 'SAL Hospital', 1500, False, 4.12282831885586, 19, '2025-05-14 11:59:33.129730', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MCh'', ''institution'': '''', ''year'': ''''}, {''degree'': ''DNB'', ''institution'': '''', ''year'': ''''}]', NULL, 'MBBS, MS, MCh, DNB', 'SAL Hospital, Opp. Vastrapur Police Station, Drive in Rd.', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/b/a/f/253449-1971158.jpg', 'https://fi.realself.com/300/b/a/f/253449-1971158.jpg'),
(37, 44, 'Dr. Sharad Mishra', 'Plastic Surgeon', 19, 'New Delhi', 'Delhi', '1001', 1500, False, 4.39395707268412, 55, '2025-05-14 11:59:34.432830', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MS'', ''institution'': '''', ''year'': ''''}, {''degree'': ''MCh'', ''institution'': '''', ''year'': ''''}]', NULL, 'MS, MCh', '1001, 10th Floor, Padma Tower 1', 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/d/c/e/906362-2847298-T1479410442.639.png', 'https://fi.realself.com/300/d/c/e/906362-2847298-T1479410442.639.png'),
(39, 46, 'Dr. Bhavna Patel', 'Plastic Surgeon', 12, 'Delhi', NULL, NULL, 1500, False, 4.7, 28, '2025-05-14 12:27:08.015501', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(41, 48, 'Dr. Divya Agarwal', 'Aesthetic Surgeon', 10, 'Chennai', NULL, NULL, 1600, False, 4.6, 31, '2025-05-14 12:28:12.558504', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(43, 50, 'Dr. Hina Khan', 'Aesthetic Surgeon', 12, 'Ahmedabad', NULL, NULL, 1700, False, 4.6, 31, '2025-05-14 12:30:45.485271', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(44, 51, 'Dr. Gaurav Singh', 'Plastic Surgeon', 16, 'Kolkata', NULL, NULL, 1800, False, 4.9, 42, '2025-05-14 12:30:45.485271', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(70, 78, 'Dr. Abhishek Vijayakumar', 'Plastic Surgeon', 14, 'Bangalore', 'Karnataka', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:19.317644', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/b/1/b/6465983-3418788.jpeg', 'https://fi.realself.com/300/b/1/b/6465983-3418788.jpeg'),
(71, 79, 'Dr. Prerna Mittal', 'Plastic Surgeon', 12, 'Ludhiana', 'Punjab', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:20.462522', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/e/6/5/7523884-3857491.jpg', 'https://fi.realself.com/300/e/6/5/7523884-3857491.jpg'),
(72, 80, 'Dr. Karishma Kagodu', 'Plastic Surgeon', 14, 'Bengaluru', 'Karnataka', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:21.590460', '', NULL, NULL, NULL, '[''(Not specified)'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/6/f/e/6647236-3451552.png', 'https://fi.realself.com/300/6/f/e/6647236-3451552.png'),
(73, 81, 'Dr. Alexander George', 'Plastic Surgeon', 31, '(Not specified)', 'Kerala', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:50.624470', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/3/1/e/3306036-2764468-T1479416037.501.jpg', 'https://fi.realself.com/300/3/1/e/3306036-2764468-T1479416037.501.jpg'),
(74, 82, 'Dr. Salil Patil', 'Plastic Surgeon', 12, 'Pune', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:51.702613', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/0/8/0/6260978-3366185.JPG', 'https://fi.realself.com/300/0/8/0/6260978-3366185.JPG'),
(75, 83, 'Dr. Jyoshid R. Balan', 'Plastic Surgeon', 12, 'Thrissur', 'Kerala', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:52.801160', '', NULL, NULL, NULL, '[''MBBS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/e/5/0/12557561-5471909.png', 'https://fi.realself.com/300/e/5/0/12557561-5471909.png'),
(79, 87, 'Dr. Rustom Ginwalla', 'Plastic Surgeon', 19, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:17:16.225068', '', NULL, NULL, NULL, '[''MBBS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/6/0/b/1367869-4453752.jpeg', 'https://fi.realself.com/300/6/0/b/1367869-4453752.jpeg'),
(80, 88, 'Dr. Krishan Mohan Kapoor', 'Plastic Surgeon', 24, 'Chandigarh', 'Chandigarh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:17:17.391072', '', NULL, NULL, NULL, '[''MS, MCh, DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/6/f/e/1312595-2041501-T1479412492.027.jpg', 'https://fi.realself.com/300/6/f/e/1312595-2041501-T1479412492.027.jpg'),
(81, 89, 'Dr. Kiran Naik', 'Plastic Surgeon', 27, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:17:18.497417', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/2/7/5/5628889-3559725-T1529681640.479.jpg', 'https://fi.realself.com/300/2/7/5/5628889-3559725-T1529681640.479.jpg'),
(82, 90, 'Dr. Sasikumar Muthu', 'Plastic Surgeon', 18, 'Chennai', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:17:19.599578', '', NULL, NULL, NULL, '[''MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/d/1/6/1929246-4392628.jpeg', 'https://fi.realself.com/300/d/1/6/1929246-4392628.jpeg'),
(83, 91, 'Dr. Audumbar Borgaonkar', 'Plastic Surgeon', 15, 'Navi Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:18:28.658443', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/a/2/9/4319546-2930082-T1488481911.256.png', 'https://fi.realself.com/300/a/2/9/4319546-2930082-T1488481911.256.png'),
(89, 97, 'Dr. Arunesh Gupta', 'Plastic Surgeon', 20, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:19:23.328305', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/d/0/0/6398183-3398360.png', 'https://fi.realself.com/300/d/0/0/6398183-3398360.png'),
(91, 99, 'Dr. Ram Chilgar', 'Plastic Surgeon', 14, 'Aurangabad', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:19:25.456210', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/6/d/7/2643776-4000846.jpeg', 'https://fi.realself.com/300/6/d/7/2643776-4000846.jpeg'),
(92, 100, 'Dr. Ashish Sangvikar', 'Plastic Surgeon', 15, 'Navi Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:19:26.539606', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/b/d/c/9564972-4401989.jpeg', 'https://fi.realself.com/300/b/d/c/9564972-4401989.jpeg'),
(93, 101, 'Dr. BRN Padmini', 'Plastic Surgeon', 19, 'Hyderabad', 'Telangana', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:12.004227', '', NULL, NULL, NULL, '[''MBBS, MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/4/7/6/12135878-5207523.png', 'https://fi.realself.com/300/4/7/6/12135878-5207523.png'),
(94, 102, 'Dr. Vinay Jacob', 'Plastic Surgeon', 24, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:13.197045', '', NULL, NULL, NULL, '[''MS, MCh, DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/f/c/6/5739434-3241166.png', 'https://fi.realself.com/300/f/c/6/5739434-3241166.png'),
(95, 103, 'Dr. Lakshyajit Dhami', 'Plastic Surgeon', 47, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:28:14.346197', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/a/9/a/4720117-2999049.jpg', 'https://fi.realself.com/300/a/9/a/4720117-2999049.jpg'),
(102, 110, 'Dr. Aamod Rao', 'Plastic Surgeon', 15, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:29:20.168284', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/c/e/e/1223429-3546981.jpg', 'https://fi.realself.com/300/c/e/e/1223429-3546981.jpg'),
(69, 77, 'Dr. Rohit Krishna', 'Plastic Surgeon', 30, 'New Delhi', 'Delhi', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:18.159480', '', NULL, NULL, NULL, '[''MBBS, MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-default.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-default.jpg'),
(90, 98, 'Dr. Hirenkumar Bhatt', 'Plastic Surgeon', 28, 'Vadodara', 'Gujarat', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:19:24.395666', '', NULL, NULL, NULL, '[''MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-143138.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-143138.jpg'),
(13, 14, 'Dr. Sameer Karkhanis', 'Plastic Surgeon', 20, 'Thane', 'Maharashtra', 'Centre for Cosmetic and Reconstructive Surgery, Karkhanis Super Speciality Hospital, Tikuji–ni–Wadi', 1000, True, 4.0, 0, NULL, 'Dr. Karkhanis is a Plastic Surgeon with 20 years of experience.', NULL, NULL, NULL, '{''degrees'': [''MS'', ''DNB'']}', NULL, NULL, NULL, 'approved', '2025-05-14 08:08:07.092106', NULL, NULL, NULL, 'https://fi.realself.com/300/1/1/4/587668-3189559.JPG', 'https://fi.realself.com/300/1/1/4/587668-3189559.JPG'),
(27, 33, 'Dr. Ashish Davalbhakta', 'Plastic Surgeon', 25, 'Pune', 'Maharashtra', '2, Sneh Riviera, Next to Model colony lake, Off FC rd or Lakaki Road', NULL, True, 4.627489165687683, 48, NULL, NULL, NULL, NULL, NULL, '{''degrees'': [''MBBS'', ''MCh(Plast)'', ''FRCS'']}', NULL, NULL, NULL, 'approved', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/a/c/4/1231097-1963140.jpg', 'https://fi.realself.com/300/a/c/4/1231097-1963140.jpg'),
(60, 67, 'Dr. Sudhanva H Kumar', 'Plastic Surgeon', 10, 'Mumbai', 'Maharashtra', NULL, 2500, False, 4.645614317194456, 37, '2025-05-14 13:05:11.227839', 'Dr. Sudhanva H Kumar is a respected medical professional with expertise in Plastic Surgeon.', '[]', NULL, NULL, '[{''degree'': ''DNB''}, {''degree'': ''MCh''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/d/c/9/13458780-7012276.png', 'https://fi.realself.com/300/d/c/9/13458780-7012276.png'),
(61, 68, 'Dr. Raja Tiwari', 'Plastic Surgeon', 16, 'New Delhi', 'Delhi', NULL, 3100, False, 4.8015332209457755, 37, '2025-05-14 13:05:12.106653', 'Dr. Raja Tiwari is a respected medical professional with expertise in Plastic Surgeon.', '[]', NULL, NULL, '[{''degree'': ''MCh''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/b/8/4/8996405-4903407.png', 'https://fi.realself.com/300/b/8/4/8996405-4903407.png'),
(62, 69, 'Dr. Surindher DSA', 'Plastic Surgeon', 24, 'Bangalore', 'Karnataka', NULL, 3900, False, 4.778311177931014, 24, '2025-05-14 13:05:12.957737', 'Dr. Surindher DSA is a respected medical professional with expertise in Plastic Surgeon.', '[]', NULL, NULL, '[{''degree'': ''MS''}, {''degree'': ''MCh (Plast)''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/e/b/4/1744229-4088674.jpeg', 'https://fi.realself.com/300/e/b/4/1744229-4088674.jpeg'),
(63, 70, 'Dr. Madhu Kumar', 'Plastic Surgeon', 20, 'Bangalore', 'Karnataka', NULL, 3500, False, 4.5395239702276395, 48, '2025-05-14 13:06:43.674637', 'Dr. Madhu Kumar is a respected medical professional with expertise in Plastic Surgeon.', '[]', NULL, NULL, '[{''degree'': ''MCh''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/e/b/d/2249117-2464237.png', 'https://fi.realself.com/300/e/b/d/2249117-2464237.png'),
(64, 71, 'Dr. Harsh B. Amin', 'Plastic Surgeon', 14, 'Ahmedabad', 'Gujarat', NULL, 2900, False, 4.9992574196799975, 37, '2025-05-14 13:06:44.527248', 'Dr. Harsh B. Amin is a respected medical professional with expertise in Plastic Surgeon.', '[]', NULL, NULL, '[{''degree'': ''MS''}, {''degree'': ''MCh''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/e/8/b/1723566-8134992.png', 'https://fi.realself.com/300/e/8/b/1723566-8134992.png'),
(65, 72, 'Dr. Charanjeev Sobti', 'Plastic Surgeon', 28, 'New Delhi', 'Delhi', NULL, 4300, False, 4.866060855930862, 24, '2025-05-14 13:06:45.380933', 'Dr. Charanjeev Sobti is a respected medical professional with expertise in Plastic Surgeon.', '[]', NULL, NULL, '[{''degree'': ''MBBS''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/0/9/c/1228520-1961981.png', 'https://fi.realself.com/300/0/9/c/1228520-1961981.png'),
(68, 76, 'Dr. Sumit Saxena', 'Plastic Surgeon', 21, 'Pune', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:16.996094', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/2/a/8/1707928-2221095-T1479410859.871.jpg', 'https://fi.realself.com/300/2/a/8/1707928-2221095-T1479410859.871.jpg'),
(76, 84, 'Dr. Girish Amarapuram Chandramouly', 'Plastic Surgeon', 17, 'Bangalore', 'Karnataka', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:53.889212', '', NULL, NULL, NULL, '[''MBBS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/8/5/c/6356958-3390288.png', 'https://fi.realself.com/300/8/5/c/6356958-3390288.png'),
(77, 85, 'Dr. Ashwani Kumar', 'Plastic Surgeon', 11, 'New Delhi', 'Delhi', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:16:54.964579', '', NULL, NULL, NULL, '[''MBBS, MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/5/b/7/10399809-4626778.jpeg', 'https://fi.realself.com/300/5/b/7/10399809-4626778.jpeg'),
(78, 86, 'Dr. Prince HP', 'Plastic Surgeon', 14, 'Thrissur', 'Kerala', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:17:15.111962', '', NULL, NULL, NULL, '[''MBBS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/0/4/5/11658826-5183755.png', 'https://fi.realself.com/300/0/4/5/11658826-5183755.png'),
(84, 92, 'Dr. Vikram Kumar Raja', 'Plastic Surgeon', 15, 'Coimbatore', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:18:29.737981', '', NULL, NULL, NULL, '[''MBBS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/f/7/6/2308596-2493283.png', 'https://fi.realself.com/300/f/7/6/2308596-2493283.png'),
(85, 93, 'Dr. Srinjoy Saha', 'Plastic Surgeon', 17, 'Kolkata', 'West Bengal', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:18:30.812091', '', NULL, NULL, NULL, '[''MD, FACS, FRCS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/2/f/c/1493955-5086815.png', 'https://fi.realself.com/300/2/f/c/1493955-5086815.png'),
(86, 94, 'Dr. Vybhav Deraje', 'Plastic Surgeon', 12, 'Bangalore', 'Karnataka', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:18:31.897209', '', NULL, NULL, NULL, '[''DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/1/6/0/10465503-4631707.jpeg', 'https://fi.realself.com/300/1/6/0/10465503-4631707.jpeg'),
(87, 95, 'Dr. Vicky Jain', 'Plastic Surgeon', 12, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:18:32.965551', '', NULL, NULL, NULL, '[''MBBS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/c/4/e/9704778-4424215.jpeg', 'https://fi.realself.com/300/c/4/e/9704778-4424215.jpeg'),
(88, 96, 'Dr. Anoop G. Mohan', 'Plastic Surgeon', 11, 'Kollam', 'Kerala', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:19:22.254055', '', NULL, NULL, NULL, '[''MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://fi.realself.com/300/d/c/0/9444189-4348996.jpeg', 'https://fi.realself.com/300/d/c/0/9444189-4348996.jpeg'),
(110, 118, 'Dr. Kannan Prema', 'Plastic Surgeon', 15, 'Chennai', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:30:31.173283', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-140000.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-140000.jpg'),
(113, 121, 'Dr. Rohit Munot', 'Plastic Surgeon', 15, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:03.051106', '', NULL, NULL, NULL, '[''MD, MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-147999.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-147999.jpg'),
(116, 124, 'Dr. Shivprasad Date', 'Plastic Surgeon', 15, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:37.692475', '', NULL, NULL, NULL, '[''MCh, MRCS (Edinburgh)'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-122163.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-122163.jpg'),
(46, 53, 'Dr. Leela Reddy', 'Plastic Surgeon', 17, 'Bhopal', NULL, NULL, 1800, False, 4.9, 44, '2025-05-14 12:31:45.329257', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(48, 55, 'Dr. Jayshree Naidu', 'Facial Plastic Surgeon', 11, 'Lucknow', NULL, NULL, 1600, False, 4.7, 26, '2025-05-14 12:31:45.329257', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(118, 126, 'Dr. Devi Prasad Mohapatra', 'Plastic Surgeon', 15, 'Gorimedu', 'Puducherry', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:39.965090', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(120, 128, 'Dr. Dinesh Kadam', 'Plastic Surgeon', 15, 'Mangalore', 'Karnataka', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:42.260638', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(122, 130, 'Dr. James Kanjoor', 'Plastic Surgeon', 15, 'Coimbatore', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:32:13.218922', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(124, 132, 'Dr. Hafiz Koyappathody', 'Plastic Surgeon', 15, 'Calicut', 'Kerala', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:32:15.479122', '', NULL, NULL, NULL, '[''MS, MCh, FRCSEd'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(126, 134, 'Dr. Ramasamy Lingappan', 'Plastic Surgeon', 15, 'Madurai', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:33:24.371322', '', NULL, NULL, NULL, '[''MCh (Plastic Surgery)'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(128, 136, 'Dr. Raj Mishra', 'Plastic Surgeon', 15, 'Lucknow', 'Uttar Pradesh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:33:26.676959', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(130, 138, 'Dr. Satya Saraswat', 'Plastic Surgeon', 15, 'Agra', 'Uttar Pradesh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:33:58.831618', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(132, 140, 'Dr. Mohammed Fahud Khurram', 'Plastic Surgeon', 15, 'Aligarh', 'Uttar Pradesh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:34:01.019135', '', NULL, NULL, NULL, '[''MD, MBBS, MS, MCh, DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(104, 112, 'Dr. Ravi Annamaneni', 'Plastic Surgeon', 15, 'Hyderabad', 'Telangana', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:29:22.425570', '', NULL, NULL, NULL, '[''MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-139910.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-139910.jpg'),
(106, 114, 'Dr. Parag Sahasrabudhe', 'Plastic Surgeon', 15, 'Pune', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:30:26.797128', '', NULL, NULL, NULL, '[''Prof. and Head, MD, MCh, FRCS Ed'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-173863.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-173863.jpg'),
(108, 116, 'Dr. Hitesh Laad', 'Plastic Surgeon', 15, 'Pune', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:30:28.970569', '', NULL, NULL, NULL, '[''MD, MS, MCh, DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-169310.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-169310.jpg'),
(134, 142, 'Dr. Amitabh Singh', 'Plastic Surgeon', 15, 'Gurgaon', 'Haryana', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:34:03.210307', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(103, 111, 'Dr. Rajesh Yellinedi', 'Plastic Surgeon', 15, 'Hyderabad', 'Telangana', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:29:21.297469', '', NULL, NULL, NULL, '[''MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-145730.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-145730.jpg'),
(117, 125, 'Dr. M.T. Friji', 'Plastic Surgeon', 15, 'Pondicherry', 'Puducherry', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:38.824368', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(119, 127, 'Dr. Santosh Bhatia', 'Plastic Surgeon', 15, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:41.116351', '', NULL, NULL, NULL, '[''MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(121, 129, 'Dr. Ved Prakash Cheruvu', 'Plastic Surgeon', 15, 'Bhopal', 'Madhya Pradesh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:32:12.113570', '', NULL, NULL, NULL, '[''MS, MCh, FCAPS, FACS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(123, 131, 'Dr. Hari Venkatramani', 'Plastic Surgeon', 15, 'Coimbatore', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:32:14.316879', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(125, 133, 'Dr. Shashank Shringarpure', 'Plastic Surgeon', 15, 'Baroda', 'Gujarat', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:33:23.226936', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(127, 135, 'Dr. Shailendra Singh', 'Plastic Surgeon', 15, 'Shela', 'Gujarat', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:33:25.531598', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(129, 137, 'Dr. Amit Agarwal', 'Plastic Surgeon', 15, 'Lucknow', 'Uttar Pradesh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:33:27.809697', '', NULL, NULL, NULL, '[''MCh, DNB'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(131, 139, 'Dr. Shabbir Warsi', 'Plastic Surgeon', 15, 'Patna', 'Bihar', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:33:59.924903', '', NULL, NULL, NULL, '[''MBBS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(133, 141, 'Dr. Kaushik Nandy', 'Plastic Surgeon', 15, 'Kolkata', 'West Bengal', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:34:02.104585', '', NULL, NULL, NULL, '[''MD, FRCS'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(38, 45, 'Dr. Anand Sharma', 'Cosmetic Surgeon', 15, 'Mumbai', NULL, NULL, 1500, False, 4.8, 35, '2025-05-14 12:26:57.519854', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(40, 47, 'Dr. Chetan Desai', 'Facial Plastic Surgeon', 18, 'Bengaluru', NULL, NULL, 1800, False, 4.9, 42, '2025-05-14 12:28:01.460638', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(42, 49, 'Dr. Eshan Gupta', 'Plastic Surgeon', 14, 'Hyderabad', NULL, NULL, 1700, False, 4.8, 39, '2025-05-14 12:29:28.464872', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(45, 52, 'Dr. Falguni Mehta', 'Cosmetic Dermatologist', 9, 'Pune', NULL, NULL, 1600, False, 4.7, 29, '2025-05-14 12:30:45.485271', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(47, 54, 'Dr. Kunal Verma', 'Cosmetic Surgeon', 13, 'Chandigarh', NULL, NULL, 1750, False, 4.8, 35, '2025-05-14 12:31:45.329257', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL);

INSERT INTO "doctors" ("id", "user_id", "name", "specialty", "experience", "city", "state", "hospital", "consultation_fee", "is_verified", "rating", "review_count", "created_at", "bio", "certifications", "video_url", "success_stories", "education", "medical_license_number", "qualification", "practice_location", "verification_status", "verification_date", "verification_notes", "credentials_url", "aadhaar_number", "profile_image", "image_url") VALUES
(49, 56, 'Dr. Imran Ali', 'Plastic Surgeon', 14, 'Jaipur', NULL, NULL, 1700, False, 4.8, 38, '2025-05-14 12:31:45.329257', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(50, 57, 'Dr. Omkar Kulkarni', 'Plastic Surgeon', 18, 'Surat', NULL, NULL, 1800, False, 4.9, 45, '2025-05-14 12:32:49.561847', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(51, 58, 'Dr. Neha Malhotra', 'Cosmetic Dermatologist', 9, 'Nagpur', NULL, NULL, 1600, False, 4.7, 28, '2025-05-14 12:32:49.561847', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(52, 59, 'Dr. Manish Joshi', 'Aesthetic Surgeon', 15, 'Indore', NULL, NULL, 1700, False, 4.8, 36, '2025-05-14 12:32:49.561847', 'Experienced healthcare professional specializing in cosmetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Medical College'', ''year'': ''''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(53, 60, 'Dr. Priya Sharma', 'Cosmetic Surgeon', 15, 'Mumbai', 'Maharashtra', NULL, 3000, False, 4.9, 44, '2025-05-14 12:52:51.531646', 'Experienced cosmetic surgeon specializing in facial rejuvenation and body contouring procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Grant Medical College'', ''year'': ''2000''}, {''degree'': ''MS'', ''institution'': ''King Edward Memorial Hospital'', ''year'': ''2004''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(54, 61, 'Dr. Vikram Reddy', 'Plastic Surgeon', 18, 'Hyderabad', 'Telangana', NULL, 3300, False, 4.8, 48, '2025-05-14 12:52:51.531646', 'Leading plastic surgeon with expertise in reconstructive and aesthetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Osmania Medical College'', ''year'': ''1998''}, {''degree'': ''MCh'', ''institution'': ''NIMS Hyderabad'', ''year'': ''2003''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(105, 113, 'Dr. Baburao Ravuri', 'Plastic Surgeon', 15, 'Tirupati', 'Andhra Pradesh', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:29:23.558357', '', NULL, NULL, NULL, '[''MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-145739.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-145739.jpg'),
(107, 115, 'Dr. PARIMAL KULKARNI', 'Plastic Surgeon', 15, 'Pune', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:30:27.883342', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-148005.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-148005.jpg'),
(109, 117, 'Dr. Karthik Ramasamy', 'Plastic Surgeon', 15, 'Chennai', 'Tamil Nadu', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:30:30.076433', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-121299.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-121299.jpg'),
(111, 119, 'Dr. Vinod Vij', 'Plastic Surgeon', 15, 'Vashi', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:00.855402', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-112542.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-112542.jpg'),
(112, 120, 'Dr. Mukund Jagannathan', 'Plastic Surgeon', 15, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:01.950970', '', NULL, NULL, NULL, '[''MD'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-40897.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-40897.jpg'),
(114, 122, 'Dr. Saumya Mathews', 'Plastic Surgeon', 15, 'Mumbai', 'Maharashtra', NULL, NULL, NULL, NULL, NULL, '2025-05-14 13:31:04.144015', '', NULL, NULL, NULL, '[''MS, MCh'']', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'https://cdn.plasticsurgery.org/images/profile/crop-163595.jpg', 'https://cdn.plasticsurgery.org/images/profile/crop-163595.jpg'),
(55, 62, 'Dr. Anjali Mehta', 'Dermatologist', 12, 'Bangalore', 'Karnataka', NULL, 2700, False, 4.9, 44, '2025-05-14 12:52:51.531646', 'Specialized in advanced cosmetic dermatology and skincare treatments.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': "St. John''s Medical College", ''year'': ''2005''}, {''degree'': ''MD'', ''institution'': ''AIIMS Bangalore'', ''year'': ''2009''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(56, 63, 'Dr. Rahul Singh', 'Facial Plastic Surgeon', 14, 'Delhi', 'Delhi', NULL, 2900, False, 4.7, 32, '2025-05-14 12:52:51.531646', 'Expert in facial plastic surgery with focus on natural-looking results.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Maulana Azad Medical College'', ''year'': ''2003''}, {''degree'': ''MS'', ''institution'': ''AIIMS Delhi'', ''year'': ''2008''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(57, 64, 'Dr. Sunita Patel', 'Aesthetic Surgeon', 10, 'Ahmedabad', 'Gujarat', NULL, 2500, False, 4.5, 20, '2025-05-14 12:52:51.531646', 'Specializes in modern aesthetic procedures with minimal recovery time.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''BJ Medical College'', ''year'': ''2007''}, {''degree'': ''DNB'', ''institution'': ''Sterling Hospital'', ''year'': ''2013''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(58, 65, 'Dr. Rajesh Kumar', 'Plastic Surgeon', 16, 'Kolkata', 'West Bengal', NULL, 3100, False, 4.9, 34, '2025-05-14 12:52:51.531646', 'Experienced plastic surgeon specializing in reconstructive and aesthetic procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''Calcutta Medical College'', ''year'': ''2002''}, {''degree'': ''MS'', ''institution'': ''IPGMER Kolkata'', ''year'': ''2007''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL),
(59, 66, 'Dr. Meera Joshi', 'Cosmetic Dermatologist', 9, 'Pune', 'Maharashtra', NULL, 2400, False, 4.7, 27, '2025-05-14 12:52:51.531646', 'Specializes in advanced cosmetic dermatology with focus on non-invasive procedures.', '[]', NULL, NULL, '[{''degree'': ''MBBS'', ''institution'': ''BJ Medical College Pune'', ''year'': ''2009''}, {''degree'': ''MD'', ''institution'': ''Seth GS Medical College'', ''year'': ''2013''}]', NULL, NULL, NULL, 'pending', NULL, NULL, NULL, NULL, NULL, NULL);

SELECT setval(pg_get_serial_sequence('doctors', 'id'), 134, true);


\echo 'Importing doctor_procedures...'
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


\echo 'Importing doctor_categories...'
-- SQL for table: doctor_categories
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "doctor_categories" (
    "id" SERIAL PRIMARY KEY,
    "doctor_id" INTEGER NOT NULL,
    "category_id" INTEGER NOT NULL,
    "created_at" TIMESTAMP NULL,
    "is_verified" BOOLEAN NULL
);


\echo 'Importing banners...'
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


\echo 'Importing banner_slides...'
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


\echo 'Importing community...'
-- SQL for table: community
-- Generated: 2025-05-15 17:44:41
-- Row count: 147

CREATE TABLE IF NOT EXISTS "community" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    "title" TEXT NOT NULL,
    "content" TEXT NOT NULL,
    "is_anonymous" BOOLEAN NULL,
    "created_at" TIMESTAMP NULL,
    "updated_at" TIMESTAMP NULL,
    "view_count" INTEGER NULL,
    "reply_count" INTEGER NULL,
    "featured" BOOLEAN NULL,
    "tags" ARRAY NULL,
    "category_id" INTEGER NULL,
    "procedure_id" INTEGER NULL,
    "parent_id" INTEGER NULL,
    "photo_url" TEXT NULL,
    "video_url" TEXT NULL
);

INSERT INTO "community" ("id", "user_id", "title", "content", "is_anonymous", "created_at", "updated_at", "view_count", "reply_count", "featured", "tags", "category_id", "procedure_id", "parent_id", "photo_url", "video_url") VALUES
(1, 14, 'My experience with Rhinoplasty - What I wish I knew before', 'I recently underwent rhinoplasty to fix both functional and aesthetic issues with my nose. I wanted to share my experience and what I wish I had known beforehand.

First, the recovery was much longer than I expected. While the initial pain subsided after about a week, the swelling took months to completely resolve. Even now, 6 months later, I still have some minor swelling that''s only noticeable to me.

Second, finding the right surgeon is crucial. I spent months researching doctors, looking at before and after photos, and reading reviews. This paid off tremendously as I''m very happy with my results.

Third, the psychological aspect was unexpected. There''s a period after surgery where your nose looks worse than before due to swelling, and this can be emotionally challenging.

Has anyone else gone through rhinoplasty? What was your experience like? Anything you wish you had known?', False, '2025-04-14 20:16:38.010897', '2025-04-19 20:16:38.010897', 150, 1, True, '[''rhinoplasty'', ''recovery'', ''plastic surgery'']', 1, 1, NULL, NULL, NULL),
(2, 37, 'Breast Augmentation Recovery Timeline - My Weekly Progress', 'I''m documenting my breast augmentation recovery journey for anyone considering this procedure.

Week 1: The first few days were the hardest. Pain was manageable with prescribed medication, but movement was very limited. Slept in a reclined position on pillows.

Week 2: Started to feel more like myself. Reduced pain medication to just over-the-counter options. Still wearing the surgical bra 24/7.

Week 3: Bruising has mostly faded. Switched to a sports bra. Started light daily activities but still avoiding lifting anything heavy.

Week 4: Feeling almost normal now! Implants are still high and tight, but my surgeon says this is normal and they''ll "drop and fluff" over the next few months.

Now at 6 weeks post-op, I can do most activities except heavy lifting and chest exercises. The scars are healing nicely, and I''m applying silicone sheets as recommended by my doctor.

Would love to hear others'' experiences with recovery timelines!', False, '2025-04-24 20:21:08.203152', '2025-04-25 20:21:08.203152', 648, 2, True, '[''breast augmentation'', ''breast implants'', ''recovery'', ''plastic surgery'']', 1, 1, NULL, NULL, NULL),
(3, 104, 'Considering a BBL - Safety Concerns and Doctor Recommendations', 'I''ve been researching Brazilian Butt Lift procedures and am considering getting one, but I''m concerned about the safety risks I''ve read about.

I understand that BBLs have had higher complication rates than other cosmetic procedures, particularly related to fat embolism if fat is injected into the muscle.

Can anyone share experiences with this procedure? Have the newer techniques made it safer? And most importantly, can you recommend surgeons in Mumbai or Delhi who specialize in safer BBL techniques?

I''m looking for someone who is board-certified and has extensive experience specifically with BBLs. Any advice or personal experiences would be greatly appreciated!', True, '2025-05-04 20:21:11.838168', '2025-05-06 20:21:11.838168', 642, 0, False, '[''bbl'', ''brazilian butt lift'', ''safety'', ''doctor recommendations'']', 3, 3, NULL, NULL, NULL),
(4, 95, 'Tummy Tuck and C-section scar - Special considerations?', 'I''ve had two C-sections and am planning to get a tummy tuck to address the loose skin and separated muscles (diastasis recti). I''m wondering if having C-section scars creates any special considerations for a tummy tuck.

Will the surgeon remove my C-section scar as part of the procedure? Does having previous abdominal surgery make the recovery more difficult? Are there any specific questions I should ask surgeons about this during consultations?

If you''ve had a tummy tuck after C-sections, I''d love to hear about your experience and results. Also, how long did you wait after your last pregnancy before getting a tummy tuck?', False, '2025-05-08 20:22:52.801644', '2025-05-11 20:22:52.801644', 876, 1, False, '[''tummy tuck'', ''abdominoplasty'', ''c-section'', ''diastasis recti'']', 2, 2, NULL, NULL, NULL),
(5, 86, 'How long did your bruising last after liposuction?', 'I had liposuction on my abdomen and flanks 10 days ago, and while the pain has subsided, I''m still quite bruised. My surgeon said this is normal, but I''m curious about others'' experiences.

How long did it take for your bruising to completely resolve after lipo? Did you do anything that seemed to help speed up the process? I''ve been taking arnica and applying arnica gel, but I''m not sure if it''s making a difference.

Also, I''m still wearing the compression garment 24/7 as instructed. When were you able to stop wearing it, or at least reduce the hours?', True, '2025-05-12 20:23:02.544529', '2025-05-17 20:23:02.544529', 153, 1, False, '[''liposuction'', ''bruising'', ''recovery'', ''compression garment'']', 7, 9, NULL, NULL, NULL),
(6, 50, 'Realistic expectations for Eyelid Surgery (Blepharoplasty) results', 'I''m 52 and considering upper and lower blepharoplasty to address my droopy eyelids and under-eye bags. I''ve done some research, but I''d like to hear from people who''ve had this procedure.

What kind of results can I realistically expect? How much younger did it make you look? Were there any unexpected changes to your appearance? I want to look refreshed but still like myself.

I''m also curious about recovery and downtime. How long before you were comfortable going out in public? Did you experience any dry eye issues after surgery?

Thank you for any insights you can share!', False, '2025-05-03 20:23:12.369693', '2025-05-08 20:23:12.369693', 375, 1, False, '[''blepharoplasty'', ''eyelid surgery'', ''aging'', ''facial rejuvenation'']', 6, 8, NULL, NULL, NULL),
(7, 78, 'How to hide Macrolane from family/coworkers', 'I want to get Macrolane but I don''t want my family/coworkers to know. Has anyone successfully kept their procedure private? What excuses did you use for your recovery time? Any specific tips for hiding healing/results?', False, '2024-12-21 20:39:15.040992', '2025-01-03 20:39:15.040992', 434, 1, False, NULL, 11, 479, NULL, NULL, NULL),
(8, 95, 'Is Nonsurgical Butt Lift worth it? Long-term results', 'I''m considering Nonsurgical Butt Lift but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets or things you wish you knew beforehand?', False, '2025-04-05 20:39:15.529852', '2025-04-06 20:39:15.529852', 15, 5, False, NULL, 3, 269, NULL, NULL, NULL),
(9, 114, 'Natural-looking results after Areola Reduction Surgery', 'I''m interested in getting Areola Reduction Surgery but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2024-12-20 20:39:15.957730', '2025-01-13 20:39:15.957730', 444, 2, False, NULL, 1, 221, NULL, NULL, NULL),
(10, 82, 'Pain level during recovery from diVa Vaginal Laser', 'For those who''ve had diVa Vaginal Laser, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last? I have a low pain tolerance, so I''m trying to prepare mentally.', True, '2024-11-22 20:39:16.383749', '2024-12-07 20:39:16.383749', 358, 1, False, NULL, 40, 263, NULL, NULL, NULL),
(11, 48, 'Is Lipedema Surgery worth it? Long-term results', 'I''m considering Lipedema Surgery but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets or things you wish you knew beforehand?', False, '2025-02-01 20:39:16.808624', '2025-02-16 20:39:16.808624', 40, 2, False, NULL, 7, 127, NULL, NULL, NULL),
(12, 117, 'How to prepare for Kybella - Tips and advice', 'I''m scheduled for Kybella in 3 weeks. What preparations should I make before the surgery? Any specific supplements to avoid? How did you prepare your home/living space for recovery? I want to make sure I''m fully prepared.', True, '2025-01-25 20:39:17.236663', '2025-02-23 20:39:17.236663', 63, 0, True, NULL, 23, 75, NULL, NULL, NULL),
(13, 132, 'Psychological readiness for Liposuction Revision', 'How do you know if you''re psychologically ready for Liposuction Revision? I''ve wanted this for years but still feel nervous about permanent changes. Did anyone work with a therapist before deciding? How did you know you were making the right choice?', False, '2024-12-26 20:39:17.670145', '2025-01-23 20:39:17.670145', 28, 4, False, NULL, 7, 98, NULL, NULL, NULL),
(14, 94, 'Lipodissolve during pregnancy planning', 'I want to have Lipodissolve but I''m also planning to get pregnant within the next 1-2 years. Should I wait until after having children? Will pregnancy affect the results of the procedure? Has anyone had this procedure before pregnancy?', False, '2025-03-23 20:39:18.101242', '2025-03-29 20:39:18.101242', 95, 5, False, NULL, 7, 179, NULL, NULL, NULL),
(15, 79, 'Cultural taboos and Sofwave in India', 'I come from a conservative Indian family and I''m considering Sofwave. Has anyone navigated cultural taboos around cosmetic procedures? How did you handle family reactions or pressure? Any advice for addressing traditional mindsets?', True, '2024-12-22 20:39:18.580378', '2024-12-29 20:39:18.580378', 148, 1, False, NULL, 26, 176, NULL, NULL, NULL),
(16, 115, 'Is Microneedling RF worth it? Long-term results', 'I''m considering Microneedling RF but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets or things you wish you knew beforehand?', False, '2025-03-09 20:39:19.007198', '2025-03-29 20:39:19.007198', 298, 0, False, NULL, 27, 184, NULL, NULL, NULL),
(17, 51, 'Pain level during recovery from Pixel Laser', 'For those who''ve had Pixel Laser, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last? I have a low pain tolerance, so I''m trying to prepare mentally.', False, '2025-03-29 20:39:19.432562', '2025-03-31 20:39:19.432562', 488, 4, False, NULL, 27, 168, NULL, NULL, NULL),
(18, 40, 'Visible vs invisible results from Sculptra', 'I''m interested in getting Sculptra but I''m curious about how noticeable the results are to others. Did people comment on your appearance after recovery? Did they know you had work done or just notice you looked better/different?', False, '2025-02-05 20:39:19.858036', '2025-02-27 20:39:19.858036', 143, 4, False, NULL, 11, 67, NULL, NULL, NULL),
(19, 67, 'How to prepare for VenaSeal - Tips and advice', 'I''m scheduled for VenaSeal in 3 weeks. What preparations should I make before the surgery? Any specific supplements to avoid? How did you prepare your home/living space for recovery? I want to make sure I''m fully prepared.', False, '2025-03-21 20:39:20.283135', '2025-04-03 20:39:20.283135', 393, 3, False, NULL, 38, 408, NULL, NULL, NULL),
(20, 21, 'Pain level during recovery from Earfold', 'For those who''ve had Earfold, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last? I have a low pain tolerance, so I''m trying to prepare mentally.', False, '2025-01-25 20:42:08.026072', '2025-02-21 20:42:08.026072', 327, 2, True, NULL, 28, 291, NULL, NULL, NULL),
(21, 125, 'Recovery milestones after Scar Removal', 'For those who''ve had Scar Removal, can you share your recovery timeline and milestones? When could you return to work? When did swelling/bruising subside? When did you feel ''normal'' again? I''m trying to plan my life around recovery.', False, '2025-01-29 20:42:08.554367', '2025-02-06 20:42:08.554367', 328, 0, False, NULL, 31, 88, NULL, NULL, NULL),
(22, 35, 'Natural-looking results after Body-Jet Liposuction', 'I''m interested in getting Body-Jet Liposuction but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-01-27 20:42:08.984911', '2025-02-17 20:42:08.984911', 379, 0, False, NULL, 7, 190, NULL, NULL, NULL),
(23, 86, 'Post-Lipedema Surgery exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Lipedema Surgery, how long did you need to avoid exercise? When were you able to resume light workouts? When could you get back to full intensity? I''m concerned about losing progress.', True, '2025-02-02 20:42:09.427020', '2025-02-05 20:42:09.427020', 152, 3, False, NULL, 7, 127, NULL, NULL, NULL),
(24, 126, 'How to prepare for SlimLipo - Tips and advice', 'I''m scheduled for SlimLipo in 3 weeks. What preparations should I make before the surgery? Any specific supplements to avoid? How did you prepare your home/living space for recovery? I want to make sure I''m fully prepared.', True, '2024-12-06 20:42:09.867359', '2025-01-01 20:42:09.867359', 13, 1, True, NULL, 7, 198, NULL, NULL, NULL),
(25, 118, 'How to prepare for NovaThreads - Tips and advice', 'I''m scheduled for NovaThreads in 3 weeks. What preparations should I make before the surgery? Any specific supplements to avoid? How did you prepare your home/living space for recovery? I want to make sure I''m fully prepared.', False, '2025-04-18 20:42:10.312522', '2025-04-21 20:42:10.312522', 469, 4, False, NULL, 10, 317, NULL, NULL, NULL),
(26, 31, 'Pain level during recovery from Collagen Injection', 'For those who''ve had Collagen Injection, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last? I have a low pain tolerance, so I''m trying to prepare mentally.', False, '2025-04-29 20:42:10.741814', '2025-04-29 20:42:10.741814', 16, 5, True, NULL, 11, 276, NULL, NULL, NULL),
(27, 142, 'Post-Macrolane exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Macrolane, how long did you need to avoid exercise? When were you able to resume light workouts? When could you get back to full intensity? I''m concerned about losing progress.', True, '2025-03-22 20:42:11.170441', '2025-04-11 20:42:11.170441', 178, 2, False, NULL, 11, 479, NULL, NULL, NULL),
(28, 72, 'Recovery time after Jeuveau?', 'I''m scheduled for Jeuveau next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-05-04 20:42:58.184622', '2025-05-11 20:42:58.184622', 179, 1, False, NULL, 11, 223, NULL, NULL, NULL),
(29, 50, 'Scarring after Silikon 1000 - How visible?', 'I''m concerned about scarring after Silikon 1000. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2025-05-11 20:42:58.635002', '2025-05-17 20:42:58.635002', 121, 0, False, NULL, 11, 113, NULL, NULL, NULL),
(30, 72, 'Natural-looking results after Aquamid', 'I''m interested in getting Aquamid but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-02-07 20:42:59.085692', '2025-02-09 20:42:59.085692', 107, 3, False, NULL, 11, 322, NULL, NULL, NULL),
(31, 121, 'Is Silicone Injections worth it? Long-term results', 'I''m considering Silicone Injections but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2024-11-16 20:42:59.539277', '2024-11-16 20:42:59.539277', 148, 2, False, NULL, 11, 240, NULL, NULL, NULL),
(32, 66, 'Post-JeNu exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had JeNu, how long did you need to avoid exercise? When were you able to resume activities?', False, '2024-12-31 20:43:00.000206', '2024-12-31 20:43:00.000206', 115, 0, False, NULL, 41, 434, NULL, NULL, NULL),
(33, 31, 'Natural-looking results after Snap-On Smile', 'I''m interested in getting Snap-On Smile but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-02-15 20:43:00.453387', '2025-02-15 20:43:00.453387', 12, 0, False, NULL, 22, 407, NULL, NULL, NULL),
(34, 111, 'Age considerations for UltraShape Power', 'I''m in my 40s and considering UltraShape Power. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2025-01-06 20:43:00.909441', '2025-01-16 20:43:00.909441', 57, 3, False, NULL, 7, 367, NULL, NULL, NULL),
(35, 31, 'Cost of Breast Lift in India - 2025', 'What is the current cost range for Breast Lift in major Indian cities? I''ve been quoted ₹3,00,000-4,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-04-29 20:43:01.368526', '2025-05-09 20:43:01.368526', 193, 1, False, NULL, 1, 18, NULL, NULL, NULL),
(36, 99, 'Age considerations for Thigh Lift', 'I''m in my 40s and considering Thigh Lift. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2025-04-03 20:43:01.835011', '2025-04-11 20:43:01.835011', 32, 3, False, NULL, 7, 77, NULL, NULL, NULL),
(37, 31, 'Cost of Botox in India - 2025', 'What is the current cost range for Botox in major Indian cities? I''ve been quoted ₹1,50,000-2,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-03-03 20:43:02.294015', '2025-03-12 20:43:02.294015', 159, 2, False, NULL, 11, 14, NULL, NULL, NULL),
(38, 45, 'Natural-looking results after Photodynamic Therapy', 'I''m interested in getting Photodynamic Therapy but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-02-03 20:43:31.369951', '2025-02-09 20:43:31.369951', 37, 3, False, NULL, 27, 193, NULL, NULL, NULL),
(39, 45, 'Cost of Zerona in India - 2025', 'What is the current cost range for Zerona in major Indian cities? I''ve been quoted ₹1,50,000-2,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-02-04 20:43:31.817252', '2025-02-07 20:43:31.817252', 76, 1, False, NULL, 7, 477, NULL, NULL, NULL),
(40, 119, 'Is Breast Lift worth it? Long-term results', 'I''m considering Breast Lift but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2024-12-09 20:43:32.262995', '2024-12-15 20:43:32.262995', 56, 0, False, NULL, 1, 18, NULL, NULL, NULL),
(41, 78, 'Pain level during recovery from Thermage FLX', 'For those who''ve had Thermage FLX, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2025-03-02 20:43:32.709886', '2025-03-03 20:43:32.709886', 33, 1, False, NULL, 26, 270, NULL, NULL, NULL),
(42, 78, 'Best doctors for Jewel Tone Facial in Mumbai', 'I''m looking for recommendations for the best doctors for Jewel Tone Facial in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-05-09 20:43:33.155722', '2025-05-19 20:43:33.155722', 162, 3, False, NULL, 51, 499, NULL, NULL, NULL),
(43, 92, 'Best doctors for Laser Resurfacing in Mumbai', 'I''m looking for recommendations for the best doctors for Laser Resurfacing in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-02-09 20:43:33.600528', '2025-02-15 20:43:33.600528', 59, 0, False, NULL, 27, 62, NULL, NULL, NULL),
(44, 97, 'Post-BodyFX exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had BodyFX, how long did you need to avoid exercise? When were you able to resume activities?', False, '2025-01-11 20:43:34.048468', '2025-01-14 20:43:34.048468', 41, 0, False, NULL, 7, 267, NULL, NULL, NULL),
(45, 99, 'Post-Ultra Femme 360 exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Ultra Femme 360, how long did you need to avoid exercise? When were you able to resume activities?', False, '2024-12-28 20:43:34.493167', '2024-12-29 20:43:34.493167', 56, 1, False, NULL, 40, 402, NULL, NULL, NULL),
(46, 119, 'Scarring after Cheek Augmentation - How visible?', 'I''m concerned about scarring after Cheek Augmentation. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2025-02-01 20:43:34.938386', '2025-02-10 20:43:34.938386', 43, 3, False, NULL, 23, 227, NULL, NULL, NULL),
(47, 97, 'Pain level during recovery from Calf Implant', 'For those who''ve had Calf Implant, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2025-05-04 20:43:35.383581', '2025-05-11 20:43:35.383581', 120, 3, False, NULL, 42, 226, NULL, NULL, NULL),
(48, 48, 'Combining Genioplasty with other procedures', 'I''m planning to get Genioplasty and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-01-14 20:43:47.900386', '2025-01-17 20:43:47.900386', 69, 3, False, NULL, 23, 107, NULL, NULL, NULL),
(49, 39, 'Best doctors for Areola Reduction Surgery in Mumbai', 'I''m looking for recommendations for the best doctors for Areola Reduction Surgery in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2024-12-03 20:43:48.363305', '2024-12-10 20:43:48.363305', 155, 0, False, NULL, 1, 221, NULL, NULL, NULL),
(50, 116, 'Post-Chin Liposuction exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Chin Liposuction, how long did you need to avoid exercise? When were you able to resume activities?', False, '2025-02-12 20:43:48.823863', '2025-02-21 20:43:48.823863', 55, 2, False, NULL, 23, 47, NULL, NULL, NULL),
(51, 48, 'Cost of Genioplasty in India - 2025', 'What is the current cost range for Genioplasty in major Indian cities? I''ve been quoted ₹3,00,000-4,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-05-05 20:43:49.282440', '2025-05-14 20:43:49.282440', 17, 1, False, NULL, 23, 107, NULL, NULL, NULL),
(52, 80, 'Cost of Microblading in India - 2025', 'What is the current cost range for Microblading in major Indian cities? I''ve been quoted ₹50,000-90,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2024-12-05 20:43:49.741533', '2024-12-09 20:43:49.741533', 179, 1, False, NULL, 34, 102, NULL, NULL, NULL),
(53, 56, 'Best doctors for Scalp Micropigmentation in Mumbai', 'I''m looking for recommendations for the best doctors for Scalp Micropigmentation in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-03-09 20:43:50.200335', '2025-03-16 20:43:50.200335', 90, 0, False, NULL, 12, 175, NULL, NULL, NULL),
(54, 77, 'Best doctors for Butt Lift in Mumbai', 'I''m looking for recommendations for the best doctors for Butt Lift in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2024-12-17 20:43:50.659241', '2024-12-17 20:43:50.659241', 140, 2, False, NULL, 3, 128, NULL, NULL, NULL),
(55, 89, 'Combining Teosyal with other procedures', 'I''m planning to get Teosyal and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2024-12-21 20:43:51.120245', '2024-12-22 20:43:51.120245', 86, 2, False, NULL, 11, 247, NULL, NULL, NULL),
(56, 141, 'Is Intensity Peel worth it? Long-term results', 'I''m considering Intensity Peel but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2024-12-14 20:43:51.580391', '2024-12-22 20:43:51.580391', 102, 3, False, NULL, 51, 497, NULL, NULL, NULL),
(57, 109, 'Is Revanesse worth it? Long-term results', 'I''m considering Revanesse but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-02-12 20:43:52.038965', '2025-02-16 20:43:52.038965', 179, 3, False, NULL, 11, 326, NULL, NULL, NULL),
(58, 27, 'Natural-looking results after Microneedling', 'I''m interested in getting Microneedling but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-03-09 20:44:00.663456', '2025-03-15 20:44:00.663456', 49, 2, False, NULL, 27, 90, NULL, NULL, NULL),
(59, 101, 'Combining Low-Level Laser Therapy with other procedures', 'I''m planning to get Low-Level Laser Therapy and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-04-07 20:44:01.120327', '2025-04-16 20:44:01.120327', 41, 1, False, NULL, 12, 456, NULL, NULL, NULL),
(60, 61, 'Combining TriPollar with other procedures', 'I''m planning to get TriPollar and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-03-25 20:44:01.574057', '2025-04-01 20:44:01.574057', 176, 2, False, NULL, 26, 387, NULL, NULL, NULL),
(61, 128, 'Natural-looking results after Fractora RF', 'I''m interested in getting Fractora RF but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-03-26 20:44:02.165168', '2025-04-01 20:44:02.165168', 41, 0, False, NULL, 27, 208, NULL, NULL, NULL),
(62, 112, 'Scarring after Microneedling - How visible?', 'I''m concerned about scarring after Microneedling. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2025-01-05 20:44:02.615324', '2025-01-08 20:44:02.615324', 23, 2, False, NULL, 27, 90, NULL, NULL, NULL),
(63, 66, 'Cost of PicoSure in India - 2025', 'What is the current cost range for PicoSure in major Indian cities? I''ve been quoted ₹1,50,000-2,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-01-08 20:44:03.069298', '2025-01-13 20:44:03.069298', 44, 0, False, NULL, 27, 82, NULL, NULL, NULL),
(64, 15, 'Recovery time after Dental Bridge?', 'I''m scheduled for Dental Bridge next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-04-24 20:44:03.528873', '2025-04-29 20:44:03.528873', 34, 1, False, NULL, 22, 372, NULL, NULL, NULL),
(65, 53, 'Is ThermiTight worth it? Long-term results', 'I''m considering ThermiTight but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-02-21 20:44:03.980252', '2025-02-25 20:44:03.980252', 30, 3, False, NULL, 26, 166, NULL, NULL, NULL),
(66, 27, 'Cost of Fractora RF in India - 2025', 'What is the current cost range for Fractora RF in major Indian cities? I''ve been quoted ₹1,50,000-2,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2024-12-09 20:44:04.430497', '2024-12-17 20:44:04.430497', 73, 3, False, NULL, 27, 208, NULL, NULL, NULL),
(67, 127, 'Natural-looking results after Enzyme Renewal Treatment', 'I''m interested in getting Enzyme Renewal Treatment but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2024-11-28 20:44:04.886334', '2024-12-03 20:44:04.886334', 116, 1, False, NULL, 52, 525, NULL, NULL, NULL),
(68, 63, 'Best doctors for Forma in Mumbai', 'I''m looking for recommendations for the best doctors for Forma in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-04-03 20:44:36.280444', '2025-04-12 20:44:36.280444', 55, 2, False, NULL, 26, 294, NULL, NULL, NULL),
(69, 77, 'Best doctors for Coolaser in Mumbai', 'I''m looking for recommendations for the best doctors for Coolaser in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-05-07 20:44:36.716267', '2025-05-11 20:44:36.716267', 107, 3, False, NULL, 27, 537, NULL, NULL, NULL),
(70, 72, 'Age considerations for Coolaser', 'I''m in my 40s and considering Coolaser. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2024-12-27 20:44:37.150822', '2025-01-06 20:44:37.150822', 8, 3, False, NULL, 27, 537, NULL, NULL, NULL),
(71, 88, 'Is Forma worth it? Long-term results', 'I''m considering Forma but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-04-16 20:44:37.596095', '2025-04-21 20:44:37.596095', 41, 1, False, NULL, 26, 294, NULL, NULL, NULL),
(72, 91, 'Recovery time after Microneedling RF?', 'I''m scheduled for Microneedling RF next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-04-26 20:44:38.038958', '2025-04-30 20:44:38.038958', 196, 1, False, NULL, 27, 184, NULL, NULL, NULL),
(73, 72, 'Is ArteFill worth it? Long-term results', 'I''m considering ArteFill but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-02-25 20:44:38.479939', '2025-03-04 20:44:38.479939', 76, 0, False, NULL, 11, 195, NULL, NULL, NULL),
(74, 77, 'Age considerations for Forma', 'I''m in my 40s and considering Forma. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2025-04-29 20:44:38.916048', '2025-05-05 20:44:38.916048', 48, 3, False, NULL, 26, 294, NULL, NULL, NULL),
(75, 128, 'Is Latisse worth it? Long-term results', 'I''m considering Latisse but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-02-14 20:44:39.361070', '2025-02-14 20:44:39.361070', 172, 3, False, NULL, 34, 141, NULL, NULL, NULL),
(76, 91, 'Cost of Silken Smooth Facial in India - 2025', 'What is the current cost range for Silken Smooth Facial in major Indian cities? I''ve been quoted ₹3,00,000-4,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-02-03 20:44:39.804345', '2025-02-05 20:44:39.804345', 33, 1, False, NULL, 51, 505, NULL, NULL, NULL),
(77, 127, 'Best doctors for Coolaser in Mumbai', 'I''m looking for recommendations for the best doctors for Coolaser in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-05-07 20:44:40.239782', '2025-05-15 20:44:40.239782', 47, 0, False, NULL, 27, 537, NULL, NULL, NULL),
(78, 59, 'Scarring after Vital Rejuvenation - How visible?', 'I''m concerned about scarring after Vital Rejuvenation. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2025-03-26 20:44:52.034418', '2025-04-03 20:44:52.034418', 141, 2, False, NULL, 51, 511, NULL, NULL, NULL),
(79, 90, 'Best doctors for Lash Lift in Mumbai', 'I''m looking for recommendations for the best doctors for Lash Lift in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-01-12 20:44:52.508917', '2025-01-21 20:44:52.508917', 99, 2, False, NULL, 34, 396, NULL, NULL, NULL),
(80, 59, 'Post-Thigh Lift exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Thigh Lift, how long did you need to avoid exercise? When were you able to resume activities?', False, '2025-03-15 20:44:52.975935', '2025-03-24 20:44:52.975935', 86, 3, False, NULL, 7, 77, NULL, NULL, NULL),
(81, 17, 'Combining Lip Lift with other procedures', 'I''m planning to get Lip Lift and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-05-13 20:44:53.446970', '2025-05-20 20:44:53.446970', 158, 2, False, NULL, 21, 45, NULL, NULL, NULL),
(82, 23, 'Pain level during recovery from Mohs Surgery', 'For those who''ve had Mohs Surgery, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2025-01-16 20:44:53.920149', '2025-01-16 20:44:53.920149', 191, 1, False, NULL, 39, 473, NULL, NULL, NULL),
(83, 90, 'Combining Thigh Lift with other procedures', 'I''m planning to get Thigh Lift and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-03-24 20:44:54.462619', '2025-04-01 20:44:54.462619', 151, 0, False, NULL, 7, 77, NULL, NULL, NULL),
(84, 96, 'Is Skin Lightening worth it? Long-term results', 'I''m considering Skin Lightening but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-02-19 20:44:54.933284', '2025-02-25 20:44:54.933284', 98, 3, False, NULL, 27, 224, NULL, NULL, NULL),
(85, 37, 'Cost of Thigh Lift in India - 2025', 'What is the current cost range for Thigh Lift in major Indian cities? I''ve been quoted ₹75,000-1,25,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-01-24 20:44:55.408648', '2025-01-29 20:44:55.408648', 79, 2, False, NULL, 7, 77, NULL, NULL, NULL),
(86, 80, 'Scarring after Labia Puffing - How visible?', 'I''m concerned about scarring after Labia Puffing. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2024-12-04 20:44:55.877436', '2024-12-09 20:44:55.877436', 40, 1, False, NULL, 13, 342, NULL, NULL, NULL),
(87, 142, 'Recovery time after Lip Lift?', 'I''m scheduled for Lip Lift next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2024-12-27 20:44:56.351276', '2025-01-02 20:44:56.351276', 39, 1, False, NULL, 21, 45, NULL, NULL, NULL),
(88, 60, 'Natural-looking results after ArteFill', 'I''m interested in getting ArteFill but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-04-15 20:45:47.981136', '2025-04-16 20:45:47.981136', 28, 1, False, NULL, 11, 195, NULL, NULL, NULL),
(89, 93, 'Post-Gum Graft exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Gum Graft, how long did you need to avoid exercise? When were you able to resume activities?', False, '2024-12-30 20:45:48.455632', '2025-01-01 20:45:48.455632', 46, 3, False, NULL, 46, 295, NULL, NULL, NULL),
(90, 130, 'Post-Penis Enlargement exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Penis Enlargement, how long did you need to avoid exercise? When were you able to resume activities?', False, '2025-03-13 20:45:48.928369', '2025-03-19 20:45:48.928369', 77, 1, False, NULL, 42, 154, NULL, NULL, NULL),
(91, 52, 'Best doctors for Lymphatic Massage in Mumbai', 'I''m looking for recommendations for the best doctors for Lymphatic Massage in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-02-28 20:45:49.399439', '2025-03-04 20:45:49.399439', 169, 2, False, NULL, 7, 304, NULL, NULL, NULL),
(92, 24, 'Cost of Gum Graft in India - 2025', 'What is the current cost range for Gum Graft in major Indian cities? I''ve been quoted ₹1,50,000-2,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-01-16 20:45:49.866391', '2025-01-22 20:45:49.866391', 197, 1, False, NULL, 46, 295, NULL, NULL, NULL),
(93, 128, 'Pain level during recovery from Botox', 'For those who''ve had Botox, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2025-02-01 20:45:50.341688', '2025-02-08 20:45:50.341688', 122, 1, False, NULL, 11, 14, NULL, NULL, NULL),
(94, 101, 'Cost of Thermage in India - 2025', 'What is the current cost range for Thermage in major Indian cities? I''ve been quoted ₹3,00,000-4,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-02-20 20:45:50.823667', '2025-02-27 20:45:50.823667', 46, 3, False, NULL, 26, 136, NULL, NULL, NULL),
(95, 93, 'Best doctors for Breast Lift in Mumbai', 'I''m looking for recommendations for the best doctors for Breast Lift in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-01-24 20:45:51.301029', '2025-01-28 20:45:51.301029', 197, 1, False, NULL, 1, 18, NULL, NULL, NULL),
(96, 88, 'Best doctors for Teosyal in Mumbai', 'I''m looking for recommendations for the best doctors for Teosyal in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-01-17 20:45:51.771235', '2025-01-17 20:45:51.771235', 81, 3, False, NULL, 11, 247, NULL, NULL, NULL),
(97, 52, 'Is Facial Reconstructive Surgery worth it? Long-term results', 'I''m considering Facial Reconstructive Surgery but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-01-17 20:45:52.240435', '2025-01-26 20:45:52.240435', 175, 2, False, NULL, 37, 124, NULL, NULL, NULL),
(98, 121, 'Post-Viveve exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Viveve, how long did you need to avoid exercise? When were you able to resume activities?', False, '2024-11-30 20:46:03.816460', '2024-12-03 20:46:03.816460', 96, 2, False, NULL, 40, 300, NULL, NULL, NULL),
(99, 52, 'Best doctors for QuickLift in Mumbai', 'I''m looking for recommendations for the best doctors for QuickLift in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2024-12-08 20:46:04.290074', '2024-12-16 20:46:04.290074', 146, 1, False, NULL, 10, 478, NULL, NULL, NULL),
(100, 52, 'Recovery time after Thermage?', 'I''m scheduled for Thermage next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-04-03 20:46:04.769136', '2025-04-10 20:46:04.769136', 17, 1, False, NULL, 26, 136, NULL, NULL, NULL);

INSERT INTO "community" ("id", "user_id", "title", "content", "is_anonymous", "created_at", "updated_at", "view_count", "reply_count", "featured", "tags", "category_id", "procedure_id", "parent_id", "photo_url", "video_url") VALUES
(101, 37, 'Scarring after Agnes RF - How visible?', 'I''m concerned about scarring after Agnes RF. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2025-02-01 20:46:05.240990', '2025-02-10 20:46:05.240990', 76, 1, False, NULL, 27, 371, NULL, NULL, NULL),
(102, 50, 'Best doctors for Skin Tightening in Mumbai', 'I''m looking for recommendations for the best doctors for Skin Tightening in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-01-05 20:46:05.711391', '2025-01-11 20:46:05.711391', 20, 2, False, NULL, 26, 149, NULL, NULL, NULL),
(103, 50, 'Recovery time after Lipodissolve?', 'I''m scheduled for Lipodissolve next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-03-09 20:46:06.180334', '2025-03-19 20:46:06.180334', 139, 1, False, NULL, 7, 179, NULL, NULL, NULL),
(104, 32, 'Natural-looking results after Affirm Laser', 'I''m interested in getting Affirm Laser but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-05-06 20:46:06.653858', '2025-05-14 20:46:06.653858', 130, 1, False, NULL, 27, 350, NULL, NULL, NULL),
(105, 108, 'Is Thermage worth it? Long-term results', 'I''m considering Thermage but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-04-12 20:46:07.129062', '2025-04-18 20:46:07.129062', 90, 0, False, NULL, 26, 136, NULL, NULL, NULL),
(106, 43, 'Age considerations for Spironolactone For Acne', 'I''m in my 40s and considering Spironolactone For Acne. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2024-11-20 20:46:07.617818', '2024-11-22 20:46:07.617818', 17, 3, False, NULL, 30, 275, NULL, NULL, NULL),
(107, 43, 'Age considerations for NeoGen Plasma', 'I''m in my 40s and considering NeoGen Plasma. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2025-04-06 20:46:08.088034', '2025-04-08 20:46:08.088034', 51, 1, False, NULL, 27, 332, NULL, NULL, NULL),
(108, 57, 'Pain level during recovery from Liposuction Revision', 'For those who''ve had Liposuction Revision, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2025-02-19 20:46:17.616837', '2025-02-22 20:46:17.616837', 121, 3, False, NULL, 7, 98, NULL, NULL, NULL),
(109, 102, 'Is Liposuction Revision worth it? Long-term results', 'I''m considering Liposuction Revision but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-02-14 20:46:18.055626', '2025-02-20 20:46:18.055626', 111, 2, False, NULL, 7, 98, NULL, NULL, NULL),
(110, 33, 'Combining Youth Essence Facial with other procedures', 'I''m planning to get Youth Essence Facial and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-04-16 20:46:18.482659', '2025-04-17 20:46:18.482659', 112, 2, False, NULL, 51, 515, NULL, NULL, NULL),
(111, 78, 'Natural-looking results after MiraDry', 'I''m interested in getting MiraDry but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-01-18 20:46:18.907717', '2025-01-20 20:46:18.907717', 177, 1, False, NULL, 32, 91, NULL, NULL, NULL),
(112, 134, 'Cost of Glycolic Peel in India - 2025', 'What is the current cost range for Glycolic Peel in major Indian cities? I''ve been quoted ₹50,000-90,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-01-27 20:46:19.337244', '2025-02-06 20:46:19.337244', 65, 3, False, NULL, 27, 297, NULL, NULL, NULL),
(113, 31, 'Age considerations for Liposuction Revision', 'I''m in my 40s and considering Liposuction Revision. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2024-12-26 20:46:19.762818', '2025-01-04 20:46:19.762818', 32, 0, False, NULL, 7, 98, NULL, NULL, NULL),
(114, 27, 'Post-Youth Essence Facial exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Youth Essence Facial, how long did you need to avoid exercise? When were you able to resume activities?', False, '2024-12-02 20:46:20.187335', '2024-12-09 20:46:20.187335', 26, 2, False, NULL, 51, 515, NULL, NULL, NULL),
(115, 28, 'Age considerations for ProFractional Laser', 'I''m in my 40s and considering ProFractional Laser. Is there an ideal age range for this procedure? Has anyone had this procedure at a similar age with good results?', False, '2024-11-15 20:46:20.611529', '2024-11-17 20:46:20.611529', 7, 0, False, NULL, 27, 185, NULL, NULL, NULL),
(116, 103, 'Recovery time after Transgender Laser Hair Removal?', 'I''m scheduled for Transgender Laser Hair Removal next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-05-01 20:46:21.036766', '2025-05-07 20:46:21.036766', 146, 0, False, NULL, 29, 487, NULL, NULL, NULL),
(117, 57, 'Cost of Cataract Surgery in India - 2025', 'What is the current cost range for Cataract Surgery in major Indian cities? I''ve been quoted ₹1,50,000-2,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-03-26 20:46:21.461197', '2025-03-30 20:46:21.461197', 150, 0, False, NULL, 36, 380, NULL, NULL, NULL),
(118, 111, 'Best doctors for Belly Button Surgery in Mumbai', 'I''m looking for recommendations for the best doctors for Belly Button Surgery in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-03-15 20:46:32.677653', '2025-03-18 20:46:32.677653', 82, 3, False, NULL, 7, 266, NULL, NULL, NULL),
(119, 111, 'Post-diVa Vaginal Laser exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had diVa Vaginal Laser, how long did you need to avoid exercise? When were you able to resume activities?', False, '2025-03-08 20:46:33.144136', '2025-03-08 20:46:33.144136', 181, 3, False, NULL, 40, 263, NULL, NULL, NULL),
(120, 47, 'Is Labia Puffing worth it? Long-term results', 'I''m considering Labia Puffing but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-01-24 20:46:33.608044', '2025-02-01 20:46:33.608044', 130, 1, False, NULL, 13, 342, NULL, NULL, NULL),
(121, 111, 'Recovery time after Labia Puffing?', 'I''m scheduled for Labia Puffing next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-02-21 20:46:34.072692', '2025-02-21 20:46:34.072692', 134, 3, False, NULL, 13, 342, NULL, NULL, NULL),
(122, 44, 'Recovery time after Eurosilicone Breast Implants?', 'I''m scheduled for Eurosilicone Breast Implants next month. Can anyone share their recovery experience? How long did it take before you could return to your normal activities? Any tips to speed up recovery?', False, '2025-01-30 20:46:34.542585', '2025-02-09 20:46:34.542585', 138, 3, False, NULL, 1, 447, NULL, NULL, NULL),
(123, 46, 'Post-Zerona exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Zerona, how long did you need to avoid exercise? When were you able to resume activities?', False, '2025-02-18 20:46:35.008584', '2025-02-28 20:46:35.008584', 50, 2, False, NULL, 7, 477, NULL, NULL, NULL),
(124, 35, 'Pain level during recovery from Zerona', 'For those who''ve had Zerona, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2024-12-26 20:46:35.488080', '2024-12-31 20:46:35.488080', 62, 0, False, NULL, 7, 477, NULL, NULL, NULL),
(125, 49, 'Pain level during recovery from diVa Vaginal Laser', 'For those who''ve had diVa Vaginal Laser, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2024-12-22 20:46:35.958968', '2024-12-23 20:46:35.958968', 119, 2, False, NULL, 40, 263, NULL, NULL, NULL),
(126, 112, 'Is Lash Lift worth it? Long-term results', 'I''m considering Lash Lift but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2025-01-27 20:46:36.423790', '2025-01-30 20:46:36.423790', 82, 1, False, NULL, 34, 396, NULL, NULL, NULL),
(127, 111, 'Scarring after Silhouette Soft - How visible?', 'I''m concerned about scarring after Silhouette Soft. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2024-11-25 20:46:36.889275', '2024-12-01 20:46:36.889275', 146, 3, False, NULL, 10, 343, NULL, NULL, NULL),
(128, 21, 'Scarring after Radiance Restore Pro - How visible?', 'I''m concerned about scarring after Radiance Restore Pro. Can those who''ve had this procedure share how visible their scars are now? How long did it take for scars to fade?', False, '2024-12-24 20:46:46.547990', '2025-01-01 20:46:46.547990', 124, 0, False, NULL, 51, 506, NULL, NULL, NULL),
(129, 136, 'Cost of Laser Liposuction in India - 2025', 'What is the current cost range for Laser Liposuction in major Indian cities? I''ve been quoted ₹75,000-1,25,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-01-22 20:46:46.978308', '2025-01-22 20:46:46.978308', 56, 1, False, NULL, 7, 68, NULL, NULL, NULL),
(130, 124, 'Combining Eyebrow Transplant with other procedures', 'I''m planning to get Eyebrow Transplant and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-02-16 20:46:47.407698', '2025-02-16 20:46:47.407698', 195, 3, False, NULL, 34, 122, NULL, NULL, NULL),
(131, 15, 'Is Epionce worth it? Long-term results', 'I''m considering Epionce but wondering if it''s truly worth the investment. For those who had this procedure 2+ years ago, are you still happy with the results? Any regrets?', False, '2024-12-21 20:46:47.838729', '2024-12-26 20:46:47.838729', 195, 0, False, NULL, 41, 382, NULL, NULL, NULL),
(132, 51, 'Post-Umbilical Hernia Repair exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Umbilical Hernia Repair, how long did you need to avoid exercise? When were you able to resume activities?', False, '2024-11-16 20:46:48.264716', '2024-11-25 20:46:48.264716', 196, 2, False, NULL, 33, 310, NULL, NULL, NULL),
(133, 136, 'Pain level during recovery from Cheek Implants', 'For those who''ve had Cheek Implants, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2024-12-19 20:46:48.701068', '2024-12-19 20:46:48.701068', 63, 3, False, NULL, 23, 217, NULL, NULL, NULL),
(134, 109, 'Combining Scar Removal Surgery with other procedures', 'I''m planning to get Scar Removal Surgery and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-05-08 20:46:49.126058', '2025-05-08 20:46:49.126058', 152, 1, False, NULL, 31, 120, NULL, NULL, NULL),
(135, 139, 'Best doctors for Titan Laser in Mumbai', 'I''m looking for recommendations for the best doctors for Titan Laser in Mumbai. Has anyone had a good experience with a particular doctor they can recommend?', False, '2025-03-21 20:46:49.552592', '2025-03-22 20:46:49.552592', 27, 3, False, NULL, 26, 359, NULL, NULL, NULL),
(136, 43, 'Pain level during recovery from Epionce', 'For those who''ve had Epionce, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2025-02-23 20:46:49.986341', '2025-02-26 20:46:49.986341', 37, 2, False, NULL, 41, 382, NULL, NULL, NULL),
(137, 45, 'Cost of Scar Removal Surgery in India - 2025', 'What is the current cost range for Scar Removal Surgery in major Indian cities? I''ve been quoted ₹75,000-1,25,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-01-15 20:46:50.414041', '2025-01-19 20:46:50.414041', 163, 1, False, NULL, 31, 120, NULL, NULL, NULL),
(138, 110, 'Post-African American Rhinoplasty exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had African American Rhinoplasty, how long did you need to avoid exercise? When were you able to resume activities?', False, '2024-12-07 20:46:59.220709', '2024-12-16 20:46:59.220709', 173, 0, False, NULL, 4, 93, NULL, NULL, NULL),
(139, 121, 'Cost of African American Rhinoplasty in India - 2025', 'What is the current cost range for African American Rhinoplasty in major Indian cities? I''ve been quoted ₹1,50,000-2,50,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2024-12-31 20:46:59.655107', '2025-01-10 20:46:59.655107', 198, 1, False, NULL, 4, 93, NULL, NULL, NULL),
(140, 56, 'Cost of Smart Lipo in India - 2025', 'What is the current cost range for Smart Lipo in major Indian cities? I''ve been quoted ₹50,000-90,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-03-26 20:47:00.090919', '2025-03-27 20:47:00.090919', 195, 1, False, NULL, 7, 461, NULL, NULL, NULL),
(141, 42, 'Natural-looking results after Restylane', 'I''m interested in getting Restylane but I''m concerned about having obvious results that look ''done''. Has anyone achieved natural-looking results? What should I discuss with my doctor to ensure subtlety?', False, '2025-04-20 20:47:00.531618', '2025-04-26 20:47:00.531618', 105, 3, False, NULL, 11, 52, NULL, NULL, NULL),
(142, 102, 'Combining ULTRAcel with other procedures', 'I''m planning to get ULTRAcel and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-05-08 20:47:00.964834', '2025-05-17 20:47:00.964834', 76, 2, False, NULL, 26, 439, NULL, NULL, NULL),
(143, 42, 'Pain level during recovery from Lumecca', 'For those who''ve had Lumecca, how would you describe the pain level during recovery? Was the pain manageable with prescribed medication? How long did the most intense pain last?', False, '2025-04-05 20:47:01.406075', '2025-04-10 20:47:01.406075', 185, 0, False, NULL, 27, 355, NULL, NULL, NULL),
(144, 24, 'Combining Restylane with other procedures', 'I''m planning to get Restylane and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-04-02 20:47:01.846701', '2025-04-02 20:47:01.846701', 90, 1, False, NULL, 11, 52, NULL, NULL, NULL),
(145, 106, 'Post-Hyaluronidase exercise restrictions', 'I''m an active person who exercises 5-6 times a week. For those who''ve had Hyaluronidase, how long did you need to avoid exercise? When were you able to resume activities?', False, '2025-03-20 20:47:02.309143', '2025-03-21 20:47:02.309143', 181, 0, False, NULL, 11, 117, NULL, NULL, NULL),
(146, 121, 'Cost of Bio-Revitalization Treatment in India - 2025', 'What is the current cost range for Bio-Revitalization Treatment in major Indian cities? I''ve been quoted ₹75,000-1,25,000 in Mumbai, but I''m wondering if this is reasonable or if I should look at other cities.', False, '2025-05-03 20:47:02.744774', '2025-05-09 20:47:02.744774', 163, 3, False, NULL, 52, 522, NULL, NULL, NULL),
(147, 110, 'Combining Sinus Surgery with other procedures', 'I''m planning to get Sinus Surgery and wondering if it makes sense to combine it with another procedure in the same session. Has anyone done multiple procedures together?', False, '2025-04-10 20:47:03.180969', '2025-04-17 20:47:03.180969', 98, 1, False, NULL, 44, 245, NULL, NULL, NULL);

SELECT setval(pg_get_serial_sequence('community', 'id'), 147, true);


\echo 'Importing community_replies...'
-- SQL for table: community_replies
-- Generated: 2025-05-15 17:44:41
-- Row count: 6

CREATE TABLE IF NOT EXISTS "community_replies" (
    "id" SERIAL PRIMARY KEY,
    "thread_id" INTEGER NOT NULL,
    "user_id" INTEGER NOT NULL,
    "content" TEXT NOT NULL,
    "is_anonymous" BOOLEAN NULL,
    "is_doctor_response" BOOLEAN NULL,
    "created_at" TIMESTAMP NULL,
    "upvotes" INTEGER NULL,
    "parent_reply_id" INTEGER NULL,
    "is_expert_advice" BOOLEAN NULL,
    "is_ai_response" BOOLEAN NULL,
    "photo_url" TEXT NULL,
    "video_url" TEXT NULL
);

INSERT INTO "community_replies" ("id", "thread_id", "user_id", "content", "is_anonymous", "is_doctor_response", "created_at", "upvotes", "parent_reply_id", "is_expert_advice", "is_ai_response", "photo_url", "video_url") VALUES
(1, 1, 14, 'I had rhinoplasty about a year ago and your experience sounds very similar to mine. The psychological aspect was definitely the hardest part! That "middle phase" where you''re still swollen but the initial excitement has worn off was tough.

One thing I wish I''d known was how much the tip of my nose would change over time. It took almost a full year for it to reach its final shape, which was longer than I expected.

Overall though, I''m very happy with my decision. My breathing is so much better now (I had a deviated septum), and I feel more confident in photos.', False, False, '2025-04-24 20:16:38.010897', 5, NULL, False, False, NULL, NULL),
(2, 2, 79, 'Thanks for sharing such a detailed timeline! I''m scheduled for BA next month and this helps me know what to expect.

Question - did you find that you needed help at home during the first week? I live alone and am trying to decide if I should have someone stay with me.', False, False, '2025-05-03 20:21:08.203152', 3, NULL, False, False, NULL, NULL),
(3, 2, 63, 'I had my BA about 3 months ago and your timeline is spot on! The "drop and fluff" is real - mine looked so unnatural at first but now they''ve settled beautifully.

One thing I''d add is that I experienced random sharp pains (like nerve zings) around week 5-8 as everything was healing. My surgeon said this was normal nerve regeneration.

Also, sleeping was difficult for me for almost 6 weeks. I had to sleep on my back with pillows on either side to prevent accidentally rolling onto my side or stomach.', False, False, '2025-04-30 20:21:08.203152', 4, NULL, False, False, NULL, NULL),
(5, 4, 35, 'I had a tummy tuck 2 years after my second C-section, and the surgeon was able to completely remove my C-section scar as part of the procedure. The new tummy tuck scar is lower and thinner than my old C-section scar was.

One thing to note is that if you have any numbness around your C-section scar (which is common), you''ll likely have a larger numb area after the tummy tuck. I have numbness from hip to hip above the new scar, but it doesn''t bother me.

Recovery wasn''t harder because of my previous surgeries. In fact, my surgeon said the internal scar tissue from C-sections can sometimes provide additional support for the muscle repair.

I waited 3 years after my last pregnancy before getting the tummy tuck. My surgeon recommended waiting until I''d been at a stable weight for at least 6 months.', False, False, '2025-05-17 20:22:52.801644', 6, NULL, False, False, NULL, NULL),
(6, 5, 122, 'My bruising after lipo on similar areas lasted about 3 weeks total, but it faded gradually. By the end of the second week, it was yellow rather than purple/blue and much less noticeable.

What helped me: arnica (like you''re doing), gentle walking to increase circulation, and staying super hydrated. My doctor also recommended pineapple for its bromelain content, which may help with swelling.

As for the compression garment, I wore mine 24/7 for 4 weeks, then only during the day for 2 more weeks. Don''t rush taking it off - it really helps with skin retraction and reducing swelling!', True, False, '2025-05-15 20:23:02.544529', 4, NULL, False, False, NULL, NULL),
(7, 6, 84, 'I had upper and lower blepharoplasty at 54, and it was one of the best decisions I''ve made. I''m now 58 and still very happy with the results.

As for how much younger it made me look - people consistently guess my age about 7-10 years younger than I am. But more importantly, I no longer look perpetually tired or sad. Friends and coworkers said I looked "refreshed" rather than "different," which is exactly what I wanted.

Recovery: I had significant bruising that lasted about 2 weeks. I was comfortable running errands with sunglasses after 10 days. At 3 weeks, makeup easily covered any remaining discoloration.

I did experience dry eyes for about 3 months, but using preservative-free eye drops helped tremendously. This resolved completely.

My advice: Find a surgeon who specializes in eyes specifically (oculoplastic surgeon or facial plastic surgeon with lots of eye experience), and be very clear about wanting natural results.', False, False, '2025-05-08 20:23:12.369693', 9, NULL, False, False, NULL, NULL);

SELECT setval(pg_get_serial_sequence('community_replies', 'id'), 7, true);


\echo 'Importing community_tagging...'
-- SQL for table: community_tagging
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "community_tagging" (
    "id" SERIAL PRIMARY KEY,
    "community_id" INTEGER NOT NULL,
    "category_id" INTEGER NULL,
    "procedure_id" INTEGER NULL,
    "confidence_score" DOUBLE PRECISION NULL,
    "user_confirmed" BOOLEAN NULL,
    "created_at" TIMESTAMP NULL
);


\echo 'Importing community_moderation...'
-- SQL for table: community_moderation
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "community_moderation" (
    "id" SERIAL PRIMARY KEY,
    "community_id" INTEGER NULL,
    "reply_id" INTEGER NULL,
    "moderator_id" INTEGER NOT NULL,
    "action" TEXT NOT NULL,
    "reason" TEXT NULL,
    "created_at" TIMESTAMP NULL
);


\echo 'Importing face_scan_analyses...'
-- SQL for table: face_scan_analyses
-- Generated: 2025-05-15 17:44:41
-- Row count: 1

CREATE TABLE IF NOT EXISTS "face_scan_analyses" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NULL,
    "image_path" TEXT NOT NULL,
    "analysis_data" JSON NOT NULL,
    "created_at" TIMESTAMP NULL,
    "is_anonymous" BOOLEAN NULL
);

INSERT INTO "face_scan_analyses" ("id", "user_id", "image_path", "analysis_data", "created_at", "is_anonymous") VALUES
(1, NULL, 'static/uploads/face_scans/3df8da95804b413c825dd68ca7e28927_238b9f222b8a43c519adf955c6610bcc.jpg', '{''timestamp'': ''2025-05-14T13:34:56.719443'', ''analysis'': "**Cosmetic and Plastic Surgery Consultation**\n\nThis consultation is based on a single image and does not constitute a formal medical evaluation.  A thorough in-person examination is necessary for a definitive diagnosis and personalized treatment plan.\n\n\n**1. Facial Structure and Proportions:**\n\n* **Observation:** The patient appears to have a naturally oval face shape with generally good facial symmetry.  The proportions of the facial thirds appear balanced. The profile shows a slightly recessed chin.\n\n* **Treatment Options:**\n    * **Surgical:** Chin augmentation (e.g., chin implant) to enhance chin projection and improve profile harmony.\n    * **Non-surgical:** Dermal fillers injected into the chin to add volume and improve projection.\n\n* **Expected Outcomes:**  Chin augmentation can create a more balanced and defined jawline, enhancing facial harmony.  Results are typically long-lasting with implants, and temporary with fillers (requiring periodic touch-ups).\n\n* **Key Considerations:**  Surgical options involve incisions and recovery time (swelling, bruising). Filler injections have minimal downtime but require repeat treatments for long-term effects.\n\n\n\n**2. Skin Quality and Texture:**\n\n* **Observation:** The image shows relatively clear skin with a healthy complexion. There are no visible signs of significant aging, scarring, or hyperpigmentation.  There''s a slight suggestion of potential mild under-eye darkness, which could be due to several factors.\n\n* **Treatment Options:**\n    * **Non-surgical (for potential under-eye darkness):**  Topical treatments (e.g., retinoids, vitamin C serums), chemical peels, microdermabrasion, and/or professional strength concealer for improved coverage.  If darkness is related to underlying dark circles, fillers can be considered but are generally only used in more mature patients.\n\n\n* **Expected Outcomes:**  Topical treatments can improve skin texture and tone over time. Microdermabrasion can provide immediate improvement in texture. Concealer may instantly hide this problem.\n\n\n* **Key Considerations:** Topical treatments may take several weeks or months to show noticeable results and may cause slight irritation initially.  Chemical peels may result in temporary peeling and redness. Fillers for under-eye darkness may cause bruising and carry a higher risk of complications compared to other areas.\n\n\n**3. Specific Feature Analysis:**\n\n* **Eyes:**  The eyes appear relatively symmetrical in shape and size.  There is a subtle suggestion of mild under-eye hollowness or darkness which could be masked by makeup or addressed with topical skin care treatments. \n\n* **Nose:** The nose appears proportionate to other facial features and aesthetically pleasing. No visible asymmetries are observed in this view.\n\n* **Lips:**  The lips appear naturally full and well-proportioned.  \n\n* **Cheeks:** Cheek volume seems appropriate for the overall facial structure.\n\n* **Jawline:**  The jawline is moderately defined. Chin augmentation (as mentioned above) could slightly improve definition.\n\n* **Chin:**  A slightly recessed chin is noted, as discussed above.\n\n* **Forehead:** The forehead appears smooth and without significant wrinkles or asymmetry.\n\n\n**Recommendations Summary:**\n\nBased on the limited information provided, the most prominent area for potential cosmetic improvement is the chin projection.  Both surgical chin augmentation and non-surgical dermal filler injections are viable options, depending on the patient’s preferences and risk tolerance.  Addressing any under-eye concerns could involve topical skincare or makeup application.\n\n**Disclaimer:** This analysis is for educational purposes only and should not be interpreted as a substitute for a thorough in-person consultation with a qualified medical professional.  A comprehensive medical history, physical examination, and potentially additional diagnostic tests are required before any treatment recommendations can be made.\n", ''image_path'': ''static/uploads/face_scans/3df8da95804b413c825dd68ca7e28927_238b9f222b8a43c519adf955c6610bcc.jpg'', ''procedures'': [{''name'': ''Chin Augmentation'', ''context'': ''Based on the limited information provided, the most prominent area for potential cosmetic improvement is the chin projection.  Both surgical chin augmentation and non-surgical dermal filler injections are viable options, depending on the patient’s preferences and risk tolerance.  Addressing any under-eye concerns could involve topical skincare or makeup application.'', ''relevance_score'': 0.7}], ''treatments'': [{''name'': ''Dermal Fillers'', ''context'': ''Based on the limited information provided, the most prominent area for potential cosmetic improvement is the chin projection.  Both surgical chin augmentation and non-surgical dermal filler injections are viable options, depending on the patient’s preferences and risk tolerance.  Addressing any under-eye concerns could involve topical skincare or makeup application.'', ''relevance_score'': 0.6}, {''name'': ''Chemical Peel'', ''context'': ''* **Treatment Options:**\n    * **Non-surgical (for potential under-eye darkness):**  Topical treatments (e.g., retinoids, vitamin C serums), chemical peels, microdermabrasion, and/or professional strength concealer for improved coverage.  If darkness is related to underlying dark circles, fillers can be considered but are generally only used in more mature patients.'', ''relevance_score'': 0.6}, {''name'': ''Microdermabrasion'', ''context'': ''* **Treatment Options:**\n    * **Non-surgical (for potential under-eye darkness):**  Topical treatments (e.g., retinoids, vitamin C serums), chemical peels, microdermabrasion, and/or professional strength concealer for improved coverage.  If darkness is related to underlying dark circles, fillers can be considered but are generally only used in more mature patients.'', ''relevance_score'': 0.6}, {''name'': ''Vitamin C Treatment'', ''context'': ''* **Treatment Options:**\n    * **Non-surgical (for potential under-eye darkness):**  Topical treatments (e.g., retinoids, vitamin C serums), chemical peels, microdermabrasion, and/or professional strength concealer for improved coverage.  If darkness is related to underlying dark circles, fillers can be considered but are generally only used in more mature patients.'', ''relevance_score'': 0.6}]}', '2025-05-14 13:34:48.730488', False);

SELECT setval(pg_get_serial_sequence('face_scan_analyses', 'id'), 1, true);


\echo 'Importing face_scan_recommendations...'
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


\echo 'Importing education_modules...'
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


\echo 'Importing favorites...'
-- SQL for table: favorites
-- Generated: 2025-05-15 17:44:41
-- Row count: 0

CREATE TABLE IF NOT EXISTS "favorites" (
    "id" SERIAL PRIMARY KEY,
    "user_id" INTEGER NOT NULL,
    "procedure_id" INTEGER NULL,
    "doctor_id" INTEGER NULL,
    "created_at" TIMESTAMP NULL
);


\echo 'Importing appointments...'
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


\echo 'Importing doctor_availability...'
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


\echo 'Importing doctor_photos...'
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


