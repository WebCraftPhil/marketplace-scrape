from playwright.sync_api import sync_playwright
import csv, time
from datetime import datetime

# Strategic search terms for high-demand, moderate-competition opportunities
SEEDS = [
    # Japanese Art & Culture (High demand, can use public domain ukiyo-e)
    "japanese wall art", "ukiyo-e prints", "japanese woodblock prints", "mount fuji art",
    "cherry blossom art", "japanese garden prints", "zen wall art", "japanese calligraphy art",
    "tokyo city art", "kyoto temple art", "japanese wave art", "hokusai prints",
    
    # National Parks (Public domain opportunities, high demand)
    "national parks posters", "yosemite wall art", "yellowstone posters", "grand canyon art",
    "national park vintage posters", "park ranger art", "nature conservation posters",
    "outdoor adventure posters", "hiking trail maps", "camping wall art",
    
    # Vintage Travel (Excellent public domain opportunities)
    "vintage travel posters", "old travel advertisements", "retro travel art",
    "vintage airline posters", "old cruise ship posters", "vintage destination art",
    "classic travel prints", "old tourism posters", "vintage city posters",
    
    # Old Maps & Cartography (Perfect for public domain)
    "old city maps", "vintage map prints", "antique map posters", "historical maps",
    "old world maps", "vintage atlas prints", "antique cartography", "old street maps",
    "vintage city plans", "historical cartography art",
    
    # Vintage Botanical & Scientific (Excellent public domain)
    "vintage botanical prints", "old scientific illustrations", "vintage medical art",
    "antique flower prints", "vintage herbarium", "old anatomy prints", "vintage butterfly art",
    "antique bird prints", "vintage natural history", "old botanical drawings",
    
    # Classic Literature & Books (Public domain goldmine)
    "classic literature posters", "old book covers", "vintage book illustrations",
    "shakespeare quotes art", "classic novel posters", "vintage library art",
    "old manuscript art", "classic poetry posters", "vintage bookplate art",
    
    # Art Nouveau & Art Deco (Public domain style)
    "art nouveau posters", "art deco prints", "vintage art nouveau", "deco wall art",
    "vintage advertising art", "old poster art", "retro advertising prints",
    "vintage typography art", "old logo art", "vintage brand posters",
    
    # Vintage Photography (Public domain opportunities)
    "vintage photographs", "old family photos", "historical photography",
    "vintage portrait art", "old street photography", "vintage landscape photos",
    "antique photo art", "vintage documentary photos", "old architectural photos",
    
    # Vintage Fashion & Style (Public domain)
    "vintage fashion posters", "old fashion illustrations", "retro style art",
    "vintage beauty ads", "old magazine covers", "vintage pinup art",
    "retro fashion prints", "vintage clothing art", "old style posters",
    
    # Vintage Transportation (Public domain)
    "vintage car posters", "old train art", "vintage airplane posters",
    "retro transportation art", "vintage motorcycle art", "old ship posters",
    "vintage vehicle art", "retro travel posters", "old transportation prints",
    
    # Vintage Americana (Public domain)
    "vintage american posters", "old western art", "vintage cowboy art",
    "retro american prints", "vintage patriotic art", "old american advertisements",
    "vintage baseball art", "retro american style", "vintage american life",
    
    # Vintage European (Public domain)
    "vintage european art", "old french posters", "vintage italian art",
    "retro european prints", "vintage british art", "old german posters",
    "vintage paris art", "retro european style", "vintage european life",
    
    # Trending Space/Science (from your original)
    "james webb space telescope wall art", "nasa space posters", "astronomy wall art",
    "galaxy wall prints", "nebula posters", "solar system art",
    
    # High-Demand Personalized (Moderate competition)
    "personalized name art", "custom family tree", "birthday gift personalized",
    "anniversary gift custom", "wedding guest book", "baby milestone cards",
    "pet portrait custom", "housewarming gift", "teacher appreciation gift"
]

