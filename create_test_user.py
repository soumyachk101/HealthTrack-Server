import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'healthtracker.settings')
django.setup()

from django.contrib.auth import get_user_model, authenticate

User = get_user_model()

username = 'testsprite'
email = 'testsprite@example.com'
password = 'testpassword123'

if User.objects.filter(username=username).exists():
    print(f"User {username} already exists. Deleting...")
    User.objects.get(username=username).delete()

print(f"Creating user {username}...")
user = User.objects.create_user(
    username=username,
    email=email,
    password=password,
    user_type='patient',
    is_email_verified=True,
    is_approved=True
)

print(f"User {username} created successfully.")

# Verify creation
if User.objects.filter(username=username).exists():
    print("Verification: User exists in DB.")
else:
    print("Verification Failed: User not found in DB.")

# Verify authentication
print("Testing authentication...")
auth_user = authenticate(username=username, password=password)
if auth_user is not None:
    print("Authentication Successful!")
else:
    print("Authentication Failed.")
