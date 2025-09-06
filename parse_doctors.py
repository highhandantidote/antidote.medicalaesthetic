#!/usr/bin/env python3
"""
Parse the doctors CSV file and create a properly formatted version
"""
import csv
import os
import json

# Input and output files
INPUT_FILE = "attached_assets/doctors profiles - Sheet1.csv"
OUTPUT_FILE = "attached_assets/formatted_doctors.csv"

# Function to extract proper field values
def extract_field_values(row):
    # Define the expected column structure based on the header
    columns = [
        "Doctor Name", "Specialization", "Experience", "City", "State", 
        "Hospital Name", "Consultation Fee", "Description", "License Number", 
        "Qualifications", "Address", "Phone", "Email", "Procedures Offered", 
        "Special Interests", "Education History", "Certifications", "Is Available"
    ]
    
    # Create a dictionary with default values
    result = {col: "" for col in columns}
    
    # Fill in values from the row
    for i, col in enumerate(columns):
        if i < len(row):
            # Clean the value (remove quotes)
            value = row[i].strip().strip('"')
            result[col] = value
    
    return result

# Main function to convert the CSV
def convert_csv():
    # Read the input as raw text
    with open(INPUT_FILE, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Extract the header
    header = lines[0].strip().strip('"').split(',')
    
    # Process the rows
    rows = []
    for i in range(1, len(lines)):
        line = lines[i].strip().strip('"')
        
        # Skip empty lines
        if not line:
            continue
            
        # Split by commas, but be careful about quotes
        row_values = []
        current_value = ""
        in_quotes = False
        
        for char in line:
            if char == '"':
                in_quotes = not in_quotes
            elif char == ',' and not in_quotes:
                row_values.append(current_value)
                current_value = ""
            else:
                current_value += char
        
        # Add the last value
        if current_value:
            row_values.append(current_value)
        
        # Process the row
        processed_row = extract_field_values(row_values)
        rows.append(processed_row)
    
    # Write the cleaned data to the output file
    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Processed {len(rows)} doctors and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    convert_csv()