OUTPUT_CSV = "etsy_market_research.csv"

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

    # Fill in the search term and submit
    search_input.click()
    search_input.fill(seed)
    
    # Try to find and click the search button
    search_button_selectors = [
        'button[type="submit"]',
        'button[aria-label*="search"]',
        'button:has-text("Search")',
        'input[type="submit"]',
        '[data-testid="search-button"]'
    ]
    
    search_submitted = False
    for button_sel in search_button_selectors:
        try:
            if page.locator(button_sel).is_visible():
                page.locator(button_sel).click()
                search_submitted = True
                print(f"Clicked search button with selector: {button_sel}")
                break
        except:
            continue
    
    # If no button found, try pressing Enter
    if not search_submitted:
        search_input.press("Enter")
        print("Pressed Enter to submit search")
    
    # Wait for search results page to load
    page.wait_for_load_state("networkidle", timeout=10000)
    time.sleep(3)
    
    # Extract related terms from search results page
    suggestions = []
    
    # Look for related search terms, filters, or suggestions on the results page
    related_selectors = [
        'a[href*="search"]',  # Search links
        '[class*="related"]',  # Related terms
        '[class*="suggestion"]',  # Suggestions
        '[class*="filter"]',  # Filter options
        'span[class*="tag"]',  # Tags
        'a[class*="category"]'  # Category links
    ]
    
    # Filter out common navigation and non-relevant terms
    skip_terms = [
        'home', 'shop', 'cart', 'account', 'help', 'sign', 'login', 'register',
        'more like this', 'all filters', 'special offers', 'free shipping', 'on sale',
        'personalizable', 'price', 'enter minimum', 'enter maximum', 'apply',
        'sort by', 'relevance', 'newest', 'price low', 'price high'
    ]
    
    for sel in related_selectors:
        try:
            elements = page.locator(sel)
            count = elements.count()
            if count > 0:
                print(f"Found {count} elements with selector: {sel}")
                for i in range(min(count, 15)):  # Increased limit
                    text = elements.nth(i).inner_text().strip()
                    if text and text not in suggestions and len(text) > 3 and len(text) < 100:
                        # Filter out common navigation text and irrelevant terms
                        text_lower = text.lower()
                        if not any(skip in text_lower for skip in skip_terms):
                            # Prioritize terms that look like product categories or search terms
                            if any(keyword in text_lower for keyword in ['print', 'poster', 'art', 'gift', 'personalized', 'custom', 'vintage', 'wall', 'decor']):
                                suggestions.append(text)
                            else:
                                suggestions.append(text)
        except Exception as e:
            continue
    
    # If no suggestions found, take a screenshot for debugging
    if not suggestions:
        print("No related terms found - taking screenshot for debugging")
        page.screenshot(path=f"etsy_search_results_{seed.replace(' ', '_')}.png")
        
        # Get page title and URL for debugging
        title = page.title()
        url = page.url()
        print(f"Search results page: {title}")
        print(f"URL: {url}")
    
    return suggestions

def analyze_competition_level(seed):
    """Simple heuristic to estimate competition level based on search term"""
    high_competition_keywords = ['gift', 'personalized', 'custom', 'print', 'poster']
    moderate_competition_keywords = ['vintage', 'antique', 'classic', 'art', 'decor']
    low_competition_keywords = ['niche', 'specific', 'unique', 'rare']
    
    seed_lower = seed.lower()
    
    high_count = sum(1 for keyword in high_competition_keywords if keyword in seed_lower)
    moderate_count = sum(1 for keyword in moderate_competition_keywords if keyword in seed_lower)
    low_count = sum(1 for keyword in low_competition_keywords if keyword in seed_lower)
    
    if high_count > moderate_count and high_count > low_count:
        return "High"
    elif moderate_count > high_count and moderate_count > low_count:
        return "Moderate"
    elif low_count > high_count and low_count > moderate_count:
        return "Low"
    else:
        return "Moderate"

