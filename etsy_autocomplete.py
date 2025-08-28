from playwright.sync_api import sync_playwright
import csv, time
from datetime import datetime

SEEDS = [
    "james webb space telescope wall art"
]

OUTPUT_CSV = "etsy_autocomplete_results.csv"

def scrape_seed(page, seed):
    # Go to homepage to ensure clean state each time (resets suggestions)
    page.goto("https://www.etsy.com/", wait_until="domcontentloaded")
    
    # Accept cookies/consent banners if present (selectors can vary by region)
    try:
        # Common consent button patterns; ignore if not present
        for sel in [
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button[aria-label="Accept"]',
            '[data-testid="gdpr-banner-accept"]'
        ]:
            if page.locator(sel).first.is_visible():
                page.locator(sel).first.click()
                break
    except:
        pass

    # Try multiple search input selectors - Etsy's selectors change frequently
    search_selectors = [
        'input[data-id="search-query"]',
        'input[name="search_query"]',
        'input[placeholder*="search"]',
        'input[aria-label*="search"]',
        'input[type="search"]',
        '[data-testid="search-input"]',
        'input[data-ui="search-input"]'
    ]
    
    search_input = None
    for selector in search_selectors:
        try:
            if page.locator(selector).is_visible(timeout=3000):
                search_input = page.locator(selector)
                print(f"Found search input with selector: {selector}")
                break
        except:
            continue
    
    if not search_input:
        print("Could not find search input - taking screenshot for debugging")
        page.screenshot(path="etsy_debug.png")
        return []

    # Focus search input and type slowly (human-like)
    search_input.click()
    search_input.fill("")
    search_input.type(seed, delay=50)

    # Wait for suggestion container to appear; selectors can change. These are common patterns:
    suggestion_selectors = [
        # Newer Etsy UI often uses role="listbox" with options
        '[role="listbox"] [role="option"]',
        # Legacy class-based fallbacks
        'ul[data-id="search-suggestions"] li',
        'div[data-region="search-suggestions"] li',
        '[data-testid="search-suggestions"] li',
        '.search-suggestions li',
        '[class*="suggestion"]'
    ]

    suggestions = []
    start = time.time()
    while time.time() - start < 5 and not suggestions:
        for sel in suggestion_selectors:
            if page.locator(sel).count() > 0:
                items = page.locator(sel)
                count = items.count()
                for i in range(count):
                    text = items.nth(i).inner_text().strip()
                    if text and text not in suggestions:
                        suggestions.append(text)
        time.sleep(0.2)

    # As a fallback, hit "ArrowDown" a few times to force list render
    if not suggestions:
        for _ in range(3):
            page.keyboard.press("ArrowDown")
            time.sleep(0.2)
        for sel in suggestion_selectors:
            if page.locator(sel).count() > 0:
                items = page.locator(sel)
                for i in range(items.count()):
                    text = items.nth(i).inner_text().strip()
                    if text and text not in suggestions:
                        suggestions.append(text)

    return suggestions

def main():
    timestamp = datetime.utcnow().isoformat()
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False to see what's happening
        context = browser.new_context(locale="en-US")
        page = context.new_page()

        for seed in SEEDS:
            try:
                suggs = scrape_seed(page, seed)
                for s in suggs:
                    rows.append({"timestamp_utc": timestamp, "seed": seed, "suggestion": s})
                print(f"[OK] {seed} → {len(suggs)} suggestions")
                print(f"Suggestions: {suggs}")
            except Exception as e:
                print(f"[ERR] {seed}: {e}")

        browser.close()

    # Write CSV (append-safe)
    header = ["timestamp_utc", "seed", "suggestion"]
    try:
        # Append if file exists, otherwise create
        write_header = False
        try:
            open(OUTPUT_CSV, "r").close()
        except:
            write_header = True
        with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            if write_header:
                writer.writeheader()
            writer.writerows(rows)
    except Exception as e:
        print(f"[ERR] writing CSV: {e}")

if __name__ == "__main__":
    main()
