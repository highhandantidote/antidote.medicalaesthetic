-- Add test body parts
INSERT INTO body_parts (name, description)
VALUES 
    ('face', 'Procedures related to facial features and appearance'),
    ('head', 'Procedures related to the head, scalp, and hair'),
    ('body', 'Procedures for body contouring and enhancement'),
    ('skin', 'Procedures targeting skin conditions and appearance')
ON CONFLICT (name) DO NOTHING;

-- Add test users with correct field names
INSERT INTO users (
    username, email, password_hash, name, phone_number, role, role_type, 
    is_verified, created_at
)
VALUES 
    (
        'testuser', 'testuser@example.com', 
        'pbkdf2:sha256:600000$WMpZcUYA1x0Uiwz2$ceed938f70e372b63a86646b95e24c17ae9e4bad2cddb9b9f84f3dd8f3de9ea7', 
        'Test User', '9876543210', 'user', 'regular', 
        true, NOW()
    ),
    (
        'testdoctor', 'testdoctor@example.com', 
        'pbkdf2:sha256:600000$9e2QkSvQJUhGl723$ae232c4ebee147aa4d1be5fe1c14da29e07fe7dca26d43643e29f48746260f7d', 
        'Doctor Test', '9876543211', 'doctor', 'medical', 
        true, NOW()
    ),
    (
        'testadmin', 'testadmin@example.com', 
        'pbkdf2:sha256:600000$nY8sPBxVfnMRt9fz$aa9f08dc3fb19c104b1ba87b1bb8ce48e1fe585e9731e9dbe1c6f97adecfa31e', 
        'Admin User', '9876543212', 'admin', 'administrator', 
        true, NOW()
    )
ON CONFLICT (username) DO NOTHING;

-- Add doctor profile for the doctor user
INSERT INTO doctors (
    user_id, name, specialty, qualification, experience, 
    consultation_fee, created_at, city
)
SELECT 
    u.id, 
    'Dr. ' || u.name, 
    'Plastic Surgeon',
    'MBBS, MS, MCh (Plastic Surgery)',
    12,
    1500,
    NOW(),
    'Mumbai'
FROM users u
WHERE u.role = 'doctor' AND u.username = 'testdoctor'
ON CONFLICT DO NOTHING;

-- Get ID for body parts
DO $$
DECLARE
    face_id INTEGER;
    head_id INTEGER;
    body_id INTEGER;
    skin_id INTEGER;
BEGIN
    SELECT id INTO face_id FROM body_parts WHERE name = 'face';
    SELECT id INTO head_id FROM body_parts WHERE name = 'head';
    SELECT id INTO body_id FROM body_parts WHERE name = 'body';
    SELECT id INTO skin_id FROM body_parts WHERE name = 'skin';

    -- Add categories
    INSERT INTO categories (name, body_part_id, description, created_at)
    VALUES 
        ('rhinoplasty', face_id, 'Nose reshaping procedures', NOW()),
        ('facelift', face_id, 'Facial rejuvenation procedures', NOW()),
        ('hair_transplant', head_id, 'Hair restoration procedures', NOW()),
        ('liposuction', body_id, 'Fat removal procedures', NOW()),
        ('scar_revision', skin_id, 'Scar treatment procedures', NOW())
    ON CONFLICT (name) DO NOTHING;
END $$;

-- Get category IDs
DO $$
DECLARE
    rhinoplasty_id INTEGER;
    facelift_id INTEGER;
    hair_transplant_id INTEGER;
    liposuction_id INTEGER;
    scar_revision_id INTEGER;