def main():
    timestamp = datetime.utcnow().isoformat()
    rows = []

    with sync_playwright() as p:
        # Use a more realistic browser setup
        browser = p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        context = browser.new_context(
            locale="en-US",
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        # Add extra headers to appear more human
        page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        for seed in SEEDS:
            try:
                suggs = scrape_seed(page, seed)
                competition_level = analyze_competition_level(seed)
                
                for s in suggs:
                    rows.append({
                        "timestamp_utc": timestamp, 
                        "seed": seed, 
                        "suggestion": s,
                        "competition_level": competition_level,
                        "category": categorize_term(seed)
                    })
                print(f"[OK] {seed} → {len(suggs)} suggestions (Competition: {competition_level})")
                print(f"Suggestions: {suggs[:5]}...")  # Show first 5
                
                # Add a delay between searches
                time.sleep(3)
            except Exception as e:
                print(f"[ERR] {seed}: {e}")

        browser.close()

    # Write CSV with enhanced headers
    header = ["timestamp_utc", "seed", "suggestion", "competition_level", "category"]
    try:
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n✅ Research complete! Saved {len(rows)} data points to {OUTPUT_CSV}")
    except Exception as e:
        print(f"[ERR] writing CSV: {e}")

def categorize_term(term):
    """Categorize search terms for better analysis"""
    term_lower = term.lower()
    
    if any(word in term_lower for word in ['japanese', 'ukiyo-e', 'hokusai', 'fuji', 'cherry', 'zen', 'tokyo', 'kyoto']):
        return "Japanese Art"
    elif any(word in term_lower for word in ['national park', 'yosemite', 'yellowstone', 'grand canyon', 'park ranger', 'hiking', 'camping']):
        return "National Parks"
    elif any(word in term_lower for word in ['vintage travel', 'retro travel', 'airline', 'cruise', 'tourism', 'destination']):
        return "Vintage Travel"
    elif any(word in term_lower for word in ['map', 'cartography', 'atlas', 'street map', 'city plan']):
        return "Maps/Cartography"
    elif any(word in term_lower for word in ['botanical', 'scientific', 'medical', 'anatomy', 'butterfly', 'bird', 'natural history', 'herbarium']):
        return "Botanical/Scientific"
    elif any(word in term_lower for word in ['literature', 'book', 'shakespeare', 'novel', 'library', 'manuscript', 'poetry']):
        return "Literature/Books"
    elif any(word in term_lower for word in ['art nouveau', 'art deco', 'deco', 'advertising', 'typography', 'logo', 'brand']):
        return "Art Nouveau/Deco"
    elif any(word in term_lower for word in ['photograph', 'photo', 'portrait', 'street photography', 'landscape photo', 'architectural']):
        return "Vintage Photography"
    elif any(word in term_lower for word in ['fashion', 'beauty', 'pinup', 'clothing', 'style']):
        return "Vintage Fashion"
    elif any(word in term_lower for word in ['car', 'train', 'airplane', 'transportation', 'motorcycle', 'ship', 'vehicle']):
        return "Vintage Transportation"
    elif any(word in term_lower for word in ['american', 'western', 'cowboy', 'patriotic', 'baseball']):
        return "Vintage Americana"
    elif any(word in term_lower for word in ['european', 'french', 'italian', 'british', 'german', 'paris']):
        return "Vintage European"
    elif any(word in term_lower for word in ['vintage', 'antique', 'classic', 'old', 'historical', 'retro']):
        return "Vintage/Classic"
    elif any(word in term_lower for word in ['personalized', 'custom', 'name']):
        return "Personalized"
    elif any(word in term_lower for word in ['space', 'nasa', 'astronomy', 'galaxy']):
        return "Space/Science"
    elif any(word in term_lower for word in ['gift', 'present']):
        return "Gifts"
    elif any(word in term_lower for word in ['wall', 'decor', 'art']):
        return "Wall Art"
    elif any(word in term_lower for word in ['print', 'poster']):
        return "Prints/Posters"
    else:
        return "Other"

if __name__ == "__main__":
    main()
