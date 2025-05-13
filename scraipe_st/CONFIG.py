import os
from warnings import warn

# Telegram secrets
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD", "")

# LLM secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

unconfigured = []
for var_name in ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "OPENAI_API_KEY", "GEMINI_API_KEY"]:
    if not globals()[var_name]:
        unconfigured.append(var_name)
if len(unconfigured) > 0:
    warn(f"The following credentials are not configured. They must be configured in the GUI.\n {', '.join(unconfigured)}")