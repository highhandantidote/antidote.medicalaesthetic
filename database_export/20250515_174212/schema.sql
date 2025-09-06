-- Database Schema Export
-- Generated: 2025-05-15 17:42:14


-- Table: appointments
CREATE TABLE IF NOT EXISTS "appointments" (
    "id" integer NOT NULL DEFAULT nextval('appointments_id_seq'::regclass),
    "user_id" integer NOT NULL,
    "doctor_id" integer NOT NULL,
    "procedure_name" text NOT NULL,
    "appointment_date" timestamp without time zone NOT NULL,
    "appointment_time" text NOT NULL,
    "status" text NULL,
    "notes" text NULL,
    "created_at" timestamp without time zone NULL,
    "updated_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: banner_slides
CREATE TABLE IF NOT EXISTS "banner_slides" (
    "id" integer NOT NULL DEFAULT nextval('banner_slides_id_seq'::regclass),
    "banner_id" integer NOT NULL,
    "title" character varying(200) NOT NULL,
    "subtitle" text NULL,
    "image_url" character varying(500) NOT NULL,
    "redirect_url" character varying(500) NOT NULL,
    "display_order" integer NULL,
    "is_active" boolean NULL,
    "created_at" timestamp without time zone NULL,
    "updated_at" timestamp without time zone NULL,
    "click_count" integer NULL,
    "impression_count" integer NULL,
    PRIMARY KEY ("id")
);


-- Table: banners
CREATE TABLE IF NOT EXISTS "banners" (
    "id" integer NOT NULL DEFAULT nextval('banners_id_seq'::regclass),
    "name" character varying(100) NOT NULL,
    "position" character varying(50) NOT NULL,
    "is_active" boolean NULL,
    "created_at" timestamp without time zone NULL,
    "updated_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: body_parts
CREATE TABLE IF NOT EXISTS "body_parts" (
    "id" integer NOT NULL DEFAULT nextval('body_parts_id_seq'::regclass),
    "name" text NOT NULL,
    "description" text NULL,
    "icon_url" text NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: categories
CREATE TABLE IF NOT EXISTS "categories" (
    "id" integer NOT NULL DEFAULT nextval('categories_id_seq'::regclass),
    "name" text NOT NULL,
    "body_part_id" integer NOT NULL,
    "description" text NULL,
    "popularity_score" integer NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: community
CREATE TABLE IF NOT EXISTS "community" (
    "id" integer NOT NULL DEFAULT nextval('community_id_seq'::regclass),
    "user_id" integer NOT NULL,
    "title" text NOT NULL,
    "content" text NOT NULL,
    "is_anonymous" boolean NULL,
    "created_at" timestamp without time zone NULL,
    "updated_at" timestamp without time zone NULL,
    "view_count" integer NULL,
    "reply_count" integer NULL,
    "featured" boolean NULL,
    "tags" ARRAY NULL,
    "category_id" integer NULL,
    "procedure_id" integer NULL,
    "parent_id" integer NULL,
    "photo_url" text NULL,
    "video_url" text NULL,
    PRIMARY KEY ("id")
);


-- Table: community_moderation
CREATE TABLE IF NOT EXISTS "community_moderation" (
    "id" integer NOT NULL DEFAULT nextval('community_moderation_id_seq'::regclass),
    "community_id" integer NULL,
    "reply_id" integer NULL,
    "moderator_id" integer NOT NULL,
    "action" text NOT NULL,
    "reason" text NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: community_replies
CREATE TABLE IF NOT EXISTS "community_replies" (
    "id" integer NOT NULL DEFAULT nextval('community_replies_id_seq'::regclass),
    "thread_id" integer NOT NULL,
    "user_id" integer NOT NULL,
    "content" text NOT NULL,
    "is_anonymous" boolean NULL,
    "is_doctor_response" boolean NULL,
    "created_at" timestamp without time zone NULL,
    "upvotes" integer NULL,
    "parent_reply_id" integer NULL,
    "is_expert_advice" boolean NULL,
    "is_ai_response" boolean NULL,
    "photo_url" text NULL,
    "video_url" text NULL,
    PRIMARY KEY ("id")
);


-- Table: community_tagging
CREATE TABLE IF NOT EXISTS "community_tagging" (
    "id" integer NOT NULL DEFAULT nextval('community_tagging_id_seq'::regclass),
    "community_id" integer NOT NULL,
    "category_id" integer NULL,
    "procedure_id" integer NULL,
    "confidence_score" double precision NULL,
    "user_confirmed" boolean NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: doctor_availability
CREATE TABLE IF NOT EXISTS "doctor_availability" (
    "id" integer NOT NULL DEFAULT nextval('doctor_availability_id_seq'::regclass),
    "doctor_id" integer NOT NULL,
    "day_of_week" character varying(10) NULL,
    "start_time" timestamp without time zone NULL,
    "end_time" timestamp without time zone NULL,
    "date" timestamp without time zone NULL,
    "slots" json NULL,
    "booked_slots" json NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: doctor_categories
CREATE TABLE IF NOT EXISTS "doctor_categories" (
    "id" integer NOT NULL DEFAULT nextval('doctor_categories_id_seq'::regclass),
    "doctor_id" integer NOT NULL,
    "category_id" integer NOT NULL,
    "created_at" timestamp without time zone NULL,
    "is_verified" boolean NULL,
    PRIMARY KEY ("id")
);


-- Table: doctor_photos
CREATE TABLE IF NOT EXISTS "doctor_photos" (
    "id" integer NOT NULL DEFAULT nextval('doctor_photos_id_seq'::regclass),
    "doctor_id" integer NOT NULL,
    "photo_url" text NULL,
    "description" text NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: doctor_procedures
CREATE TABLE IF NOT EXISTS "doctor_procedures" (
    "id" integer NOT NULL DEFAULT nextval('doctor_procedures_id_seq'::regclass),
    "doctor_id" integer NOT NULL,
    "procedure_id" integer NOT NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);


-- Table: doctors
CREATE TABLE IF NOT EXISTS "doctors" (
    "id" integer NOT NULL DEFAULT nextval('doctors_id_seq'::regclass),
    "user_id" integer NOT NULL,
    "name" text NOT NULL,
    "specialty" text NOT NULL,
    "experience" integer NOT NULL,
    "city" text NOT NULL,
    "state" text NULL,
    "hospital" text NULL,
    "consultation_fee" integer NULL,
    "is_verified" boolean NULL,
    "rating" double precision NULL,
    "review_count" integer NULL,
    "created_at" timestamp without time zone NULL,
    "bio" text NULL,
    "certifications" json NULL,
    "video_url" text NULL,
    "success_stories" integer NULL,
    "education" json NULL,
    "medical_license_number" text NULL,
    "qualification" text NULL,
    "practice_location" text NULL,
    "verification_status" text NULL,
    "verification_date" timestamp without time zone NULL,
    "verification_notes" text NULL,
    "credentials_url" text NULL,
    "aadhaar_number" text NULL,
    "profile_image" text NULL,
    "image_url" text NULL,
    PRIMARY KEY ("id")
);


-- Table: education_modules
CREATE TABLE IF NOT EXISTS "education_modules" (
    "id" integer NOT NULL DEFAULT nextval('education_modules_id_seq'::regclass),
    "title" text NOT NULL,
    "description" text NOT NULL,
    "content" text NOT NULL,
    "category_id" integer NULL,
    "procedure_id" integer NULL,
    "level" integer NULL,
    "points" integer NULL,
    "estimated_minutes" integer NULL,
    "created_at" timestamp without time zone NULL,
    "updated_at" timestamp without time zone NULL,
    "is_active" boolean NULL,
    PRIMARY KEY ("id")
);


-- Table: face_scan_analyses
CREATE TABLE IF NOT EXISTS "face_scan_analyses" (
    "id" integer NOT NULL DEFAULT nextval('face_scan_analyses_id_seq'::regclass),
    "user_id" integer NULL,
    "image_path" text NOT NULL,
    "analysis_data" json NOT NULL,
    "created_at" timestamp without time zone NULL,
    "is_anonymous" boolean NULL,
    PRIMARY KEY ("id")
);


-- Table: face_scan_recommendations
CREATE TABLE IF NOT EXISTS "face_scan_recommendations" (
    "id" integer NOT NULL DEFAULT nextval('face_scan_recommendations_id_seq'::regclass),
    "analysis_id" integer NOT NULL,
    "procedure_id" integer NULL,
    "relevance_score" double precision NOT NULL,
    "area_of_concern" text NULL,
    "recommendation_reason" text NULL,
    "recommendation_type" text NULL,
    "created_at" timestamp without time zone NULL,
    PRIMARY KEY ("id")
);

