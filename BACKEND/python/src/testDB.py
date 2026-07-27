import os
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

# --- SECURE CONFIGURATION PATHING ---
# This locates the '.env' file relative to the script's execution path.
# It ensures the system can find its credentials regardless of where it's launched.
BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_path = BASE_DIR / '.env'

# Loading the 'Credentials Vault' into the environment
load_dotenv(dotenv_path=dotenv_path)

def check_connection():
    """
    PRE-FLIGHT DATABASE AUDIT:
    Verifies that the PostgreSQL backend is accessible and that the
    '.env' secrets are correctly mapped.
    """
    # confirming the pathing logic for the demo
    if dotenv_path.exists():
        print(f"✅ Found .env file at: {dotenv_path}")
    else:
        print(f"❌ CRITICAL ERROR: .env configuration missing at {dotenv_path}")

    try:
        # Establishing a handshake with the PostgreSQL database using environment secrets
        connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        print("✅ SUCCESS: DEVS is securely connected to the Forensic Database!")
        
        # Closing the connection immediately—this is just a health check.
        connection.close()
    except Exception as e:
        # Catching connection failures (e.g., wrong password, DB service down)
        print(f"❌ DATABASE CONNECTION FAILED: {e}")

if __name__ == "__main__":
    check_connection()