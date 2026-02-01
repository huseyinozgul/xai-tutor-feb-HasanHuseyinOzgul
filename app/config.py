import os

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")
