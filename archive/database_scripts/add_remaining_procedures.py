#!/usr/bin/env python3
"""
Add remaining procedures to the database.

This script adds the final batch of procedures to reach the target of 491 unique procedures.
"""
import os
import logging
import psycopg2
from psycopg2 import sql

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# List of procedures to add (these are essential procedures that are missing)
PROCEDURES_TO_ADD = [
    {
        "procedure_name": "Otoplasty",
        "short_description": "Ear surgery to improve the shape, position, or proportion of the ear.",
        "overview": "Otoplasty is a surgical procedure that reshapes the ear cartilage to create a natural shape while bringing balance and proportion to the ears and face.",
        "body_part": "Ears",
        "category_type": "Ear Surgery",
        "min_cost": 60000,
        "max_cost": 150000,
        "risks": "Infection, bleeding, scarring, asymmetry.",
        "benefits": "Improved appearance, increased confidence.",
        "tags": ["otoplasty", "ear surgery", "ear pinning"],
        "procedure_details": "The procedure involves making incisions behind the ear to expose and reshape the cartilage, creating a more proportional appearance.",
        "recovery_process": "Recovery typically involves some swelling and bruising that subsides within 1-2 weeks.",
        "ideal_candidates": "People with prominent or misshapen ears, typically performed after age 5.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "2-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Ear Surgery, Ear Pinning",
        "procedure_types": "Traditional Otoplasty, Incisionless Otoplasty",
        "results_duration": "Permanent",
        "benefits_detailed": "Improved ear shape and position, better facial balance, increased self-confidence",
        "alternative_procedures": "Non-surgical ear molding for infants"
    },
    {
        "procedure_name": "Lip Lift",
        "short_description": "Surgical procedure to lift and reshape the upper lip.",
        "overview": "A lip lift is a surgical procedure that shortens the space between the nose and the top of the lip, increasing the amount of visible pink lip.",
        "body_part": "Lips",
        "category_type": "Lip Enhancement",
        "min_cost": 40000,
        "max_cost": 120000,
        "risks": "Scarring, asymmetry, infection.",
        "benefits": "More youthful appearance, fuller lips.",
        "tags": ["lip lift", "lip surgery", "lip enhancement"],
        "procedure_details": "The procedure involves removing a small strip of skin just below the nose to lift the upper lip and create a more appealing shape.",
        "recovery_process": "Recovery typically involves swelling and bruising that subsides within 1-2 weeks.",
        "ideal_candidates": "People with a long upper lip or those seeking a more youthful lip appearance.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "1 hour",
        "hospital_stay_required": "No",
        "alternative_names": "Upper Lip Lift, Bullhorn Lip Lift",
        "procedure_types": "Bullhorn Lip Lift, Corner Lip Lift, Central Lip Lift",
        "results_duration": "Permanent",
        "benefits_detailed": "More visible upper lip, reduced distance between nose and lip, more youthful appearance",
        "alternative_procedures": "Dermal fillers for temporary lip enhancement"
    },
    {
        "procedure_name": "Brow Lift",
        "short_description": "Surgical procedure to elevate drooping eyebrows.",
        "overview": "A brow lift, also known as a forehead lift, improves the appearance of the forehead, the brow and the area around the eyes by raising the soft tissue and skin of the forehead and brow.",
        "body_part": "Forehead",
        "category_type": "Facial Rejuvenation",
        "min_cost": 70000,
        "max_cost": 180000,
        "risks": "Scarring, asymmetry, nerve damage.",
        "benefits": "More youthful, refreshed appearance.",
        "tags": ["brow lift", "forehead lift", "eyebrow lift"],
        "procedure_details": "The procedure involves removing excess skin on the forehead and repositioning the underlying muscle and tissue.",
        "recovery_process": "Recovery typically involves swelling and bruising that subsides within 2-3 weeks.",
        "ideal_candidates": "People with drooping brows or deep forehead wrinkles.",
        "recovery_time": "2-3 weeks",
        "procedure_duration": "1-2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Forehead Lift, Eyebrow Lift",
        "procedure_types": "Endoscopic Brow Lift, Coronal Brow Lift, Temporal Brow Lift",
        "results_duration": "5-10 years",
        "benefits_detailed": "Elevated brow position, reduced forehead wrinkles, more alert and youthful appearance",
        "alternative_procedures": "Botox injections for temporary brow elevation"
    },
    {
        "procedure_name": "Neck Lift",
        "short_description": "Surgical procedure to improve the appearance of the neck.",
        "overview": "A neck lift is a surgical procedure that improves visible signs of aging in the jawline and neck, such as excess fat and skin relaxation in the lower face.",
        "body_part": "Neck",
        "category_type": "Facial Rejuvenation",
        "min_cost": 90000,
        "max_cost": 200000,
        "risks": "Scarring, asymmetry, nerve damage.",
        "benefits": "More youthful neck contour.",
        "tags": ["neck lift", "neck surgery", "cervicoplasty"],
        "procedure_details": "The procedure involves removing excess skin, tightening underlying muscles, and often includes liposuction to remove fat.",
        "recovery_process": "Recovery typically involves swelling and bruising that subsides within 2-3 weeks.",
        "ideal_candidates": "People with excess neck skin, visible neck bands, or a double chin.",
        "recovery_time": "2-3 weeks",
        "procedure_duration": "2-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Cervicoplasty, Platysmaplasty",
        "procedure_types": "Traditional Neck Lift, Limited Incision Neck Lift",
        "results_duration": "5-10 years",
        "benefits_detailed": "Refined jaw and neck contour, reduced sagging, more youthful profile",
        "alternative_procedures": "Neck liposuction for patients with good skin elasticity"
    },
    {
        "procedure_name": "Abdominoplasty",
        "short_description": "Surgical removal of excess skin and fat from the abdomen.",
        "overview": "Abdominoplasty, also known as a tummy tuck, removes excess skin and fat from the abdomen and tightens the abdominal wall muscles.",
        "body_part": "Abdomen",
        "category_type": "Body Contouring",
        "min_cost": 120000,
        "max_cost": 300000,
        "risks": "Scarring, infection, fluid accumulation.",
        "benefits": "Flatter, firmer abdominal contour.",
        "tags": ["tummy tuck", "abdominoplasty", "stomach surgery"],
        "procedure_details": "The procedure involves making a horizontal incision above the pubic area, removing excess skin and fat, and tightening the abdominal muscles.",
        "recovery_process": "Recovery typically involves significant downtime with limited activity for 2-4 weeks.",
        "ideal_candidates": "People with excess abdominal skin after pregnancy or weight loss.",
        "recovery_time": "2-4 weeks",
        "procedure_duration": "2-4 hours",
        "hospital_stay_required": "Sometimes",
        "alternative_names": "Tummy Tuck",
        "procedure_types": "Full Abdominoplasty, Mini-Abdominoplasty, Extended Abdominoplasty",
        "results_duration": "Long-lasting with stable weight",
        "benefits_detailed": "Flatter abdomen, removal of stretch marks below the navel, improved body contour",
        "alternative_procedures": "Liposuction for patients with good skin elasticity"
    },
    {
        "procedure_name": "Liposuction",
        "short_description": "Surgical removal of excess fat deposits.",
        "overview": "Liposuction is a surgical procedure that removes fat from specific areas of the body to improve contour and proportion.",
        "body_part": "Multiple",
        "category_type": "Body Contouring",
        "min_cost": 80000,
        "max_cost": 250000,
        "risks": "Contour irregularities, fluid accumulation, infection.",
        "benefits": "Improved body contour and proportion.",
        "tags": ["liposuction", "lipo", "fat removal"],
        "procedure_details": "The procedure involves inserting a thin tube called a cannula through small incisions to remove fat with a suction device.",
        "recovery_process": "Recovery typically involves wearing compression garments and limited activity for 1-3 weeks.",
        "ideal_candidates": "People with localized fat deposits and good skin elasticity.",
        "recovery_time": "1-3 weeks",
        "procedure_duration": "1-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Lipo, Suction-Assisted Lipectomy",
        "procedure_types": "Tumescent Liposuction, Ultrasound-Assisted, Laser-Assisted",
        "results_duration": "Long-lasting with stable weight",
        "benefits_detailed": "Improved body contour, reduced localized fat deposits, better proportion",
        "alternative_procedures": "Non-surgical fat reduction with CoolSculpting or Kybella"
    },
    {
        "procedure_name": "Breast Augmentation",
        "short_description": "Surgical enhancement of breast size and shape.",
        "overview": "Breast augmentation is a surgical procedure that increases breast size or improves shape using implants or fat transfer.",
        "body_part": "Breast",
        "category_type": "Breast Enhancement",
        "min_cost": 100000,
        "max_cost": 280000,
        "risks": "Capsular contracture, implant rupture, changes in nipple sensation.",
        "benefits": "Enhanced breast size and shape.",
        "tags": ["breast augmentation", "breast implants", "breast enhancement"],
        "procedure_details": "The procedure involves placing implants either behind the breast tissue or under the chest muscle through incisions made in inconspicuous areas.",
        "recovery_process": "Recovery typically involves wearing a support bra and limited activity for 1-2 weeks.",
        "ideal_candidates": "People desiring larger breasts or improved breast shape.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "1-2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Breast Implants, Augmentation Mammoplasty",
        "procedure_types": "Saline Implants, Silicone Implants, Fat Transfer",
        "results_duration": "10-20 years (implants may need replacement)",
        "benefits_detailed": "Increased breast volume, improved breast shape, enhanced body proportion",
        "alternative_procedures": "Fat transfer breast augmentation for modest enhancement"
    },
    {
        "procedure_name": "Breast Reduction",
        "short_description": "Surgical reduction of breast size.",
        "overview": "Breast reduction surgery removes excess breast tissue and skin to achieve a breast size in proportion with your body.",
        "body_part": "Breast",
        "category_type": "Breast Surgery",
        "min_cost": 120000,
        "max_cost": 300000,
        "risks": "Scarring, changes in nipple sensation, asymmetry.",
        "benefits": "Relief from discomfort, improved proportion.",
        "tags": ["breast reduction", "reduction mammoplasty"],
        "procedure_details": "The procedure involves removing excess breast tissue, fat, and skin to reduce breast size and reshape the breasts.",
        "recovery_process": "Recovery typically involves wearing a support bra and limited activity for 2-4 weeks.",
        "ideal_candidates": "People with overly large breasts causing physical discomfort.",
        "recovery_time": "2-4 weeks",
        "procedure_duration": "2-5 hours",
        "hospital_stay_required": "Sometimes",
        "alternative_names": "Reduction Mammoplasty",
        "procedure_types": "Vertical or 'Lollipop' Reduction, Inverted-T or 'Anchor' Reduction",
        "results_duration": "Permanent (barring significant weight changes)",
        "benefits_detailed": "Reduced breast size, relief from physical discomfort, improved posture",
        "alternative_procedures": "Liposuction alone for minimally sagging breasts"
    },
    {
        "procedure_name": "Eyelid Surgery",
        "short_description": "Surgical procedure to improve the appearance of the eyelids.",
        "overview": "Eyelid surgery, or blepharoplasty, improves the appearance of the upper eyelids, lower eyelids, or both by removing excess skin, muscle, and fat.",
        "body_part": "Eyes",
        "category_type": "Eyelid Enhancement",
        "min_cost": 80000,
        "max_cost": 180000,
        "risks": "Dry eyes, scarring, difficulty closing eyes.",
        "benefits": "More youthful, refreshed appearance.",
        "tags": ["eyelid surgery", "blepharoplasty", "eye lift"],
        "procedure_details": "The procedure involves making incisions in the natural creases of the upper eyelids and just below the lashes in the lower eyelids to remove excess tissue.",
        "recovery_process": "Recovery typically involves some swelling and bruising that subsides within 1-2 weeks.",
        "ideal_candidates": "People with droopy upper eyelids or puffy lower eyelids.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "1-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Blepharoplasty, Eye Lift",
        "procedure_types": "Upper Blepharoplasty, Lower Blepharoplasty, Double Eyelid Surgery",
        "results_duration": "5-7 years for upper eyelids, potentially longer for lower eyelids",
        "benefits_detailed": "Reduced sagging skin, diminished puffiness, improved field of vision",
        "alternative_procedures": "Non-surgical treatments with fillers, lasers, or chemical peels"
    },
    {
        "procedure_name": "Ear Surgery",
        "short_description": "Surgical procedure to improve the appearance of the ears.",
        "overview": "Ear surgery, or otoplasty, improves the shape, position, or proportion of the ear to create a more natural shape and bring balance to the ears and face.",
        "body_part": "Ears",
        "category_type": "Ear Surgery",
        "min_cost": 60000,
        "max_cost": 150000,
        "risks": "Scarring, asymmetry, changes in sensation.",
        "benefits": "Improved ear appearance, increased confidence.",
        "tags": ["ear surgery", "otoplasty", "ear pinning"],
        "procedure_details": "The procedure involves making incisions behind the ear to expose the ear cartilage, which is then reshaped and secured with stitches.",
        "recovery_process": "Recovery typically involves wearing a bandage and later a headband at night for several weeks.",
        "ideal_candidates": "People with protruding or misshapen ears, typically performed after age 5.",
        "recovery_time": "1-2 weeks",
        "procedure_duration": "2-3 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Otoplasty, Ear Pinning",
        "procedure_types": "Traditional Otoplasty, Incisionless Otoplasty, Ear Reconstruction",
        "results_duration": "Permanent",
        "benefits_detailed": "Repositioned ears closer to head, improved ear shape, better facial balance",
        "alternative_procedures": "Non-surgical ear molding for infants"
    },
    {
        "procedure_name": "Facelift",
        "short_description": "Surgical procedure to reduce visible signs of aging in the face and neck.",
        "overview": "A facelift, or rhytidectomy, improves visible signs of aging in the face and neck by removing excess facial skin and tightening underlying tissues.",
        "body_part": "Face",
        "category_type": "Facial Rejuvenation",
        "min_cost": 150000,
        "max_cost": 400000,
        "risks": "Scarring, nerve injury, hair loss at incision sites.",
        "benefits": "More youthful facial appearance.",
        "tags": ["facelift", "rhytidectomy", "face lift"],
        "procedure_details": "The procedure involves making incisions typically beginning in the hairline at the temples, continuing around the ear, and ending in the lower scalp, through which facial skin is lifted and underlying tissues are tightened.",
        "recovery_process": "Recovery typically involves significant swelling and bruising that gradually improves over 2-3 weeks.",
        "ideal_candidates": "People with facial sagging, jowls, and loss of muscle tone.",
        "recovery_time": "2-3 weeks",
        "procedure_duration": "3-5 hours",
        "hospital_stay_required": "Sometimes",
        "alternative_names": "Rhytidectomy",
        "procedure_types": "Traditional Facelift, Mini-Facelift, Mid-Facelift, Deep Plane Facelift",
        "results_duration": "5-10 years",
        "benefits_detailed": "Tighter facial skin, reduced jowls, improved neck contour, more youthful appearance",
        "alternative_procedures": "Thread lift for minimally invasive lifting"
    },
    {
        "procedure_name": "Rhinoplasty",
        "short_description": "Surgical reshaping of the nose.",
        "overview": "Rhinoplasty is a surgical procedure that reshapes the nose by modifying the bone, cartilage, skin, or all three to enhance facial harmony or correct breathing problems.",
        "body_part": "Nose",
        "category_type": "Nose Reshaping",
        "min_cost": 100000,
        "max_cost": 300000,
        "risks": "Difficulty breathing, asymmetry, persistent swelling.",
        "benefits": "Improved nasal appearance and proportion.",
        "tags": ["rhinoplasty", "nose job", "nose surgery"],
        "procedure_details": "The procedure involves making incisions inside the nose or across the columella (the tissue between the nostrils) to access and reshape the underlying bone and cartilage.",
        "recovery_process": "Recovery typically involves wearing a nasal splint for the first week and experiencing swelling that gradually improves over several months.",
        "ideal_candidates": "People dissatisfied with their nose appearance or having breathing difficulties.",
        "recovery_time": "1-2 weeks initial, several months for final results",
        "procedure_duration": "1-4 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Nose Job, Nose Reshaping Surgery",
        "procedure_types": "Open Rhinoplasty, Closed Rhinoplasty, Revision Rhinoplasty",
        "results_duration": "Permanent",
        "benefits_detailed": "Improved nasal shape, better facial proportion, potential breathing improvement",
        "alternative_procedures": "Non-surgical rhinoplasty using fillers for minor corrections"
    },
    {
        "procedure_name": "Botox Injection",
        "short_description": "Non-surgical treatment to reduce facial wrinkles.",
        "overview": "Botox injections use a toxin to temporarily paralyze muscle activity, reducing the appearance of facial wrinkles.",
        "body_part": "Face",
        "category_type": "Non-Surgical Treatments",
        "min_cost": 15000,
        "max_cost": 50000,
        "risks": "Bruising, headache, temporary facial drooping.",
        "benefits": "Reduced appearance of wrinkles.",
        "tags": ["botox", "botulinum toxin", "wrinkle treatment"],
        "procedure_details": "The procedure involves injecting small amounts of botulinum toxin into specific muscles to temporarily reduce muscle activity.",
        "recovery_process": "Recovery is minimal with results appearing within 3-7 days and lasting 3-4 months.",
        "ideal_candidates": "People with dynamic wrinkles caused by facial expressions.",
        "recovery_time": "0-1 day",
        "procedure_duration": "10-30 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Botulinum Toxin Type A, Dysport, Xeomin",
        "procedure_types": "Cosmetic Botox, Therapeutic Botox",
        "results_duration": "3-4 months",
        "benefits_detailed": "Reduced appearance of forehead lines, crow's feet, and frown lines",
        "alternative_procedures": "Dermal fillers, laser treatments, chemical peels"
    },
    {
        "procedure_name": "Dermal Fillers",
        "short_description": "Injectable treatments to add volume and reduce wrinkles.",
        "overview": "Dermal fillers are gel-like substances injected beneath the skin to restore lost volume, smooth lines, soften creases, or enhance facial contours.",
        "body_part": "Face",
        "category_type": "Non-Surgical Treatments",
        "min_cost": 20000,
        "max_cost": 80000,
        "risks": "Bruising, redness, lumps, asymmetry.",
        "benefits": "Restored volume, smoother skin.",
        "tags": ["fillers", "dermal fillers", "facial fillers"],
        "procedure_details": "The procedure involves injecting hyaluronic acid, calcium hydroxylapatite, or other substances beneath the skin surface.",
        "recovery_process": "Recovery is minimal with temporary swelling and bruising possible for a few days.",
        "ideal_candidates": "People with static wrinkles, volume loss, or desire for lip enhancement.",
        "recovery_time": "0-2 days",
        "procedure_duration": "15-60 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Facial Fillers, Injectable Fillers",
        "procedure_types": "Hyaluronic Acid Fillers, Calcium Hydroxylapatite, Poly-L-lactic Acid",
        "results_duration": "6-24 months depending on filler type",
        "benefits_detailed": "Immediate volume restoration, wrinkle reduction, enhanced facial contours",
        "alternative_procedures": "Fat transfer, facial implants, laser treatments"
    },
    {
        "procedure_name": "Laser Skin Resurfacing",
        "short_description": "Non-surgical treatment to improve skin texture and appearance.",
        "overview": "Laser skin resurfacing uses laser energy to improve skin texture and appearance by removing damaged skin layers and stimulating new collagen production.",
        "body_part": "Face",
        "category_type": "Non-Surgical Treatments",
        "min_cost": 30000,
        "max_cost": 100000,
        "risks": "Redness, swelling, changes in skin color.",
        "benefits": "Smoother, more youthful-looking skin.",
        "tags": ["laser resurfacing", "skin resurfacing", "laser treatment"],
        "procedure_details": "The procedure involves directing short, concentrated pulsating beams of light at irregular skin, precisely removing skin layer by layer.",
        "recovery_process": "Recovery depends on treatment intensity, ranging from a few days for non-ablative to 1-2 weeks for ablative lasers.",
        "ideal_candidates": "People with acne scars, age spots, fine lines, or uneven skin tone.",
        "recovery_time": "3-14 days depending on treatment intensity",
        "procedure_duration": "30 minutes - 2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Laser Peel, Lasabrasion",
        "procedure_types": "Ablative Laser Resurfacing, Non-ablative Laser Resurfacing, Fractional Laser Treatment",
        "results_duration": "1-5 years depending on treatment type",
        "benefits_detailed": "Reduced fine lines, improved skin texture, more even skin tone",
        "alternative_procedures": "Chemical peels, microdermabrasion, microneedling"
    },
    {
        "procedure_name": "Chemical Peel",
        "short_description": "Non-surgical treatment to improve skin appearance.",
        "overview": "A chemical peel is a technique used to improve the appearance of the skin by applying a chemical solution that causes dead skin to slough off and eventually peel off.",
        "body_part": "Face",
        "category_type": "Non-Surgical Treatments",
        "min_cost": 10000,
        "max_cost": 60000,
        "risks": "Redness, scaling, changes in skin color.",
        "benefits": "Smoother, more even skin tone.",
        "tags": ["chemical peel", "skin peel", "facial peel"],
        "procedure_details": "The procedure involves applying a chemical solution (acid) to the skin, causing controlled damage that leads to skin regeneration.",
        "recovery_process": "Recovery depends on peel depth, ranging from 1-7 days for light peels to 2-3 weeks for deep peels.",
        "ideal_candidates": "People with sun damage, uneven skin tone, fine lines, or certain types of acne.",
        "recovery_time": "1-21 days depending on peel depth",
        "procedure_duration": "30-90 minutes",
        "hospital_stay_required": "No",
        "alternative_names": "Chemexfoliation, Derma Peel",
        "procedure_types": "Superficial Peels, Medium Peels, Deep Peels",
        "results_duration": "1 month to years depending on peel depth",
        "benefits_detailed": "Improved skin texture, reduced hyperpigmentation, more even skin tone",
        "alternative_procedures": "Laser resurfacing, microdermabrasion, dermaplaning"
    },
    {
        "procedure_name": "Scar Revision",
        "short_description": "Surgical or non-surgical treatment to improve the appearance of scars.",
        "overview": "Scar revision is a surgical or non-surgical procedure designed to improve the appearance of a scar by making it blend more naturally with the surrounding skin tone and texture.",
        "body_part": "Multiple",
        "category_type": "Reconstructive Surgery",
        "min_cost": 40000,
        "max_cost": 150000,
        "risks": "Infection, additional scarring, changes in skin texture.",
        "benefits": "Improved scar appearance.",
        "tags": ["scar revision", "scar treatment", "scar removal"],
        "procedure_details": "The procedure may involve surgical excision, laser therapy, chemical treatments, or injections depending on scar type and location.",
        "recovery_process": "Recovery depends on the treatment approach, ranging from minimal downtime for non-surgical options to 1-2 weeks for surgical revision.",
        "ideal_candidates": "People with noticeable or disfiguring scars from injuries, surgeries, or burns.",
        "recovery_time": "1 day to 2 weeks depending on treatment type",
        "procedure_duration": "30 minutes - 2 hours",
        "hospital_stay_required": "No",
        "alternative_names": "Scar Treatment, Scar Reduction",
        "procedure_types": "Surgical Scar Revision, Laser Scar Revision, Injectable Treatments",
        "results_duration": "Permanent improvement with proper care",
        "benefits_detailed": "Improved scar appearance, better texture match with surrounding skin",
        "alternative_procedures": "Topical silicone treatments, steroid injections, dermabrasion"
    },
    {
        "procedure_name": "Body Contouring",
        "short_description": "Surgical procedures to reshape body contours.",
        "overview": "Body contouring refers to surgical procedures that improve the shape and tone of underlying tissue that supports fat and skin to reshape different areas of the body.",
        "body_part": "Multiple",
        "category_type": "Body Contouring",
        "min_cost": 100000,
        "max_cost": 350000,
        "risks": "Scarring, asymmetry, fluid accumulation.",
        "benefits": "Improved body shape and contour.",
        "tags": ["body contouring", "body lift", "body sculpting"],
        "procedure_details": "The procedures may include tummy tuck, arm lift, thigh lift, or body lift depending on the areas being treated.",
        "recovery_process": "Recovery typically involves wearing compression garments and limited activity for 2-6 weeks depending on the extent of surgery.",
        "ideal_candidates": "People with excess skin after significant weight loss or those seeking improved body contours.",
        "recovery_time": "2-6 weeks",
        "procedure_duration": "2-8 hours depending on extent",
        "hospital_stay_required": "Sometimes",
        "alternative_names": "Body Lift, Body Sculpting",
        "procedure_types": "Lower Body Lift, Upper Body Lift, Total Body Lift",
        "results_duration": "Long-lasting with stable weight",
        "benefits_detailed": "Removal of excess skin, improved body contours, better-fitting clothes",
        "alternative_procedures": "Non-surgical treatments for modest improvements only"
    },
    {
        "procedure_name": "Buttock Augmentation",
        "short_description": "Surgical enhancement of the buttocks.",
        "overview": "Buttock augmentation enhances the size and shape of the buttocks using implants, fat transfer, or a combination of both methods.",
        "body_part": "Buttocks",
        "category_type": "Body Contouring",
        "min_cost": 120000,
        "max_cost": 300000,
        "risks": "Infection, implant displacement, asymmetry.",
        "benefits": "Enhanced buttock shape and size.",
        "tags": ["buttock augmentation", "brazilian butt lift", "BBL"],
        "procedure_details": "The procedure may involve placing silicone implants or injecting purified fat harvested from other body areas (Brazilian Butt Lift).",
        "recovery_process": "Recovery typically involves avoiding sitting directly on the buttocks for 2-3 weeks and wearing a compression garment.",
        "ideal_candidates": "People seeking fuller, more projected buttocks.",
        "recovery_time": "2-4 weeks",
        "procedure_duration": "2-4 hours",
        "hospital_stay_required": "Sometimes",
        "alternative_names": "Brazilian Butt Lift (BBL), Gluteal Augmentation",
        "procedure_types": "Buttock Implants, Fat Transfer (BBL), Combination Approach",
        "results_duration": "2-8 years for fat transfer, longer for implants",
        "benefits_detailed": "Enhanced buttock volume, improved hip-to-waist ratio, more balanced silhouette",
        "alternative_procedures": "Non-surgical buttock enhancement with injectable fillers"
    }
]

