from playwright.sync_api import sync_playwright
import csv, time, json, random, argparse
from datetime import datetime, timedelta
import os
from pathlib import Path
import requests
import urllib.parse
import re
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# Try to import optional dependencies
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False
    print("⚠️ pytrends not available. Install with: pip install pytrends")

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️ selenium not available. Install with: pip install selenium webdriver-manager")

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
CHECKPOINT_FILE = "scraping_checkpoint.json"
LOG_FILE = "scraping_log.txt"

# Configuration
CONFIG = {
    "min_delay": 2,  # Minimum delay between requests (seconds)
    "max_delay": 8,  # Maximum delay between requests (seconds)
    "max_retries": 3,  # Maximum retries for failed searches
    "timeout": 15000,  # Page load timeout (ms)
    "enable_google_trends": True,  # Enable Google Trends analysis
    "enable_etsy_analysis": True,  # Enable Etsy search result analysis
    "enable_amazon_analysis": False,  # Enable Amazon analysis (requires API)
    "enable_social_analysis": False,  # Enable social media analysis
    "user_agents": [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
}

# Initialize Google Trends
if PYTRENDS_AVAILABLE and CONFIG["enable_google_trends"]:
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10,25), retries=2, backoff_factor=0.1)
        log_message("✅ Google Trends API initialized")
    except Exception as e:
        log_message(f"❌ Failed to initialize Google Trends: {e}", "ERROR")
        CONFIG["enable_google_trends"] = False

def log_message(message, level="INFO"):
    """Log message to file and console"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {level}: {message}"
    print(log_entry)
    
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

def load_checkpoint():
    """Load progress from checkpoint file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, "r") as f:
                checkpoint = json.load(f)
            log_message(f"Resuming from checkpoint: {checkpoint['processed_count']}/{len(SEEDS)} seeds completed")
            return checkpoint
        except Exception as e:
            log_message(f"Error loading checkpoint: {e}", "ERROR")
    return {"processed_seeds": [], "processed_count": 0, "total_rows": 0}

def save_checkpoint(processed_seeds, total_rows):
    """Save progress to checkpoint file"""
    checkpoint = {
        "processed_seeds": processed_seeds,
        "processed_count": len(processed_seeds),
        "total_rows": total_rows,
        "timestamp": datetime.now().isoformat()
    }
    try:
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(checkpoint, f, indent=2)
    except Exception as e:
        log_message(f"Error saving checkpoint: {e}", "ERROR")

def get_remaining_seeds(processed_seeds):
    """Get list of seeds that haven't been processed yet"""
    return [seed for seed in SEEDS if seed not in processed_seeds]

def random_delay():
    """Add random delay to appear more human-like"""
    delay = random.uniform(CONFIG["min_delay"], CONFIG["max_delay"])
    time.sleep(delay)

