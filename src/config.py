from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_CLEAN = ROOT / "data" / "clean"
DATA_POLICIES = ROOT / "data" / "policies"
DB_PATH = ROOT / "data" / "instamart.db"
OUTPUTS = ROOT / "outputs"
STATE_DIR = ROOT / "state"
SQL_DIR = ROOT / "sql"
DOCS_DIR = ROOT / "docs"

SEED = 42
SNAPSHOT = "2025-10-01 00:00:00"
LAPSE_CUTOFF = "2025-09-01"
K_RANGE = range(2, 9)
CHUNK_WORDS = 40
CHUNK_OVERLAP = 10
MAX_INPUT_TOKENS = 400
TOKEN_BUDGET = 6000
AGENT_MAX_ITERATIONS = 6
AGENT_TOKEN_LIMIT = 6000
AGENT_TIME_LIMIT_SECONDS = 10
