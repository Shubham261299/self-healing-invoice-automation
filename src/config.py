"""Centralized configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
DOWNLOADS_DIR = ROOT / "downloads"
SCREENSHOTS_DIR = ROOT / "screenshots"
LOGS_DIR = ROOT / "logs"

INPUT_XLSX = DATA_DIR / "invoices_to_process.xlsx"
OUTPUT_XLSX = DATA_DIR / "invoice_status.xlsx"

# Create dirs on import
for d in (DATA_DIR, DOWNLOADS_DIR, SCREENSHOTS_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- Anthropic ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = "claude-sonnet-4-5"

# --- Tesseract (Windows path override) ---
TESSERACT_CMD = os.getenv("TESSERACT_CMD")

# --- Target portal ---
PORTAL_BASE = "https://the-internet.herokuapp.com"
LOGIN_URL = f"{PORTAL_BASE}/login"
TABLES_URL = f"{PORTAL_BASE}/tables"
DOWNLOAD_URL = f"{PORTAL_BASE}/download"

PORTAL_USERNAME = os.getenv("PORTAL_USERNAME", "tomsmith")
PORTAL_PASSWORD = os.getenv("PORTAL_PASSWORD", "SuperSecretPassword!")

# --- Selectors (the "fragile" layer that self-heals) ---
# When SIMULATE_BREAKAGE is True, we use intentionally-wrong selectors
# to demonstrate Claude's recovery capability.
SELECTORS = {
    "healthy": {
        "username_input": "#username",
        "password_input": "#password",
        "login_button": "button[type='submit']",
        "flash_message": "#flash",
        "invoice_table": "#table1",
        "invoice_rows": "#table1 tbody tr",
    },
    "broken": {
        # These selectors don't exist — Claude must heal them
        "username_input": "#user-name-field-v2",
        "password_input": "#pwd-input-new",
        "login_button": "button.login-submit-btn",
        "flash_message": ".alert-banner",
        "invoice_table": ".invoices-grid",
        "invoice_rows": ".invoices-grid .row-item",
    },
}

# --- Runtime ---
HEADLESS = False  # Show browser during demo
TIMEOUT_MS = 8000
MAX_HEAL_RETRIES = 2