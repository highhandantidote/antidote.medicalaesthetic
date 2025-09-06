"""
Script to update the community_reply_routes.py file to add doctor check.
"""
import re

with open('community_reply_routes.py', 'r') as f:
    content = f.read()

# Add check_doctor_status call after is_anonymous in the API endpoint
updated_content = content.replace(
    "        # Handle optional fields\n        if 'is_anonymous' in data:\n            new_reply.is_anonymous = data['is_anonymous']\n        \n        # Handle nested replies",
    "        # Handle optional fields\n        if 'is_anonymous' in data:\n            new_reply.is_anonymous = data['is_anonymous']\n        \n        # Check if the current user is a doctor and mark reply accordingly\n        check_doctor_status(new_reply, current_user.id)\n        \n        # Handle nested replies",
    1  # Replace only the second occurrence
)

with open('community_reply_routes.py', 'w') as f:
    f.write(updated_content)

print("File updated successfully.")