def scrape_seed_with_retry(page, seed, max_retries=3):
    """Scrape a seed term with retry logic"""
    for attempt in range(max_retries):
        try:
            return scrape_seed(page, seed)
        except Exception as e:
            log_message(f"Attempt {attempt + 1} failed for '{seed}': {e}", "WARNING")
            if attempt < max_retries - 1:
                delay = (attempt + 1) * 5  # Exponential backoff
                log_message(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                log_message(f"All retries failed for '{seed}'", "ERROR")
                return [], {'listing_count': 0, 'price_range': {'min': 0, 'max': 0, 'avg': 0}, 'competition_level': 'unknown'}
    return [], {'listing_count': 0, 'price_range': {'min': 0, 'max': 0, 'avg': 0}, 'competition_level': 'unknown'}

def scrape_seed(page, seed):
    """Scrape Etsy search results and extract suggestions and market data"""
    # Go to homepage to ensure clean state each time (resets suggestions)
    page.goto("https://www.etsy.com/", wait_until="domcontentloaded", timeout=CONFIG["timeout"])
    
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
                log_message(f"Found search input with selector: {selector}")
                break
        except:
            continue
    
    if not search_input:
        log_message("Could not find search input - taking screenshot for debugging", "ERROR")
        page.screenshot(path=f"etsy_debug_{seed.replace(' ', '_')}.png")
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
                log_message(f"Clicked search button with selector: {button_sel}")
                break
        except:
            continue
    
    # If no button found, try pressing Enter
    if not search_submitted:
        search_input.press("Enter")
        log_message("Pressed Enter to submit search")
    
    # Wait for search results page to load
    page.wait_for_load_state("networkidle", timeout=CONFIG["timeout"])
    time.sleep(3)
    
    # Extract suggestions and market data
    suggestions = []
    market_data = {
        'listing_count': 0,
        'price_range': {'min': 0, 'max': 0, 'avg': 0},
        'competition_level': 'unknown'
    }
    
    # Extract related terms from search results page
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
                log_message(f"Found {count} elements with selector: {sel}")
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
    
    # Extract market data if enabled
    if CONFIG["enable_etsy_analysis"]:
        market_data = extract_etsy_market_data(page, seed)
    
    # If no suggestions found, take a screenshot for debugging
    if not suggestions:
        log_message("No related terms found - taking screenshot for debugging", "WARNING")
        page.screenshot(path=f"etsy_search_results_{seed.replace(' ', '_')}.png")
        
        # Get page title and URL for debugging
        title = page.title()
        url = page.url()
        log_message(f"Search results page: {title}")
        log_message(f"URL: {url}")
    
    return suggestions, market_data

def extract_etsy_market_data(page, seed):
    """Extract market data from Etsy search results"""
    market_data = {
        'listing_count': 0,
        'price_range': {'min': 0, 'max': 0, 'avg': 0},
        'competition_level': 'unknown',
        'price_data': []
    }
    
    try:
        # Try to get total listing count
        count_selectors = [
            '[data-testid="search-results-count"]',
            '[class*="results-count"]',
            '[class*="search-results"]',
            'span:has-text("results")',
            'span:has-text("items")'
        ]
        
        for selector in count_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    text = element.inner_text()
                    # Extract number from text like "1,234 results" or "1,234 items"
                    numbers = re.findall(r'[\d,]+', text)
                    if numbers:
                        count_str = numbers[0].replace(',', '')
                        market_data['listing_count'] = int(count_str)
                        log_message(f"Found {market_data['listing_count']} listings for '{seed}'")
                        break
            except:
                continue
        
        # Extract price data from first few listings
        price_selectors = [
            '[data-testid="price"]',
            '[class*="price"]',
            'span[class*="currency"]',
            '[data-ui="price"]'
        ]
        
        prices = []
        for selector in price_selectors:
            try:
                elements = page.locator(selector)
                count = min(elements.count(), 20)  # Check first 20 listings
                
                for i in range(count):
                    try:
                        price_text = elements.nth(i).inner_text().strip()
                        # Extract price from text like "$15.99" or "15.99"
                        price_match = re.search(r'[\$£€]?(\d+\.?\d*)', price_text)
                        if price_match:
                            price = float(price_match.group(1))
                            prices.append(price)
                    except:
                        continue
                
                if prices:
                    break
            except:
                continue
        
        # Calculate price statistics
        if prices:
            market_data['price_data'] = prices
            market_data['price_range']['min'] = min(prices)
            market_data['price_range']['max'] = max(prices)
            market_data['price_range']['avg'] = sum(prices) / len(prices)
            
            # Determine competition level based on listing count and price range
            if market_data['listing_count'] < 1000:
                market_data['competition_level'] = 'low'
            elif market_data['listing_count'] < 5000:
                market_data['competition_level'] = 'moderate'
            else:
                market_data['competition_level'] = 'high'
            
            log_message(f"Price range: ${market_data['price_range']['min']:.2f} - ${market_data['price_range']['max']:.2f} (avg: ${market_data['price_range']['avg']:.2f})")
        
    except Exception as e:
        log_message(f"Error extracting market data: {e}", "WARNING")
    
    return market_data

def analyze_competition_level(seed):
    """Analyze competition level and opportunity potential"""
    seed_lower = seed.lower()
    
    # High competition indicators (avoid these)
    high_comp_keywords = [
        'gift', 'personalized', 'custom', 'print', 'poster', 'wall art', 'decor',
        'christmas', 'birthday', 'anniversary', 'wedding', 'baby', 'kids',
        'popular', 'trending', 'viral', 'best seller', 'top rated'
    ]
    
    # Low competition opportunities (target these)
    low_comp_keywords = [
        'niche', 'specific', 'unique', 'rare', 'vintage', 'antique', 'historical',
        'obscure', 'specialized', 'professional', 'technical', 'academic',
        'regional', 'local', 'cultural', 'heritage', 'traditional'
    ]
    
    # High demand indicators (good for sales)
    demand_keywords = [
        'wall art', 'decor', 'home', 'office', 'gift', 'personalized',
        'vintage', 'antique', 'unique', 'custom', 'handmade'
    ]
    
    high_count = sum(1 for keyword in high_comp_keywords if keyword in seed_lower)
    low_count = sum(1 for keyword in low_comp_keywords if keyword in seed_lower)
    demand_count = sum(1 for keyword in demand_keywords if keyword in seed_lower)
    
    # Calculate opportunity score (higher = better opportunity)
    opportunity_score = demand_count - high_count + (low_count * 2)
    
    if high_count > low_count and high_count > 2:
        return "High Competition - Avoid"
    elif low_count > high_count and demand_count > 0:
        return "Low Competition - Good Opportunity"
    elif opportunity_score > 2:
        return "Moderate Competition - Consider"
    else:
        return "High Competition - Avoid"

def get_google_trends_data(term):
    """Get real Google Trends data for a search term"""
    if not CONFIG["enable_google_trends"] or not PYTRENDS_AVAILABLE:
        return get_simulated_trends_data(term)
    
    try:
        # Build payload
        pytrends.build_payload([term], cat=0, timeframe='today 12-m', geo='US')
        
        # Get interest over time
        interest_over_time = pytrends.interest_over_time()
        
        if interest_over_time.empty:
            return get_simulated_trends_data(term)
        
        # Calculate trend metrics
        recent_data = interest_over_time[term].tail(30)  # Last 30 days
        older_data = interest_over_time[term].head(30)   # First 30 days
        
        recent_avg = recent_data.mean()
        older_avg = older_data.mean()
        
        # Calculate trend score
        if older_avg == 0:
            trend_score = 0
        else:
            trend_score = ((recent_avg - older_avg) / older_avg) * 100
        
        # Get related queries
        related_queries = pytrends.related_queries()
        rising_queries = related_queries[term]['rising'] if related_queries[term]['rising'] is not None else pd.DataFrame()
        top_queries = related_queries[term]['top'] if related_queries[term]['top'] is not None else pd.DataFrame()
        
        return {
            'trend_score': trend_score,
            'trend_direction': 'growing' if trend_score > 5 else 'declining' if trend_score < -5 else 'stable',
            'trend_strength': abs(trend_score),
            'current_interest': recent_avg,
            'rising_queries': rising_queries.to_dict('records') if not rising_queries.empty else [],
            'top_queries': top_queries.to_dict('records') if not top_queries.empty else []
        }
        
    except Exception as e:
        log_message(f"Error getting Google Trends data for '{term}': {e}", "WARNING")
        return get_simulated_trends_data(term)

def get_simulated_trends_data(term):
    """Fallback to simulated trend data"""
    term_lower = term.lower()
    
    # Simulate trend score based on term characteristics
    trend_score = 0
    
    # Seasonal factors
    seasonal_terms = {
        'christmas': -20, 'holiday': -10, 'birthday': -5, 'wedding': -5,
        'valentine': -15, 'mother': -5, 'father': -5, 'graduation': -5
    }
    
    # Growing trends
    growing_terms = {
        'vintage': 15, 'antique': 10, 'sustainable': 20, 'eco': 15,
        'minimalist': 10, 'zen': 8, 'japanese': 12, 'scandinavian': 10,
        'boho': 8, 'industrial': 5, 'farmhouse': 5
    }
    
    # Declining trends
    declining_terms = {
        'traditional': -5, 'classic': -3, 'formal': -8, 'elegant': -3
    }
    
    for seasonal_term, score in seasonal_terms.items():
        if seasonal_term in term_lower:
            trend_score += score
    
    for growing_term, score in growing_terms.items():
        if growing_term in term_lower:
            trend_score += score
    
    for declining_term, score in declining_terms.items():
        if declining_term in term_lower:
            trend_score += score
    
    # Base trend score (most terms have slight growth)
    trend_score += 5
    
    return {
        'trend_score': trend_score,
        'trend_direction': 'growing' if trend_score > 0 else 'declining',
        'trend_strength': abs(trend_score),
        'current_interest': 50,
        'rising_queries': [],
        'top_queries': []
    }

def calculate_opportunity_score(seed, suggestions, trends_data=None):
    """Calculate opportunity score based on seed, suggestions, and market trends"""
    seed_lower = seed.lower()
    
    # Factors that increase opportunity score
    positive_factors = {
        'vintage': 3, 'antique': 3, 'historical': 3, 'niche': 4,
        'specific': 2, 'unique': 3, 'rare': 4, 'obscure': 4,
        'regional': 3, 'cultural': 3, 'heritage': 3, 'traditional': 2,
        'professional': 2, 'technical': 2, 'academic': 2
    }
    
    # Factors that decrease opportunity score
    negative_factors = {
        'gift': -2, 'personalized': -1, 'custom': -1, 'print': -1,
        'poster': -1, 'christmas': -3, 'birthday': -2, 'wedding': -2,
        'popular': -3, 'trending': -3, 'viral': -3, 'best seller': -3
    }
    
    score = 0
    
    # Analyze seed term
    for factor, points in positive_factors.items():
        if factor in seed_lower:
            score += points
    
    for factor, points in negative_factors.items():
        if factor in seed_lower:
            score += points
    
    # Analyze suggestions for additional insights
    if suggestions:
        suggestion_text = ' '.join(suggestions).lower()
        for factor, points in positive_factors.items():
            if factor in suggestion_text:
                score += points * 0.5  # Suggestions get half weight
        
        for factor, points in negative_factors.items():
            if factor in suggestion_text:
                score += points * 0.5
    
    # Add trend data to score
    if trends_data:
        trend_score = trends_data.get('trend_score', 0)
        score += trend_score * 0.3  # Trends get 30% weight
    
    return score

def main():
    parser = argparse.ArgumentParser(description="Etsy Market Research Scraper")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--delay", type=int, default=3, help="Delay between requests (seconds)")
    args = parser.parse_args()
    
    # Update config based on args
    CONFIG["min_delay"] = args.delay
    CONFIG["max_delay"] = args.delay + 2
    
    timestamp = datetime.utcnow().isoformat()
    
    # Load checkpoint if resuming
    if args.resume:
        checkpoint = load_checkpoint()
        processed_seeds = checkpoint["processed_seeds"]
        total_rows = checkpoint["total_rows"]
        remaining_seeds = get_remaining_seeds(processed_seeds)
        log_message(f"Resuming with {len(remaining_seeds)} seeds remaining")
    else:
        processed_seeds = []
        total_rows = 0
        remaining_seeds = SEEDS
        log_message(f"Starting fresh with {len(SEEDS)} seeds")
    
    # Create CSV file and write header immediately
    header = [
        "timestamp_utc", "seed", "suggestion", "competition_level", "opportunity_score", 
        "trend_score", "trend_direction", "listing_count", "avg_price", "price_range", 
        "category", "recommendation"
    ]
    if not args.resume or not os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
    
    with sync_playwright() as p:
        # Use a more realistic browser setup
        browser = p.chromium.launch(
            headless=args.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        context = browser.new_context(
            locale="en-US",
            user_agent=random.choice(CONFIG["user_agents"])
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

        for i, seed in enumerate(remaining_seeds, 1):
            try:
                log_message(f"Processing {i}/{len(remaining_seeds)}: {seed}")
                
                suggs, market_data = scrape_seed_with_retry(page, seed, CONFIG["max_retries"])
                competition_level = analyze_competition_level(seed)
                
                # Get trend data
                trends_data = get_google_trends_data(seed)
                opportunity_score = calculate_opportunity_score(seed, suggs, trends_data)
                
                # Adjust opportunity score based on market data
                if market_data['listing_count'] > 0:
                    if market_data['listing_count'] < 1000:
                        opportunity_score += 2  # Low competition bonus
                    elif market_data['listing_count'] > 10000:
                        opportunity_score -= 2  # High competition penalty
                
                # Determine recommendation based on opportunity score, trends, and market data
                if opportunity_score >= 5 and trends_data['trend_direction'] == 'growing' and market_data['competition_level'] == 'low':
                    recommendation = "🔥 PERFECT OPPORTUNITY - Low Competition + Growing Trend"
                elif opportunity_score >= 5 and trends_data['trend_direction'] == 'growing':
                    recommendation = "🔥 HIGH OPPORTUNITY - Growing Trend"
                elif opportunity_score >= 5:
                    recommendation = "🔥 HIGH OPPORTUNITY - Research Further"
                elif opportunity_score >= 2 and trends_data['trend_direction'] == 'growing':
                    recommendation = "✅ GOOD OPPORTUNITY - Growing Trend"
                elif opportunity_score >= 2:
                    recommendation = "✅ GOOD OPPORTUNITY - Consider"
                elif opportunity_score >= 0:
                    recommendation = "⚠️ MODERATE - Check Competition"
                else:
                    recommendation = "❌ HIGH COMPETITION - Avoid"
                
                # Write data immediately for this seed
                rows_for_seed = []
                for s in suggs:
                    row = {
                        "timestamp_utc": timestamp, 
                        "seed": seed, 
                        "suggestion": s,
                        "competition_level": competition_level,
                        "opportunity_score": opportunity_score,
                        "trend_score": trends_data['trend_score'],
                        "trend_direction": trends_data['trend_direction'],
                        "listing_count": market_data['listing_count'],
                        "avg_price": market_data['price_range']['avg'],
                        "price_range": f"${market_data['price_range']['min']:.2f}-${market_data['price_range']['max']:.2f}",
                        "category": categorize_term(seed),
                        "recommendation": recommendation
                    }
                    rows_for_seed.append(row)
                
                # Write to CSV immediately
                with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=header)
                    writer.writerows(rows_for_seed)
                
                total_rows += len(rows_for_seed)
                processed_seeds.append(seed)
                
                # Save checkpoint after each successful seed
                save_checkpoint(processed_seeds, total_rows)
                
                log_message(f"✅ {seed} → {len(suggs)} suggestions (Score: {opportunity_score:.1f}, Trend: {trends_data['trend_direction']}, {competition_level}) - Total: {total_rows} rows")
                log_message(f"Market: {market_data['listing_count']} listings, Avg: ${market_data['price_range']['avg']:.2f}")
                log_message(f"Recommendation: {recommendation}")
                if suggs:
                    log_message(f"Sample suggestions: {suggs[:3]}")
                
                # Highlight high-opportunity seeds
                if opportunity_score >= 5:
                    log_message(f"🎯 HIGH OPPORTUNITY FOUND: {seed} (Score: {opportunity_score:.1f}, Trend: {trends_data['trend_direction']}, Competition: {market_data['competition_level']})", "SUCCESS")
                
                # Add random delay between searches
                if i < len(remaining_seeds):  # Don't delay after the last one
                    random_delay()
                    
            except Exception as e:
                log_message(f"❌ Error processing '{seed}': {e}", "ERROR")
                continue

        browser.close()

    log_message(f"🎉 Research complete! Total data points saved: {total_rows}")
    log_message(f"Data saved to: {OUTPUT_CSV}")
    
    # Generate opportunity summary
    generate_opportunity_summary(OUTPUT_CSV)
    
    # Clean up checkpoint file on successful completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        log_message("Checkpoint file cleaned up")

def generate_opportunity_summary(csv_file):
    """Generate a summary of the best opportunities found"""
    if not os.path.exists(csv_file):
        return
    
    opportunities = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('opportunity_score'):
                    try:
                        score = float(row['opportunity_score'])
                        opportunities.append({
                            'seed': row['seed'],
                            'score': score,
                            'recommendation': row['recommendation'],
                            'category': row['category']
                        })
                    except ValueError:
                        continue
    except Exception as e:
        log_message(f"Error reading CSV for summary: {e}", "ERROR")
        return
    
    if not opportunities:
        return
    
    # Sort by opportunity score (highest first)
    opportunities.sort(key=lambda x: x['score'], reverse=True)
    
    # Generate summary report
    summary_file = "opportunity_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("🎯 ETSY OPPORTUNITY ANALYSIS SUMMARY\n")
        f.write("=" * 50 + "\n\n")
        
        # Top opportunities
        high_opportunities = [op for op in opportunities if op['score'] >= 5]
        good_opportunities = [op for op in opportunities if 2 <= op['score'] < 5]
        
        f.write(f"🔥 HIGH OPPORTUNITIES (Score ≥ 5): {len(high_opportunities)}\n")
        f.write("-" * 40 + "\n")
        for op in high_opportunities[:10]:  # Top 10
            f.write(f"• {op['seed']} (Score: {op['score']:.1f}, Category: {op['category']})\n")
        
        f.write(f"\n✅ GOOD OPPORTUNITIES (Score 2-4): {len(good_opportunities)}\n")
        f.write("-" * 40 + "\n")
        for op in good_opportunities[:10]:  # Top 10
            f.write(f"• {op['seed']} (Score: {op['score']:.1f}, Category: {op['category']})\n")
        
        # Category breakdown
        f.write(f"\n📊 CATEGORY BREAKDOWN\n")
        f.write("-" * 40 + "\n")
        categories = {}
        for op in opportunities:
            cat = op['category']
            if cat not in categories:
                categories[cat] = {'count': 0, 'avg_score': 0, 'total_score': 0}
            categories[cat]['count'] += 1
            categories[cat]['total_score'] += op['score']
        
        for cat, data in categories.items():
            data['avg_score'] = data['total_score'] / data['count']
            f.write(f"• {cat}: {data['count']} opportunities, avg score: {data['avg_score']:.1f}\n")
    
    log_message(f"📊 Opportunity summary saved to: {summary_file}")
    log_message(f"🔥 Found {len(high_opportunities)} high-opportunity seeds")
    log_message(f"✅ Found {len(good_opportunities)} good-opportunity seeds")

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
