#!/usr/bin/env python3
"""
Simple Bulk Package Import
Process the CSV and generate packages using the existing system.
"""
import csv
import json
import re
from datetime import datetime

def parse_price(price_str):
    """Parse price from string format."""
    if 'per' in price_str.lower():
        numbers = re.findall(r'\d+', price_str.replace(',', ''))
        return float(numbers[0]) if numbers else 0.0
    else:
        clean_price = price_str.replace(',', '').replace('₹', '').strip()
        try:
            return float(clean_price)
        except ValueError:
            return 0.0

def process_packages():
    """Process the CSV file and print SQL commands."""
    csv_file = 'attached_assets/Neoskin - Sheet1 (1)_1756413049898.csv'
    
    print("-- Generated SQL for bulk package import")
    print("-- Run these commands in your database tool")
    print()
    
    with open(csv_file, 'r', encoding='utf-8') as file:
        csv_reader = csv.DictReader(file)
        
        for row_num, row in enumerate(csv_reader, 1):
            try:
                # Extract data
                package_name = row['package_name'].strip()
                actual_treatment = row['actual_treatment_name'].strip()
                price = parse_price(row['price'])
                discount_percentage = int(row['discount_percentage'])
                price_discounted = price * (100 - discount_percentage) / 100
                
                # Generate slug
                slug = re.sub(r'[^a-zA-Z0-9\s]', '', package_name.lower())
                slug = re.sub(r'\s+', '-', slug.strip())
                
                # Generate category
                name_lower = f"{package_name} {actual_treatment}".lower()
                if any(word in name_lower for word in ['facial', 'glow', 'hydra', 'oxygen', 'peel']):
                    category = 'Facial'
                elif any(word in name_lower for word in ['hair', 'scalp', 'prp', 'gfc', 'transplant']):
                    category = 'Hair Restoration'
                elif any(word in name_lower for word in ['botox', 'filler', 'dermal', 'thread']):
                    category = 'Injectable'
                elif any(word in name_lower for word in ['laser', 'bright', 'lift', 'erase']):
                    category = 'Laser'
                elif any(word in name_lower for word in ['brow', 'ombre', 'microblading', 'pigmentation']):
                    category = 'Pigmentation'
                else:
                    category = 'Aesthetic Medicine'
                
                # Generate description
                description = f"Professional {actual_treatment.lower()} treatment with expert care and proven results. Advanced technique ensuring patient satisfaction and optimal outcomes."
                
                # Generate SQL
                sql = f"""
INSERT INTO packages (
    clinic_id, title, slug, description, actual_treatment_name, 
    price_actual, price_discounted, discount_percentage, category,
    duration, downtime, anesthetic_type, aftercare_kit,
    is_active, created_at
) VALUES (
    2225, 
    '{package_name.replace("'", "''")}', 
    '{slug}', 
    '{description}',
    '{actual_treatment.replace("'", "''")}',
    {price}, 
    {price_discounted:.2f}, 
    {discount_percentage}, 
    '{category}',
    '45-60 minutes',
    'Minimal (24-48 hours)',
    'Topical anesthetic',
    'Post-treatment care kit',
    true,
    NOW()
);"""
                
                print(sql)
                print()
                
            except Exception as e:
                print(f"-- Error processing row {row_num}: {e}")

if __name__ == '__main__':
    process_packages()