import os
from pathlib import Path
from dotenv import load_dotenv

# Load backend/.env specifically
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=env_path)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
DATABASE_URL = os.getenv("DATABASE_URL")


def check_gemini() -> bool:
    print("[GEMINI] Checking connection...")
    if not GEMINI_API_KEY or not GEMINI_MODEL:
        print("[GEMINI] FAILED: GEMINI_API_KEY or GEMINI_MODEL is missing in backend/.env")
        return False

    try:
        from google import genai

        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents="Reply with the single word: ready",
        )
        reply = (response.text or "").strip()
        print(f"[GEMINI] OK: Received reply: {reply}")
        return True
    except Exception as e:
        # Never leak key in output; report exception type only
        print(f"[GEMINI] FAILED: Encountered error during request ({type(e).__name__})")
        return False


def check_database() -> bool:
    print("[DATABASE] Checking connection...")
    if not DATABASE_URL:
        print("[DATABASE] FAILED: DATABASE_URL is missing in backend/.env")
        return False

    try:
        from sqlalchemy import create_engine, text

        # Create engine and test connection with SELECT 1
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            if result == 1:
                print("[DATABASE] OK: Successfully executed SELECT 1")
                return True
            else:
                print(f"[DATABASE] FAILED: Unexpected query result ({result})")
                return False
    except Exception as e:
        # Never leak connection string, credentials or host in output; report exception type only
        print(f"[DATABASE] FAILED: Unable to connect or execute query ({type(e).__name__})")
        return False


def main():
    print("=== Checking Quoteproof Backend Connections ===")
    gemini_ok = check_gemini()
    db_ok = check_database()
    print("===============================================")
    if gemini_ok and db_ok:
        print("Summary: All connection checks PASSED.")
    else:
        print("Summary: One or more connection checks FAILED.")


if __name__ == "__main__":
    main()
