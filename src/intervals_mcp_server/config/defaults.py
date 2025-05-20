import os
try:
    from dotenv import load_dotenv

    _ = load_dotenv()
except ImportError:
    # python-dotenv not installed, proceed without it
    pass

class Config:
    API_KEY = os.getenv("API_KEY", "")
    ATHLETE_ID = os.getenv("ATHLETE_ID", "")

settings = Config()    