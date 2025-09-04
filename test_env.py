from dotenv import load_dotenv
import os

load_dotenv()
print("DATABASE_URL:", os.getenv("DATABASE_URL"))
print("DATABASE_PUBLIC_URL:", os.getenv("DATABASE_PUBLIC_URL"))
