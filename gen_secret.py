import secrets

secret_key = secrets.token_urlsafe(32)  # Generates a 32-character random string
print(secret_key)  # Output the key and copy it to your .env file