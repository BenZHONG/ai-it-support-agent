# config.py

import os

from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Please configure your .env file."
        )

    return api_key


def get_model() -> str:
    return os.getenv("OPENAI_MODEL", "gpt-6-luna")
