# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env in the project root
load_dotenv()

BING_SUBSCRIPTION_KEY = os.getenv("BING_SUBSCRIPTION_KEY")
BING_SEARCH_URL = os.getenv("BING_SEARCH_URL", "https://api.bing.microsoft.com/v7.0/search")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "summarizer")
COURT_LISTENER_API_KEY = os.getenv("COURT_LISTENER_API_KEY")
DOL_API_KEY = os.getenv("DOL_API_KEY")
JOBS_API_KEY = os.getenv("JOBS_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")
SEC_EXTRACT_API_URL = os.getenv("SEC_EXTRACT_API_URL", "https://api.sec-api.io/extractor")

OLLAMA_SERVER_URL = os.getenv("OLLAMA_SERVER_URL", "http://localhost:11434")

