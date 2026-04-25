import os
import secrets

from dotenv import load_dotenv

load_dotenv()

ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "changeme")
SESSION_SECRET: str = os.getenv("SESSION_SECRET", secrets.token_hex(32))
SESSION_MAX_AGE: int = 60 * 60 * 8  # 8 hours
