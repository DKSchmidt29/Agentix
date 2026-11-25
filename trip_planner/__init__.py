from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]

# Load the repo-level .env on import so every script and notebook that uses this package gets the keys,
# regardless of the working directory.
load_dotenv(REPO_ROOT / '.env', override=True)
