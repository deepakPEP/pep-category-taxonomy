import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3.5:9b-mlx")
INPUT_DIR = os.getenv("INPUT_DIR", "input")
PHASE1_BATCH_SIZE = int(os.getenv("PHASE1_BATCH_SIZE", 100))
PHASE2_BATCH_SIZE = int(os.getenv("PHASE2_BATCH_SIZE", 25))
PHASE4_BATCH_SIZE = int(os.getenv("PHASE4_BATCH_SIZE", 20))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
MAX_WORKERS = int(os.getenv("MAX_WORKERS", 1))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 600))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", 5))
RETRY_DELAY_SECONDS = int(os.getenv("RETRY_DELAY_SECONDS", 10))

PHASE1_OUTPUT_DIR = "output/phase1"
PHASE2_OUTPUT_DIR = "output/phase2"
PHASE3_OUTPUT_DIR = "output/phase3"
PHASE4_OUTPUT_DIR = "output/phase4"
PHASE5_OUTPUT_DIR = "output/phase5"
STATE_DIR = "output/state"
LOGS_DIR = "output/logs"
METRICS_DIR = "output/metrics"

TAXONOMY_PROMPT_FILE = "prompts/taxonomy_prompt.txt"
NORMALIZE_PROMPT_FILE = "prompts/normalize_prompt.txt"
