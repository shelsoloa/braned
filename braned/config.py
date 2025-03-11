import os

import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

DEFAULT_PID_FILE = "/var/run/braned.pid"
DEFAULT_LOG_FILE = "/var/log/braned.log"
