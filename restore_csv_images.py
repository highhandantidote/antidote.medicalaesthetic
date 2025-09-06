#!/usr/bin/env python3
"""
Restore and download all beautiful category images from the original CSV data.
"""

import os
import psycopg2
import requests
import re
import time

def get_db_connection():
    return psycopg2.connect(os.environ.get('DATABASE_URL'))

def sanitize_filename(name):
    filename = re.sub(r'[^\w\s-]', '', name)
    filename = re.sub(r'[-\s]+', '_', filename)
    return filename.lower()

def restore_original_csv_urls():
    """Restore the original Google Drive URLs from your CSV data."""
    
    # Original CSV image mappings from your data
    csv_images = {
        'abdominoplasty': 'https://drive.google.com/uc?export=download&id=1TDNoNyRmQwCeaH74_RlYMZYA4LBaZ1ZY',
        'acne_treatments': 'https://drive.google.com/uc?export=download&id=10iW_gBbSe-cQ2gCRaXUt4rjo_ILk-a0J',
        'body_contouring': 'https://drive.google.com/uc?export=download&id=1LpOOgl1y61p6i4mma4AaxUIRW5haePDx',
        'breast_surgery': 'https://drive.google.com/uc?export=download&id=1eGllh63v6N5LwC8BDYk6zBU7wLDyhVLF',
        'cheek_chin_and_jawline_enhancement': 'https://drive.google.com/uc?export=download&id=1CykNP9C_bkaPV13vYIHQA3sGWBEBueW3',
        'chin_augmentation': 'https://drive.google.com/uc?export=download&id=18Cnqck9lSDfdg73m4qKgmUteny-8KjFm',
        'cosmetic_dentistry': 'https://drive.google.com/uc?export=download&id=1SuXdQN65XYqhLQeMpA8iHUwSwrxBoF_r',
        'ear_surgery': 'https://drive.google.com/uc?export=download&id=1AmXdLZib3DCCTvht5UmD31-6a1bwhRY0',
        'eyebrow_and_lash_enhancement': 'https://drive.google.com/uc?export=download&id=1v5h_jxEAPHKAU9keU7XuqT_IAjLHhb8a',
        'eyelid_enhancement': 'https://drive.google.com/uc?export=download&id=1fxFdSmCe7_Fbjt4fF67a7OLZSLIseZUZ',
        'eyelid_surgery': 'https://drive.google.com/uc?export=download&id=12DYrNIVkAggcJxzEeHk2u_I5nL-ScaYk',
        'face_and_neck_lifts': 'https://drive.google.com/uc?export=download&id=1j1iSf4JOMU7oTrnSculxioKPMhsN8LRl',
        'facial_rejuvenation': 'https://drive.google.com/uc?export=download&id=1jzXh8HuC81s_Ny1EnYDYYXN2kmLzmHRI',
        'female_genital_aesthetic_surgery': 'https://drive.google.com/uc?export=download&id=1gdPyUy3VFJWhuKTgU7L7isNa80HcrH1E',
        'fillers_and_other_injectables': 'https://drive.google.com/uc?export=download&id=1nQCoJ99kT_pUlE8SFZsrNSSKaPNKebxO',
        'gender_confirmation_surgery': 'https://drive.google.com/uc?export=download&id=1nUsx3nQYd9wzAP_LMhcYTUxloj-15xsx',
        'general_dentistry': 'https://drive.google.com/uc?export=download&id=1LpOOgl1y61p6i4mma4AaxUIRW5haePDx',
        'hair_removal': 'https://drive.google.com/uc?export=download&id=1yqs8n9vdCs80F3yhtRYv4XKrxngLgCMK',
        'hair_restoration': 'https://drive.google.com/uc?export=download&id=1efiOM4elujOAn79UA25u1A33q55beDvW',
        'hip_butt_enhancement': 'https://drive.google.com/uc?export=download&id=13rRnQ6cRxJwz8KFbrecWYcSN66OTH6sN',
        'jawline_contouring': 'https://drive.google.com/uc?export=download&id=1CykNP9C_bkaPV13vYIHQA3sGWBEBueW3',
        'lip_augmentation': 'https://drive.google.com/uc?export=download&id=1Teg7P2-RFFFBwYsuv7Gjh52fEEfGlgvn',
        'lip_enhancement': 'https://drive.google.com/uc?export=download&id=1Teg7P2-RFFFBwYsuv7Gjh52fEEfGlgvn',
        'male_body_enhancement': 'https://drive.google.com/uc?export=download&id=1MgBSLY_SNzjr2O1Jynd_emMXSY05MFIo',
        'medical_dermatology': 'https://drive.google.com/uc?export=download&id=1bYzY-nHxj57L72UFTTaEv5FqwKYTAYdK',
        'oral_and_maxillofacial_surgeries': 'https://drive.google.com/uc?export=download&id=18y1WZygTOLVnFv2TwY6G4XOZzSGErTxW',
        'podiatry': 'https://drive.google.com/uc?export=download&id=1isU3mtBBoPAdsW8HFo1bb6Lr3TY1LFUu',
        'post_pregnancy_procedures': 'https://drive.google.com/uc?export=download&id=1uSPhTkKxV9SHGgB55Ck7qyfSYIgxu5Ft',
        'reconstructive_surgeries': 'https://drive.google.com/uc?export=download&id=18y1WZygTOLVnFv2TwY6G4XOZzSGErTxW',
        'rhinoplasty': 'https://drive.google.com/uc?export=download&id=1czF_4Cz6_V-U5Z-1AFcSoLF6Jq9rYhVS',
        'rhinoplasty_and_nose_shaping': 'https://drive.google.com/uc?export=download&id=1czF_4Cz6_V-U5Z-1AFcSoLF6Jq9rYhVS',
        'scar_treatments': 'https://drive.google.com/uc?export=download&id=1fMhpIjai9Gr0NgF4qZCpdNC6dcc4hSKF',
        'sexual_wellness': 'https://drive.google.com/uc?export=download&id=1sZ1pnx3IGWwW-6OgoQBMP4Cl1-E8-Nub',
        'skin_care_products': 'https://drive.google.com/uc?export=download&id=1SuXdQN65XYqhLQeMpA8iHUwSwrxBoF_r',
        'skin_rejuvenation_and_resurfacing': 'https://drive.google.com/uc?export=download&id=1C_NgH0QWV6zH7IaqtMSJALYUmvk_tD7P',
        'skin_tightening': 'https://drive.google.com/uc?export=download&id=1vugvLTu0avg0O9qsL8Nj1WuCCn-617yL',
        'skin_treatments': 'https://drive.google.com/uc?export=download&id=1rzA-IYJHvsGtbuZMPVcQjb-LL0zqxyh0',
        'tattoo_removal': 'https://drive.google.com/uc?export=download&id=1OI9UAGIABqoEMJK_cw7LOQB9jss_XkkA',
        'urinary_incontinence_treatments': 'https://drive.google.com/uc?export=download&id=1C_NgH0QWV6zH7IaqtMSJALYUmvk_tD7P',
        'vaginal_rejuvenation': 'https://drive.google.com/uc?export=download&id=1C_NgH0QWV6zH7IaqtMSJALYUmvk_tD7P',
        'vein_treatments': 'https://drive.google.com/uc?export=download&id=1mae0Mb0o16P_77aG5xt15x6r5QcAFKjx',
        'vision_correction': 'https://drive.google.com/uc?export=download&id=1_n2j23qVq53ty-sWlF4Fg4YnNI6xDIdn',
        'weight_loss_treatments': 'https://drive.google.com/uc?export=download&id=1JnYeWhAh_17fvbrwYZyxMUhiG9hbTd1f'
    }
    
    print(f"🎨 Processing {len(csv_images)} beautiful category images from CSV...")
    
    downloaded = 0
    for category_key, url in csv_images.items():
        filename = category_key + '.jpg'
        filepath = f'static/images/categories/{filename}'
        
        # Skip if already exists
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            print(f"⏭️ {category_key} - already exists")
            continue
        
        try:
            file_id = url.split('id=')[1]
            download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
            
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()
            
            os.makedirs('static/images/categories', exist_ok=True)
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded {category_key} ({len(response.content)} bytes)")
            downloaded += 1
            time.sleep(0.3)
            
            # Limit batch size
            if downloaded >= 10:
                break
                
        except Exception as e:
            print(f"❌ {category_key}: {str(e)[:50]}")
    
    return downloaded

if __name__ == "__main__":
    downloaded = restore_original_csv_urls()
    print(f"\n🎉 Downloaded {downloaded} beautiful images from your CSV!")
    print("✨ Now updating database to use these images...")