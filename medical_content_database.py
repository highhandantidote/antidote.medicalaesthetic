"""
Comprehensive Medical Content Database for Aesthetic Treatments
Contains detailed, medically accurate information for each treatment type
"""

TREATMENT_CONTENT = {
    # HAIR TREATMENTS
    'PRP for Hair Regrowth': {
        'about': """
        <p>PRP hair regrowth is an advanced, non-surgical treatment that uses your own blood's healing properties to stimulate hair follicles and promote natural hair regrowth. The procedure involves extracting a small amount of your blood, processing it to concentrate the platelets, and injecting this nutrient-rich plasma directly into the scalp.</p>
        
        <h4>How PRP Works for Hair Growth:</h4>
        <ul>
        <li><strong>Platelet Concentration:</strong> Your blood is spun in a centrifuge to separate and concentrate platelets</li>
        <li><strong>Growth Factor Release:</strong> Platelets release growth factors that stimulate dormant hair follicles</li>
        <li><strong>Improved Blood Flow:</strong> Enhanced circulation brings more nutrients to hair roots</li>
        <li><strong>Cellular Regeneration:</strong> Promotes healing and regeneration of hair follicle cells</li>
        </ul>
        
        <h4>Expected Results Timeline:</h4>
        <ul>
        <li><strong>4-6 weeks:</strong> Reduced hair fall and improved hair texture</li>
        <li><strong>3-4 months:</strong> New hair growth becomes visible</li>
        <li><strong>6-12 months:</strong> Significant improvement in hair density and thickness</li>
        <li><strong>Long-term:</strong> Results can last 12-18 months with maintenance sessions</li>
        </ul>
        """,
        'ideal_candidates': 'Adults with androgenetic alopecia, thinning hair, or early-stage hair loss. Not suitable for complete baldness or scarred areas.',
        'duration': '45-60 minutes per session',
        'sessions': '3-6 sessions, spaced 4-6 weeks apart',
        'downtime': '24-48 hours of mild scalp tenderness',
        'recovery_details': 'Avoid washing hair for 24 hours. No strenuous exercise for 48 hours. Mild scalp tenderness and temporary redness normal.',
        'precautions': [
            'Do not wash hair for 24 hours post-treatment',
            'Avoid direct sun exposure for 48 hours',
            'No hair styling products for 24 hours',
            'Avoid blood-thinning medications 3 days before treatment',
            'Stay hydrated and eat well before procedure'
        ],
        'contraindications': 'Active scalp infections, blood disorders, cancer patients undergoing chemotherapy, pregnancy, breastfeeding'
    },
    
    'GFC for Hair Regrowth': {
        'about': """
        <p>GFC is the next-generation advancement of PRP therapy. Growth Factor Concentrate uses a more sophisticated extraction process to isolate and concentrate specific growth factors from your blood, providing higher potency and better results than traditional PRP.</p>
        
        <h4>GFC vs Traditional PRP:</h4>
        <ul>
        <li><strong>Higher Concentration:</strong> 3-5x more growth factors than regular PRP</li>
        <li><strong>Purer Formula:</strong> Removes inflammatory cells that can hinder healing</li>
        <li><strong>Better Results:</strong> Studies show 40% better hair growth compared to PRP</li>
        <li><strong>Less Sessions:</strong> Often requires fewer treatment sessions</li>
        </ul>
        
        <h4>Growth Factors in GFC:</h4>
        <ul>
        <li><strong>PDGF:</strong> Promotes blood vessel formation</li>
        <li><strong>VEGF:</strong> Stimulates new blood vessel growth</li>
        <li><strong>IGF-1:</strong> Encourages hair follicle proliferation</li>
        <li><strong>FGF:</strong> Supports tissue repair and regeneration</li>
        </ul>
        """,
        'ideal_candidates': 'Adults with moderate to severe hair thinning, pattern baldness (Norwood 2-5), or those who need faster results than traditional PRP.',
        'duration': '60-75 minutes per session',
        'sessions': '3-4 sessions, spaced 6-8 weeks apart',
        'downtime': '24-48 hours of mild discomfort',
        'recovery_details': 'Similar to PRP but often with less inflammation. Avoid hair washing for 24 hours.',
        'precautions': [
            'No hair washing for 24 hours',
            'Avoid alcohol 48 hours before and after',
            'No anti-inflammatory medications for 3 days',
            'Use gentle, sulfate-free shampoo when resuming washing',
            'Sleep with head elevated first night'
        ],
        'contraindications': 'Same as PRP, plus patients with autoimmune conditions should consult physician first'
    },
    
    'Hair Transplantation': {
        'about': """
        <p>Hair transplantation is a permanent surgical solution for hair loss using the Follicular Unit Extraction (FUE) method. Individual hair follicles are carefully extracted from the donor area (usually back of head) and transplanted to balding or thinning areas. This procedure provides natural-looking, permanent results.</p>
        
        <h4>FUE Technique Advantages:</h4>
        <ul>
        <li><strong>No Linear Scar:</strong> Tiny circular scars that heal completely</li>
        <li><strong>Natural Results:</strong> Hair grows in natural direction and pattern</li>
        <li><strong>Permanent Solution:</strong> Transplanted hair is genetically resistant to balding</li>
        <li><strong>Minimal Downtime:</strong> Return to work in 2-3 days</li>
        </ul>
        
        <h4>Grafts Needed by Area:</h4>
        <ul>
        <li><strong>Hairline restoration:</strong> 1,000-1,500 grafts</li>
        <li><strong>Crown area:</strong> 1,200-2,000 grafts</li>
        <li><strong>Full head coverage:</strong> 2,500-4,000 grafts</li>
        <li><strong>Beard/mustache:</strong> 400-1,200 grafts</li>
        </ul>
        
        <h4>Growth Timeline:</h4>
        <ul>
        <li><strong>2-3 weeks:</strong> Transplanted hair falls out (normal shock loss)</li>
        <li><strong>3-4 months:</strong> New hair growth begins</li>
        <li><strong>6-9 months:</strong> Significant density improvement</li>
        <li><strong>12-18 months:</strong> Final results achieved</li>
        </ul>
        """,
        'ideal_candidates': 'Adults with stable hair loss pattern, sufficient donor hair, realistic expectations, and good overall health.',
        'duration': '6-8 hours depending on graft count',
        'sessions': 'Single session for most cases, large procedures may require 2 sessions',
        'downtime': '7-10 days for healing, 2-3 weeks for complete recovery',
        'recovery_details': 'Gentle hair washing after 48 hours. Avoid touching grafts for 10 days. Sleep elevated for first week.',
        'precautions': [
            'No alcohol or smoking 1 week before and after',
            'Avoid blood thinners 1 week before',
            'No strenuous exercise for 2 weeks',
            'Protect head from sun for 2 weeks',
            'Follow specific washing instructions carefully'
        ],
        'contraindications': 'Uncontrolled diabetes, bleeding disorders, active scalp infections, unrealistic expectations, insufficient donor hair'
    },
    
    # BOTOX & FILLERS
    'Botox (Facial)': {
        'about': """
        <p>Botox (Botulinum Toxin Type A) is a purified protein that temporarily relaxes facial muscles responsible for creating wrinkles. When injected into specific muscles, it blocks nerve signals that cause muscle contractions, smoothing existing wrinkles and preventing new ones from forming.</p>
        
        <h4>Common Treatment Areas:</h4>
        <ul>
        <li><strong>Forehead Lines:</strong> Horizontal lines across forehead</li>
        <li><strong>Frown Lines:</strong> Vertical lines between eyebrows (11's)</li>
        <li><strong>Crow's Feet:</strong> Lines around outer corners of eyes</li>
        <li><strong>Bunny Lines:</strong> Lines on sides of nose when smiling</li>
        <li><strong>Lip Lines:</strong> Vertical lines around mouth</li>
        <li><strong>Neck Bands:</strong> Vertical neck muscle bands</li>
        </ul>
        
        <h4>How Botox Works:</h4>
        <ul>
        <li><strong>Muscle Relaxation:</strong> Blocks acetylcholine release at nerve endings</li>
        <li><strong>Wrinkle Smoothing:</strong> Relaxed muscles allow skin to smooth out</li>
        <li><strong>Prevention:</strong> Prevents deepening of existing lines</li>
        <li><strong>Natural Look:</strong> Maintains facial expression when done properly</li>
        </ul>
        
        <h4>Results Timeline:</h4>
        <ul>
        <li><strong>3-5 days:</strong> Initial effects begin to show</li>
        <li><strong>7-14 days:</strong> Full results achieved</li>
        <li><strong>3-4 months:</strong> Gradual return of muscle movement</li>
        <li><strong>4-6 months:</strong> Repeat treatment recommended</li>
        </ul>
        """,
        'ideal_candidates': 'Adults aged 25-65 with dynamic wrinkles (wrinkles that appear with facial expressions), realistic expectations, and no contraindications.',
        'duration': '15-30 minutes',
        'sessions': 'Single session, repeat every 3-6 months',
        'downtime': 'Minimal - resume normal activities immediately',
        'recovery_details': 'Avoid lying down for 4 hours. No exercise for 24 hours. Results appear gradually over 3-14 days.',
        'precautions': [
            'No rubbing or massaging treated areas for 24 hours',
            'Stay upright for 4 hours post-treatment',
            'No strenuous exercise for 24 hours',
            'Avoid alcohol for 24 hours',
            'No facials or laser treatments for 2 weeks'
        ],
        'contraindications': 'Pregnancy, breastfeeding, neuromuscular disorders (myasthenia gravis), allergy to botulinum toxin, active skin infections'
    },
    
    'Dermal Fillers': {
        'about': """
        <p>Dermal fillers are injectable treatments using hyaluronic acid (HA) to restore volume, smooth wrinkles, and enhance facial contours. Hyaluronic acid is a naturally occurring substance in our skin that retains moisture and provides structure. As we age, HA levels decrease, leading to volume loss and wrinkles.</p>
        
        <h4>Types of Fillers Used:</h4>
        <ul>
        <li><strong>Soft Fillers:</strong> For fine lines and superficial wrinkles</li>
        <li><strong>Medium Fillers:</strong> For nasolabial folds and moderate wrinkles</li>
        <li><strong>Volumizing Fillers:</strong> For cheeks, temples, and deep volume loss</li>
        <li><strong>Specialized Fillers:</strong> For lips, under-eyes, and specific areas</li>
        </ul>
        
        <h4>Common Treatment Areas:</h4>
        <ul>
        <li><strong>Nasolabial Folds:</strong> Lines from nose to mouth corners</li>
        <li><strong>Marionette Lines:</strong> Lines from mouth corners downward</li>
        <li><strong>Cheek Volume:</strong> Restore youthful cheek fullness</li>
        <li><strong>Lip Enhancement:</strong> Add volume and definition to lips</li>
        <li><strong>Under-Eye Hollows:</strong> Fill tear troughs and dark circles</li>
        <li><strong>Jawline Contouring:</strong> Define and strengthen jaw</li>
        </ul>
        
        <h4>Benefits of HA Fillers:</h4>
        <ul>
        <li><strong>Natural Results:</strong> Biocompatible with human tissue</li>
        <li><strong>Reversible:</strong> Can be dissolved with hyaluronidase if needed</li>
        <li><strong>Long-lasting:</strong> Results last 6-18 months depending on type</li>
        <li><strong>Immediate Results:</strong> See improvement right after treatment</li>
        </ul>
        """,
        'ideal_candidates': 'Adults with volume loss, static wrinkles, or those wanting facial enhancement. Good candidates have realistic expectations and healthy skin.',
        'duration': '30-60 minutes depending on areas treated',
        'sessions': 'Single session, touch-ups may be needed after 2 weeks',
        'downtime': '24-48 hours of potential swelling and bruising',
        'recovery_details': 'Ice for first 24 hours. Avoid makeup for 12 hours. Sleep elevated first night to minimize swelling.',
        'precautions': [
            'Avoid blood thinners 1 week before (aspirin, fish oil)',
            'No alcohol 24 hours before and after',
            'Ice immediately after treatment',
            'Avoid strenuous exercise for 24 hours',
            'No dental work for 2 weeks after lip fillers'
        ],
        'contraindications': 'Pregnancy, breastfeeding, active cold sores (lip area), autoimmune conditions, allergy to hyaluronic acid'
    },
    
    # FACIAL TREATMENTS
    'Hydrafacial': {
        'about': """
        <p>HydraFacial is a patented, non-invasive treatment that combines cleansing, exfoliation, extraction, hydration, and antioxidant protection in one session. Using a unique vortex-fusion technology, it removes dead skin cells and impurities while simultaneously delivering moisturizing serums into the skin.</p>
        
        <h4>The 3-Step HydraFacial Process:</h4>
        <ul>
        <li><strong>Step 1 - Cleanse + Peel:</strong> Gentle exfoliation reveals new skin layer</li>
        <li><strong>Step 2 - Extract + Hydrate:</strong> Painless extractions remove debris from pores</li>
        <li><strong>Step 3 - Fuse + Protect:</strong> Antioxidants and peptides maximize glow</li>
        </ul>
        
        <h4>Key Benefits:</h4>
        <ul>
        <li><strong>Immediate Results:</strong> Skin looks brighter and feels smoother instantly</li>
        <li><strong>No Downtime:</strong> Resume normal activities immediately</li>
        <li><strong>Suitable for All Skin Types:</strong> Even sensitive skin tolerates well</li>
        <li><strong>Customizable:</strong> Treatment tailored to specific skin concerns</li>
        <li><strong>Painless:</strong> Comfortable treatment with no discomfort</li>
        </ul>
        
        <h4>Skin Concerns Addressed:</h4>
        <ul>
        <li>Fine lines and wrinkles</li>
        <li>Enlarged pores and blackheads</li>
        <li>Oily and congested skin</li>
        <li>Dull complexion</li>
        <li>Uneven skin tone</li>
        <li>Age spots and sun damage</li>
        </ul>
        
        <h4>Add-on Boosters Available:</h4>
        <ul>
        <li><strong>Anti-Aging Booster:</strong> Growth factors for mature skin</li>
        <li><strong>Brightening Booster:</strong> Vitamin C for radiance</li>
        <li><strong>Clarifying Booster:</strong> Salicylic acid for acne-prone skin</li>
        </ul>
        """,
        'ideal_candidates': 'All adults looking to improve skin texture, hydration, and overall appearance. Excellent for maintenance and pre-event treatments.',
        'duration': '30-45 minutes',
        'sessions': 'Single session, monthly treatments recommended for optimal results',
        'downtime': 'None - immediate return to normal activities',
        'recovery_details': 'Skin may appear slightly flushed for 1-2 hours. Apply sunscreen and moisturizer as usual.',
        'precautions': [
            'Avoid sun exposure and use SPF 30+ daily',
            'Do not use retinoids for 48 hours before treatment',
            'Gentle skincare only for 24 hours post-treatment',
            'Stay hydrated to maintain results',
            'No microdermabrasion for 1 week after'
        ],
        'contraindications': 'Active rosacea flare-up, open wounds, sunburn, recent chemical peels (within 2 weeks)'
    },
    
    # LASER TREATMENTS
    'Laser Hair Reduction': {
        'about': """
        <p>Laser hair reduction uses concentrated light energy to target and destroy hair follicles, resulting in permanent hair reduction. The diode laser system emits a specific wavelength that is absorbed by melanin in hair follicles, heating and damaging them to prevent future hair growth.</p>
        
        <h4>How Laser Hair Removal Works:</h4>
        <ul>
        <li><strong>Selective Photothermolysis:</strong> Laser targets dark pigment in hair</li>
        <li><strong>Follicle Destruction:</strong> Heat damages hair follicle stem cells</li>
        <li><strong>Growth Phase Targeting:</strong> Only effective on actively growing hair (anagen phase)</li>
        <li><strong>Progressive Reduction:</strong> Each session reduces hair count by 15-25%</li>
        </ul>
        
        <h4>Treatment Areas:</h4>
        <ul>
        <li><strong>Face:</strong> Upper lip, chin, cheeks, forehead</li>
        <li><strong>Body:</strong> Arms, legs, chest, back, shoulders</li>
        <li><strong>Intimate Areas:</strong> Brazilian, bikini line, underarms</li>
        <li><strong>Men's Areas:</strong> Beard shaping, chest, back</li>
        </ul>
        
        <h4>Expected Results:</h4>
        <ul>
        <li><strong>After 1st session:</strong> 15-20% hair reduction</li>
        <li><strong>After 3rd session:</strong> 50-60% hair reduction</li>
        <li><strong>After 6th session:</strong> 80-90% hair reduction</li>
        <li><strong>Maintenance:</strong> Annual touch-ups may be needed</li>
        </ul>
        
        <h4>Diode Laser Advantages:</h4>
        <ul>
        <li><strong>Safe for All Skin Types:</strong> Including darker skin tones</li>
        <li><strong>Fast Treatment:</strong> Large spot size covers more area</li>
        <li><strong>Comfortable:</strong> Built-in cooling system</li>
        <li><strong>Precise:</strong> Targets hair without damaging surrounding skin</li>
        </ul>
        """,
        'ideal_candidates': 'Adults with unwanted hair growth, realistic expectations about permanent reduction (not complete elimination), and suitable hair/skin color contrast.',
        'duration': '15 minutes (small area) to 90 minutes (full body)',
        'sessions': '6-8 sessions spaced 4-8 weeks apart depending on body area',
        'downtime': 'None to minimal - possible redness for 2-24 hours',
        'recovery_details': 'Avoid sun exposure and use aloe vera gel if skin is irritated. Hair will shed naturally over 1-3 weeks.',
        'precautions': [
            'No plucking, waxing, or threading 6 weeks before treatment',
            'Shave treatment area 24 hours before session',
            'Avoid sun exposure 2 weeks before and after',
            'Use SPF 30+ daily on treated areas',
            'No deodorant on day of underarm treatment'
        ],
        'contraindications': 'Pregnancy, active tan, tattoos in treatment area, photosensitive medications, history of keloid scarring'
    },
    
    # ACNE TREATMENTS
    'Acne': {
        'about': """
        <p>Our comprehensive acne treatment program combines multiple evidence-based therapies to address all aspects of acne formation. We use a multi-modal approach including topical treatments, chemical peels, extractions, and advanced technologies to achieve clear, healthy skin.</p>
        
        <h4>Types of Acne We Treat:</h4>
        <ul>
        <li><strong>Comedonal Acne:</strong> Blackheads and whiteheads</li>
        <li><strong>Inflammatory Acne:</strong> Papules, pustules, and nodules</li>
        <li><strong>Hormonal Acne:</strong> Jawline and chin breakouts</li>
        <li><strong>Cystic Acne:</strong> Deep, painful lesions</li>
        <li><strong>Body Acne:</strong> Back, chest, and shoulder breakouts</li>
        </ul>
        
        <h4>Treatment Modalities:</h4>
        <ul>
        <li><strong>Professional Extractions:</strong> Safe removal of comedones</li>
        <li><strong>Chemical Peels:</strong> Salicylic acid and glycolic acid peels</li>
        <li><strong>LED Light Therapy:</strong> Blue light kills acne bacteria</li>
        <li><strong>Microneedling:</strong> Improves skin texture and scarring</li>
        <li><strong>Customized Skincare:</strong> Medical-grade products for home care</li>
        </ul>
        
        <h4>The 4 Factors of Acne:</h4>
        <ul>
        <li><strong>Excess Oil Production:</strong> Controlled with appropriate treatments</li>
        <li><strong>Clogged Pores:</strong> Addressed with exfoliation and extractions</li>
        <li><strong>Bacterial Growth:</strong> Treated with antimicrobial therapies</li>
        <li><strong>Inflammation:</strong> Reduced with anti-inflammatory treatments</li>
        </ul>
        
        <h4>Expected Timeline:</h4>
        <ul>
        <li><strong>2-4 weeks:</strong> Initial improvement in skin texture</li>
        <li><strong>6-8 weeks:</strong> Significant reduction in active breakouts</li>
        <li><strong>3-4 months:</strong> Major improvement in skin clarity</li>
        <li><strong>6+ months:</strong> Maintenance phase with clear skin</li>
        </ul>
        """,
        'ideal_candidates': 'Teens and adults with persistent acne that hasn\'t responded to over-the-counter treatments, or those wanting professional management.',
        'duration': '45-60 minutes per treatment session',
        'sessions': 'Weekly sessions for 6-8 weeks, then bi-weekly maintenance',
        'downtime': 'Minimal - possible temporary redness and dryness',
        'recovery_details': 'Skin may be slightly red and dry for 1-2 days. Use gentle, non-comedogenic skincare products.',
        'precautions': [
            'Avoid picking or squeezing pimples',
            'Use only recommended skincare products',
            'Sun protection is crucial during treatment',
            'Avoid waxing or harsh scrubs',
            'Inform us of any oral medications'
        ],
        'contraindications': 'Recent isotretinoin use (within 6 months), active cold sores, pregnancy (some treatments), recent chemical peels'
    }
}