def get_db_connection():
    """Get a connection to the database."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        logger.error("DATABASE_URL environment variable not set")
        return None
    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def get_category_id(conn, body_part_name, category_type):
    """Get category ID by name and body part."""
    with conn.cursor() as cursor:
        # First check if category already exists
        category_display_name = f"{body_part_name}_{category_type}"
        cursor.execute(
            "SELECT id FROM categories WHERE display_name = %s",
            (category_display_name,)
        )
        result = cursor.fetchone()
        if result:
            logger.info(f"Found existing category: {category_display_name}")
            return result[0]

        # Get body part ID
        cursor.execute(
            "SELECT id FROM body_parts WHERE name = %s",
            (body_part_name,)
        )
        body_part_result = cursor.fetchone()
        if not body_part_result:
            # Create body part if it doesn't exist
            cursor.execute(
                "INSERT INTO body_parts (name) VALUES (%s) RETURNING id",
                (body_part_name,)
            )
            body_part_id = cursor.fetchone()[0]
            logger.info(f"Created new body part: {body_part_name}")
        else:
            body_part_id = body_part_result[0]

        # Create category
        cursor.execute(
            """
            INSERT INTO categories (name, body_part_id, display_name) 
            VALUES (%s, %s, %s) RETURNING id
            """,
            (category_type, body_part_id, category_display_name)
        )
        category_id = cursor.fetchone()[0]
        logger.info(f"Created category: {category_display_name}")
        return category_id

def add_procedures():
    """Add procedures to the database."""
    conn = get_db_connection()
    if not conn:
        return 0

    logger.info(f"Adding {len(PROCEDURES_TO_ADD)} procedures...")
    added_count = 0

    for procedure in PROCEDURES_TO_ADD:
        try:
            # Check if procedure already exists
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM procedures WHERE procedure_name = %s",
                    (procedure["procedure_name"],)
                )
                if cursor.fetchone():
                    logger.info(f"Procedure already exists: {procedure['procedure_name']}")
                    continue

            # Get or create category
            category_id = get_category_id(conn, procedure["body_part"], procedure["category_type"])

            # Convert tags to PostgreSQL array format
            tags = procedure.get("tags", [])
            if not tags:
                tags = [procedure["procedure_name"].lower()]

            # Insert procedure
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO procedures (
                        procedure_name, short_description, overview, body_part, category_id,
                        min_cost, max_cost, risks, benefits, tags,
                        body_area, category_type, procedure_details, recovery_process, 
                        ideal_candidates, alternative_names, recovery_time, procedure_duration,
                        hospital_stay_required, procedure_types, results_duration, 
                        benefits_detailed, alternative_procedures
                    ) VALUES (
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, 
                        %s, %s
                    )
                    """,
                    (
                        procedure["procedure_name"],
                        procedure["short_description"],
                        procedure["overview"],
                        procedure["body_part"],
                        category_id,
                        procedure["min_cost"],
                        procedure["max_cost"],
                        procedure["risks"],
                        procedure["benefits"],
                        tags,
                        procedure["body_part"],  # body_area is same as body_part
                        procedure["category_type"],
                        procedure.get("procedure_details", ""),
                        procedure.get("recovery_process", ""),
                        procedure.get("ideal_candidates", ""),
                        procedure.get("alternative_names", ""),
                        procedure.get("recovery_time", ""),
                        procedure.get("procedure_duration", ""),
                        procedure.get("hospital_stay_required", ""),
                        procedure.get("procedure_types", ""),
                        procedure.get("results_duration", ""),
                        procedure.get("benefits_detailed", ""),
                        procedure.get("alternative_procedures", "")
                    )
                )
                logger.info(f"Added procedure: {procedure['procedure_name']}")
                added_count += 1
        except Exception as e:
            logger.error(f"Error adding procedure {procedure['procedure_name']}: {e}")

    logger.info(f"Added {added_count} procedures.")
    return added_count

def main():
    """Run the procedure addition script."""
    added_count = add_procedures()
    logger.info(f"Total procedures added: {added_count}")
    
    # Get current procedure count
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM procedures")
            count = cursor.fetchone()[0]
            logger.info(f"Total procedures in database: {count}")
        conn.close()

if __name__ == "__main__":
    main()