BEGIN
    SELECT id INTO rhinoplasty_id FROM categories WHERE name = 'rhinoplasty';
    SELECT id INTO facelift_id FROM categories WHERE name = 'facelift';
    SELECT id INTO hair_transplant_id FROM categories WHERE name = 'hair_transplant';
    SELECT id INTO liposuction_id FROM categories WHERE name = 'liposuction';
    SELECT id INTO scar_revision_id FROM categories WHERE name = 'scar_revision';

    -- Add test procedures
    INSERT INTO procedures (
        procedure_name, short_description, overview, procedure_details, 
        ideal_candidates, recovery_process, min_cost, max_cost, body_part, 
        category_id, created_at, risks, procedure_types, recovery_time
    )
    VALUES 
        (
            'Rhinoplasty', 
            'Nose reshaping surgery to improve appearance and function', 
            'Rhinoplasty is a surgical procedure that changes the shape of the nose. The motivation for rhinoplasty may be to change the appearance of the nose, improve breathing or both.',
            'During rhinoplasty, the surgeon makes incisions to access the bones and cartilage that support the nose. Depending on the desired result, some bone and cartilage may be removed, or tissue may be added. After the surgeon has rearranged and reshaped the bone and cartilage, the skin and tissue is redraped over the structure of the nose.',
            'People with facial growth completion, generally over 16 years old. You should be physically healthy and have realistic goals for improvement of your appearance.',
            'Most patients can return to work or school in 1-2 weeks. Strenuous activity should be avoided for 3-6 weeks. Final results may take up to a year as subtle swelling resolves.',
            80000, 
            150000, 
            'Nose',
            rhinoplasty_id,
            NOW(),
            'Bleeding, infection, adverse reaction to anesthesia, temporary or permanent numbness, difficulty breathing, unsatisfactory results requiring revision surgery.',
            'Surgical, Non-Surgical',
            '2-3 weeks'
        ),
        (
            'Hair Transplant (FUE)', 
            'Modern follicular unit extraction technique for natural-looking hair restoration',
            'Follicular Unit Extraction (FUE) is a minimally invasive hair transplantation technique that involves extracting individual hair follicles from the donor part of the body and moving them to a bald or balding part.',
            'In FUE hair transplant, individual follicular units containing 1-4 hairs are removed under local anesthesia. These units are then transplanted to the balding areas of the scalp. The procedure is performed using a specialized punch device.',
            'Men and women with androgenic alopecia (pattern baldness), thinning hair, or those who want to restore receding hairlines.',
            'Recovery is relatively quick with minimal discomfort. Most patients can return to work within 2-3 days. The transplanted hair will shed within 2-3 weeks, and new growth usually begins in 3-4 months.',
            100000, 
            300000, 
            'Scalp',
            hair_transplant_id,
            NOW(),
            'Infection, bleeding, scarring, unnatural-looking hair patterns, poor hair growth.',
            'Surgical',
            '1 week'
        ),
        (
            'Facelift (Rhytidectomy)', 
            'Surgical procedure to reduce sagging and wrinkles for a more youthful appearance',
            'A facelift, or rhytidectomy, is a surgical procedure that improves visible signs of aging in the face and neck. It addresses sagging facial skin, deep creases, and lost muscle tone.',
            'During a facelift, the surgeon makes incisions around the hairline and ears, then lifts and tightens the underlying facial muscles and tissues. Excess skin is removed, and the remaining skin is repositioned over the newly tightened facial tissues.',
            'Adults with facial skin laxity, deep lines, and wrinkles who are generally healthy and non-smokers.',
            'Recovery typically takes 2-3 weeks. Bruising and swelling are common in the first week. Most patients can resume normal activities after 2 weeks, though final results may take several months as swelling resolves.',
            150000, 
            350000, 
            'Face',
            facelift_id,
            NOW(),
            'Scarring, nerve injury, hair loss around incisions, skin necrosis, asymmetry.',
            'Surgical',
            '2-3 weeks'
        ),
        (
            'Liposuction', 
            'Surgical fat removal procedure for body contouring',
            'Liposuction is a cosmetic procedure that removes fat deposits using suction. It is not a weight-loss method but rather a body contouring technique.',
            'During liposuction, small incisions are made in the target area. A thin tube called a cannula is inserted through these incisions and connected to a vacuum device, which suctions out the fat.',
            'Adults within 30% of their ideal weight with firm, elastic skin and good muscle tone. Best for those with localized fat deposits that don''t respond to diet and exercise.',
            'Recovery varies depending on the extent of the procedure. Expect to wear compression garments for several weeks. Most patients return to work within a week, but should avoid strenuous activity for 2-4 weeks.',
            60000, 
            200000, 
            'Body',
            liposuction_id,
            NOW(),
            'Contour irregularities, fluid accumulation, infection, internal puncture, fat embolism, thermal burns.',
            'Surgical',
            '1-2 weeks'
        ),
        (
            'Scar Revision', 
            'Procedures to improve the appearance of scars',
            'Scar revision is a procedure to minimize a scar so that it is less conspicuous and blends in with the surrounding skin tone and texture.',
            'Techniques include surgical excision, laser treatments, dermabrasion, microneedling, and injectable treatments. The method chosen depends on the scar''s size, type, location, and individual factors.',
            'Anyone with a scar that is cosmetically concerning. Best results in non-smokers with good general health and realistic expectations.',
            'Recovery varies depending on the technique used. Surgical revision may require 1-2 weeks, while less invasive techniques may have minimal downtime.',
            20000, 
            100000, 
            'Skin',
            scar_revision_id,
            NOW(),
            'Infection, bleeding, scarring (possibility of worse scarring), skin discoloration, asymmetry.',
            'Surgical, Non-Surgical',
            'Varies'
        )
    ON CONFLICT (procedure_name) DO NOTHING;
