import os
from warnings import warn

# Telegram secrets
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", None)
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", None)
if TELEGRAM_API_ID is None or TELEGRAM_API_HASH is None:
    warn("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in the environment variables to use Telegram components.")

TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD", "")

# LLM secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
