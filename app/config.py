import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://localhost:5432/snc_training")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-a-random-secret")
MAX_USERS = int(os.getenv("MAX_USERS", "1000"))
