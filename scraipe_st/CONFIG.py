import os
import logging
# Telegram secrets
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_PASSWORD = os.getenv("TELEGRAM_PASSWORD", "")

# LLM secrets
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Reddit secrets
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")

unconfigured = []
required = ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "OPENAI_API_KEY", "GEMINI_API_KEY", "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]
for var_name in required:
    if not globals()[var_name]:
        unconfigured.append(var_name)
if len(unconfigured) > 0:
    logging.warning(f"The following credentials are not configured in the environment. They must be configured in the GUI.\n {', '.join(unconfigured)}")