from werkzeug.security import generate_password_hash

# Generate hashes for the test passwords
admin_hash = generate_password_hash('admin123')
clinic_hash = generate_password_hash('test123')

print(f"Admin hash: {admin_hash}")
print(f"Clinic hash: {clinic_hash}")