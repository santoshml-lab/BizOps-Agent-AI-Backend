import os

from groq import Groq


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()


if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY is not configured."
    )


groq_client = Groq(
    api_key=GROQ_API_KEY
)
