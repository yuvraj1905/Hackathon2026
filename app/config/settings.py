import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    COMPANY_NAME = "GeekyAnts Pvt Ltd"
    COMPANY_LOGO_URL = "https://geekyants.com/images/logo/logo-dark.svg"
    COMPANY_EMAIL = "[info@geekyants.com](mailto:info@geekyants.com)"
    COMPANY_PHONE = "+91 8043058884"
    COMPANY_ADDRESS = "Bangalore, India"
    GOOGLE_SERVICE_ACCOUNT_FILE = "app/credentials/service-account.json"
    GOOGLE_DOCS_FOLDER_ID = "1cSlY8JKnaEEQNdtrDRkaOibHzvBXIdNz"
    DEFAULT_PROPOSAL_SHARE_EMAIL = "yuvrajkumar2509@gmail.com"

    # ── Email pipeline (SendGrid) ───────────────────────────────────
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_WEBHOOK_SECRET: str = os.getenv("SENDGRID_WEBHOOK_SECRET", "")
    ESTIMATES_FROM_EMAIL: str = os.getenv("ESTIMATES_FROM_EMAIL", "estimates@geekyants.com")
    SALES_TEAM_EMAIL: str = os.getenv("SALES_TEAM_EMAIL", "sales@geekyants.com")
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")


settings = Settings()