def get_treatment_content(treatment_name):
    """Get detailed medical content for a specific treatment"""
    # Normalize treatment name for lookup
    normalized_name = treatment_name.strip()
    
    if normalized_name in TREATMENT_CONTENT:
        return TREATMENT_CONTENT[normalized_name]
    
    # Try to find similar treatments
    for key in TREATMENT_CONTENT.keys():
        if normalized_name.lower() in key.lower() or key.lower() in normalized_name.lower():
            return TREATMENT_CONTENT[key]
    
    # Return generic content if no specific match found
    return {
        'about': f"""
        <p>Our {treatment_name} treatment is performed by experienced medical professionals using advanced techniques and equipment. We provide personalized treatment plans tailored to your specific needs and aesthetic goals.</p>
        """,
        'ideal_candidates': 'Adults seeking aesthetic improvement with realistic expectations',
        'duration': '30-60 minutes',
        'sessions': 'Varies based on individual needs',
        'downtime': 'Minimal to moderate depending on treatment',
        'recovery_details': 'Follow post-treatment care instructions for optimal results',
        'precautions': ['Follow all pre and post-treatment instructions', 'Avoid sun exposure', 'Use recommended skincare products'],
        'contraindications': 'Pregnancy, breastfeeding, active skin infections, unrealistic expectations'
    }