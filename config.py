# config.py
import os
from pathlib import Path

# base paths
BASE_DIR = Path(__file__).resolve().parent

# model + api
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL_NAME = "gpt-4o-mini"  # change if needed

# structured output / retry behavior
MAX_RETRIES = 3
TEMPERATURE = 0.2


def validateConfig():
    if OPENAI_API_KEY is None:
        raise ValueError("OPENAI_API_KEY is not set in environment variables.")
