"""Playwright-driven invoice automation with self-healing."""
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from src.config import (
    LOGIN_URL, TABLES_URL, DOWNLOAD_URL,
    PORTAL_USERNAME, PORTAL_PASSWORD,
    SELECTORS, HEADLESS, TIMEOUT_MS, MAX_HEAL_RETRIES,
    SCREENSHOTS_DIR,
)
from src.self_healer import heal_selector
from src.logger import get_logger
from src.ocr_validator import validate_text_present

log = get_logger()


class InvoiceBot:
    def __init__(self, simulate_breakage: bool = False):
        self.simulate_breakage = simulate_breakage
        self.selectors = SELECTORS["broken"] if simulate_breakage else SELECTORS["healthy"]
        self.heal_log = []  # Track every heal event for the dashboard

    def _try_selector(self, page, key: str, action: str = "fill", value: str = None):
        """
        Attempt an action on a selector. If it fails, ask Claude for a new one.
        action: 'fill' | 'click' | 'wait'
        """
        original = self.selectors[key]

        for attempt in range(MAX_HEAL_RETRIES + 1):
            try:
                selector = self.selectors[key]
                log.info(f"  → Attempting [cyan]{action}[/cyan] on [magenta]{selector}[/magenta] (purpose: {key})")

                if action == "fill":
                    page.fill(selector, value, timeout=TIMEOUT_MS)
                elif action == "click":
                    page.click(selector, timeout=TIMEOUT_MS)
                elif action == "wait":
                    page.wait_for_selector(selector, timeout=TIMEOUT_MS)
                return True

            except PWTimeout:
                log.warning(f"[yellow]⚠ Selector failed:[/yellow] {self.selectors[key]}")
                if attempt >= MAX_HEAL_RETRIES:
                    log.error(f"[red]✗ Gave up healing '{key}' after {attempt} attempts[/red]")
                    return False

                # Heal
                html = page.content()
                fix = heal_selector(
                    broken_selector=self.selectors[key],
                    purpose=key,
                    html_snippet=html,
                    url=page.url,
                )
                if not fix:
                    return False

                # Log + swap selector
                self.heal_log.append({
                    "purpose": key,
                    "broken": self.selectors[key],
                    "healed": fix["selector"],
                    "reasoning": fix.get("reasoning", ""),
                })
                self.selectors[key] = fix["selector"]
                log.info(f"[green]🔄 Retrying with healed selector...[/green]")

    def login(self, page) -> bool:
        log.info("[bold]→ Step 1: Login[/bold]")
        page.goto(LOGIN_URL)
        if not self._try_selector(page, "username_input", "fill", PORTAL_USERNAME):
            return False
        if not self._try_selector(page, "password_input", "fill", PORTAL_PASSWORD):
            return False
        if not self._try_selector(page, "login_button", "click"):
            return False

        # Wait for redirect + flash message to appear
        try:
            page.wait_for_url("**/secure", timeout=TIMEOUT_MS)
            page.wait_for_selector("#flash", timeout=TIMEOUT_MS)
        except PWTimeout:
            log.warning("[yellow]Post-login redirect didn't happen as expected[/yellow]")

        page.wait_for_load_state("networkidle")

        shot = SCREENSHOTS_DIR / "post_login.png"
        page.screenshot(path=str(shot), full_page=True)

        # Belt + suspenders: check URL AND OCR
        url_ok = "/secure" in page.url
        ocr_ok = validate_text_present(shot, "secure area")
        ok = url_ok or ocr_ok  # Either signal is enough

        log.info(f"  URL check: {'✓' if url_ok else '✗'} ({page.url})")
        log.info(f"  OCR check: {'✓' if ocr_ok else '✗'}")
        log.info(f"[{'green' if ok else 'red'}]{'✓' if ok else '✗'} Login {'successful' if ok else 'failed'}[/]")
        return ok

    def list_invoices(self, page) -> list[dict]:
        log.info("[bold]→ Step 2: Scrape invoice table[/bold]")
        page.goto(TABLES_URL)
        if not self._try_selector(page, "invoice_table", "wait"):
            return []

        # The rows selector might also be broken — try it, heal if needed
        rows = page.query_selector_all(self.selectors["invoice_rows"])

        if not rows:
            # Selector technically didn't error but returned empty — likely stale
            log.warning(f"[yellow]⚠ Row selector returned 0 results: {self.selectors['invoice_rows']}[/yellow]")
            log.info("[yellow]🩹 Healing row selector...[/yellow]")
            from src.self_healer import heal_selector
            fix = heal_selector(
                broken_selector=self.selectors["invoice_rows"],
                purpose="invoice_rows",
                html_snippet=page.content(),
                url=page.url,
            )
            if fix:
                self.heal_log.append({
                    "purpose": "invoice_rows",
                    "broken": self.selectors["invoice_rows"],
                    "healed": fix["selector"],
                    "reasoning": fix.get("reasoning", ""),
                })
                self.selectors["invoice_rows"] = fix["selector"]
                rows = page.query_selector_all(self.selectors["invoice_rows"])

        invoices = []
        for r in rows:
            cells = r.query_selector_all("td")
            if len(cells) >= 6:
                invoices.append({
                    "last_name": cells[0].inner_text(),
                    "first_name": cells[1].inner_text(),
                    "email": cells[2].inner_text(),
                    "due": cells[3].inner_text(),
                    "web_site": cells[4].inner_text() if len(cells) > 4 else "",
                })
        log.info(f"  Found [cyan]{len(invoices)}[/cyan] invoice rows.")
        return invoices

    def download_sample(self, page) -> bool:
        log.info("[bold]→ Step 3: Download invoice sample[/bold]")
        page.goto(DOWNLOAD_URL)
        try:
            with page.expect_download(timeout=TIMEOUT_MS) as dl_info:
                page.click("a:has-text('.txt')", timeout=TIMEOUT_MS)
            download = dl_info.value
            target = SCREENSHOTS_DIR.parent / "downloads" / download.suggested_filename
            download.save_as(str(target))
            log.info(f"[green]✓ Downloaded:[/green] {target.name}")
            return True
        except Exception as e:
            log.error(f"[red]Download failed: {e}[/red]")
            return False

    def run(self) -> dict:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            result = {
                "login_ok": False,
                "invoices_found": 0,
                "download_ok": False,
                "heal_events": [],
            }

            try:
                result["login_ok"] = self.login(page)
                if result["login_ok"]:
                    invoices = self.list_invoices(page)
                    result["invoices_found"] = len(invoices)
                    result["download_ok"] = self.download_sample(page)
            finally:
                result["heal_events"] = self.heal_log
                browser.close()

            return result