-- Clear existing data
DELETE FROM procedures;
DELETE FROM categories;
DELETE FROM body_parts;

-- Import a few body parts
INSERT INTO body_parts (name, created_at) VALUES 
('Face', NOW()),
('Nose', NOW()),
('Breasts', NOW()),
('Body', NOW()),
('Eyes', NOW()),
('Lips', NOW()),
('Stomach', NOW()),
('Hair', NOW()),
('Neck', NOW()),
('Butt', NOW());

-- Get the body part IDs
SELECT id, name FROM body_parts;

-- Import categories (Run after noting the body part IDs from above query)
-- Replace the body_part_id values with the actual IDs from your database
INSERT INTO categories (name, body_part_id, created_at, description) VALUES 
('Face_And_Neck_Lifts', 1, NOW(), 'Face and neck lift procedures'),
('Fillers_And_Other_Injectables', 1, NOW(), 'Filler and injectable procedures for the face'),
('Rhinoplasty_And_Nose_Shaping', 2, NOW(), 'Nose reshaping procedures'),
('Breast_Surgery', 3, NOW(), 'Breast enhancement and reduction procedures'),
('Body_Contouring', 4, NOW(), 'Body contouring and shaping procedures'),
('Eyelid_Enhancement', 5, NOW(), 'Eyelid enhancement procedures'),
('Lip_Enhancement', 6, NOW(), 'Lip enhancement procedures'),
('Abdominoplasty', 7, NOW(), 'Abdominal procedures'),
('Hair_Restoration', 8, NOW(), 'Hair restoration procedures'),
('Face_And_Neck_Lifts', 9, NOW(), 'Neck lift procedures'),
('Hip_and_Butt_Enhancement', 10, NOW(), 'Butt enhancement procedures');

-- Get the category IDs
SELECT id, name, body_part_id FROM categories;

-- Import a few sample procedures (Run after noting the category IDs from above query)
-- Replace the category_id values with the actual IDs from your database
INSERT INTO procedures (
    procedure_name, 
    alternative_names, 
    short_description, 
    overview, 
    procedure_details, 
    ideal_candidates, 
    recovery_time, 
    procedure_duration, 
    hospital_stay_required, 
    min_cost, 
    max_cost, 
    category_id, 
    body_part, 
    created_at, 
    updated_at
) VALUES 
(
    'Rhinoplasty',
    'Nose Job, Nasal Reshaping',
    'Reshapes the nose for aesthetic or functional reasons.',
    'Rhinoplasty modifies nasal shape for cosmetic reasons or to correct breathing issues or trauma deformities.',
    'Open or closed technique; cartilage reshaping, bone trimming or grafting may be done.',
    'Individuals with nasal asymmetry, humps, or breathing problems.',
    '1–2 weeks',
    '1–3 hours',
    'No',
    120000,
    250000,
    3, -- Replace with actual category ID for Rhinoplasty_And_Nose_Shaping
    'Nose',
    NOW(),
    NOW()
),
(
    'Breast Augmentation',
    'Boob Job, Breast Enhancement Surgery',
    'Enhances breast size using implants or fat transfer.',
    'Breast augmentation involves increasing the size or enhancing the shape of breasts using implants or fat grafting.',
    'Performed under general anesthesia; involves placing silicone or saline implants or injecting fat tissue into breasts.',
    'Women with small or asymmetrical breasts, post-pregnancy changes.',
    '1–2 weeks',
    '1–2 hours',
    'No',
    150000,
    350000,
    4, -- Replace with actual category ID for Breast_Surgery
    'Breasts',
    NOW(),
    NOW()
),
(
    'Facelift',
    'Rhytidectomy',
    'Tightens facial skin and muscles for a youthful look.',
    'A facelift reduces signs of aging by tightening the skin, removing excess fat, and smoothing wrinkles.',
    'Involves incisions around the ear, removal of excess skin, and repositioning underlying muscles.',
    'Individuals with sagging skin, deep wrinkles, and jowls.',
    '2–4 weeks',
    '3–5 hours',
    'Yes',
    250000,
    550000,
    1, -- Replace with actual category ID for Face_And_Neck_Lifts
    'Face',
    NOW(),
    NOW()
),
(
    'Liposuction',
    'Fat Removal Surgery, Liposculpture',
    'Removes unwanted fat from specific areas of the body.',
    'Liposuction targets stubborn fat deposits and sculpts body contours by removing fat through suction.',
    'Small incisions are made, and fat is removed using a suction device.',
    'Individuals with localized fat pockets or areas resistant to diet and exercise.',
    '1–2 weeks',
    '1–3 hours',
    'No',
    100000,
    350000,
    5, -- Replace with actual category ID for Body_Contouring
    'Body',
    NOW(),
    NOW()
),
(
    'Botox',
    'Botulinum Toxin Injections',
    'Reduces wrinkles and fine lines.',
    'Botox injections temporarily paralyze facial muscles to smooth wrinkles and fine lines, typically on the forehead, around the eyes, and between the brows.',
    'Small injections are made into facial muscles to reduce muscle movement and soften wrinkles.',
    'Individuals with wrinkles and fine lines, seeking a youthful appearance.',
    '1–2 days',
    '10–20 minutes',
    'No',
    15000,
    40000,
    2, -- Replace with actual category ID for Fillers_And_Other_Injectables
    'Face',
    NOW(),
    NOW()
);

-- Verify the import
SELECT COUNT(*) FROM body_parts;
SELECT COUNT(*) FROM categories;
SELECT COUNT(*) FROM procedures;