END $$;

-- Add community threads (using the threads table instead of community)
INSERT INTO threads (title, content, user_id, is_anonymous, view_count, created_at, tags)
SELECT 
    'My rhinoplasty experience - so happy with the results!',
    'I had a rhinoplasty procedure done last month and I''m absolutely thrilled with the results. My nose looks so natural and it''s made a huge difference to my confidence. I was nervous about the recovery but it was much easier than I expected. Happy to answer any questions!',
    u.id,
    false,
    54,
    NOW() - INTERVAL '6 days',
    ARRAY['rhinoplasty', 'success story', 'recovery']
FROM users u
WHERE u.role = 'user' AND u.username = 'testuser'
UNION ALL
SELECT 
    'Questions about hair transplant procedure',
    'I''m considering a hair transplant but I have a few questions:

1. How painful is the procedure?
2. How long before I see results?
3. How natural will it look?
4. What''s the maintenance like afterward?

If anyone has experience with this, I''d appreciate your insights!',
    u.id,
    true,
    38,
    NOW() - INTERVAL '5 days',
    ARRAY['hair transplant', 'questions', 'advice needed']
FROM users u
WHERE u.role = 'user' AND u.username = 'testuser'
UNION ALL
SELECT 
    'Recommendations for facial scar treatment',
    'I have a scar on my cheek from an accident when I was younger. It''s about 3cm long and quite noticeable. I''m looking into treatments to reduce its appearance. Has anyone had experience with scar revision surgery or alternative treatments like laser therapy? Any recommendations on doctors or clinics in Mumbai that specialize in this?',
    u.id,
    false,
    42,
    NOW() - INTERVAL '4 days',
    ARRAY['scar revision', 'recommendations', 'treatment options']
FROM users u
WHERE u.role = 'user' AND u.username = 'testuser';

-- Associate doctor with procedures
INSERT INTO doctor_procedures (doctor_id, procedure_id)
SELECT 
    d.id, p.id
FROM 
    doctors d, procedures p
WHERE d.name LIKE 'Dr. Doctor%'
LIMIT 5;

-- Output the test account credentials for reference
DO $$
BEGIN
    RAISE NOTICE '
===== TEST ACCOUNT CREDENTIALS =====
Regular user:
  Email: testuser@example.com
  Password: userpass123

Doctor:
  Email: testdoctor@example.com
  Password: doctorpass123

Admin:
  Email: testadmin@example.com
  Password: adminpass123
';
END $$;