"""Excel I/O for invoice tracking."""
from datetime import datetime
from pathlib import Path
import pandas as pd
from src.config import INPUT_XLSX, OUTPUT_XLSX
from src.logger import get_logger

log = get_logger()


def ensure_input_exists() -> None:
    """Create a sample input file if missing."""
    if INPUT_XLSX.exists():
        return
    sample = pd.DataFrame({
        "invoice_id": [f"INV-{i:04d}" for i in range(1, 6)],
        "vendor": ["Acme Corp", "Globex", "Initech", "Umbrella", "Stark Ind"],
        "amount": [1250.00, 890.50, 4200.00, 750.25, 9999.99],
        "status": ["PENDING"] * 5,
    })
    sample.to_excel(INPUT_XLSX, index=False)
    log.info(f"Created sample input: {INPUT_XLSX}")


def load_invoices() -> pd.DataFrame:
    ensure_input_exists()
    return pd.read_excel(INPUT_XLSX)


def append_result(row: dict) -> None:
    """Append one run result to the output Excel."""
    row["timestamp"] = datetime.now().isoformat(timespec="seconds")
    df_new = pd.DataFrame([row])

    if OUTPUT_XLSX.exists():
        df_old = pd.read_excel(OUTPUT_XLSX)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_excel(OUTPUT_XLSX, index=False)