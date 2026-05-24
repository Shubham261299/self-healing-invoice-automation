"""Claude-powered DOM analysis for selector recovery."""
import json
import re
from anthropic import Anthropic
from src.config import ANTHROPIC_API_KEY, CLAUDE_MODEL
from src.logger import get_logger

log = get_logger()
client = Anthropic(api_key=ANTHROPIC_API_KEY)

HEAL_PROMPT = """You are a web automation expert. A Playwright selector has failed on a live page.

**Failed selector:** `{broken_selector}`
**Element purpose:** {purpose}
**Page URL:** {url}

Here is the relevant HTML snippet from the page:
```html
{html_snippet}
```

Analyze the HTML and propose a NEW, robust CSS selector (or Playwright-compatible selector) that targets the intended element. Prefer:
1. Stable attributes (id, name, data-*, aria-label)
2. Semantic tags + text content (e.g., `button:has-text("Login")`)
3. Avoid brittle indices and deep nesting

Respond ONLY in this exact JSON format, no other text:
{{"selector": "your-new-selector-here", "reasoning": "brief 1-line explanation"}}
"""


def heal_selector(broken_selector: str, purpose: str, html_snippet: str, url: str) -> dict | None:
    """Ask Claude to propose a replacement selector. Returns dict or None."""
    log.info(f"[yellow]🩹 Healing selector for: {purpose}[/yellow]")

    # Trim HTML to keep prompt small
    html_snippet = html_snippet[:6000]

    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": HEAL_PROMPT.format(
                    broken_selector=broken_selector,
                    purpose=purpose,
                    html_snippet=html_snippet,
                    url=url,
                ),
            }],
        )
        text = message.content[0].text.strip()

        # Extract JSON (model may wrap in code fences)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            log.error(f"[red]Could not parse Claude response: {text}[/red]")
            return None

        result = json.loads(match.group(0))
        log.info(f"[green]✓ Proposed selector:[/green] [cyan]{result['selector']}[/cyan]")
        log.info(f"  Reasoning: {result.get('reasoning', 'n/a')}")
        return result

    except Exception as e:
        log.error(f"[red]Healing failed: {e}[/red]")
        return None