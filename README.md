# 🎯 Etsy Market Research Scraper

**Find low-competition, high-demand opportunities on Etsy with comprehensive market intelligence.**

## 🚀 Features

### 🔍 **Smart Opportunity Detection**
- **Competition Analysis**: Identifies low-competition niches vs. oversaturated markets
- **Trend Analysis**: Real Google Trends integration to spot growing vs. declining trends
- **Market Data**: Extracts listing counts, price ranges, and competition levels from Etsy
- **Opportunity Scoring**: AI-powered scoring system to rank opportunities

### 📊 **Comprehensive Market Intelligence**
- **Google Trends Integration**: Real search volume and trend data
- **Etsy Market Analysis**: Listing counts, price ranges, competition levels
- **Price Analysis**: Average prices, price ranges, market positioning
- **Category Breakdown**: Organized analysis by product categories

### 🛡️ **Robust & Reliable**
- **Resume Capability**: Continue from where you left off
- **Error Handling**: Automatic retries with exponential backoff
- **Rate Limiting**: Human-like behavior to avoid detection
- **Real-time Logging**: Detailed progress tracking and debugging

## 📦 Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## 🎯 Usage

### Basic Usage
```bash
# Start fresh research
python etsy_autocomplete.py

# Resume from checkpoint
python etsy_autocomplete.py --resume

# Run in background
python etsy_autocomplete.py --headless

# Custom delay between requests
python etsy_autocomplete.py --delay 5
```

### Advanced Options
```bash
# Disable Google Trends (faster, less data)
python etsy_autocomplete.py --no-trends

# Disable Etsy market analysis (faster)
python etsy_autocomplete.py --no-etsy-analysis

# Enable Amazon analysis (requires setup)
python etsy_autocomplete.py --enable-amazon

# Enable social media analysis
python etsy_autocomplete.py --enable-social
```

## 📈 Output Files

### 1. **etsy_market_research.csv**
Main data file with columns:
- `timestamp_utc`: When data was collected
- `seed`: Original search term
- `suggestion`: Related keywords found
- `competition_level`: Competition analysis
- `opportunity_score`: AI-calculated opportunity score
- `trend_score`: Google Trends score
- `trend_direction`: "growing", "declining", or "stable"
- `listing_count`: Number of Etsy listings
- `avg_price`: Average price in the niche
- `price_range`: Min-max price range
- `category`: Product category
- `recommendation`: Action recommendation

### 2. **opportunity_summary.txt**
Summary report with:
- Top 10 high-opportunity seeds
- Top 10 good-opportunity seeds
- Category breakdown with average scores
- Market insights and recommendations

### 3. **scraping_log.txt**
Detailed log of the scraping process

### 4. **scraping_checkpoint.json**
Progress tracking for resume functionality

## 🎯 Opportunity Scoring

### Score Ranges:
- **🔥 5+**: HIGH OPPORTUNITY - Research Further
- **✅ 2-4**: GOOD OPPORTUNITY - Consider
- **⚠️ 0-1**: MODERATE - Check Competition
- **❌ <0**: HIGH COMPETITION - Avoid

### Perfect Opportunities:
- **🔥 PERFECT OPPORTUNITY**: Low competition + Growing trend
- **🔥 HIGH OPPORTUNITY - Growing Trend**: High score + growing market
- **✅ GOOD OPPORTUNITY - Growing Trend**: Good score + growing market

## 🎯 Target Niches

The script is optimized to find:

### ✅ **Low-Competition Opportunities**
- Vintage/antique items
- Historical/niche items
- Regional/cultural items
- Professional/technical niches
- Obscure/specialized items

### ❌ **Avoids High-Competition**
- Seasonal items (Christmas, birthdays)
- Generic terms (gift, personalized)
- Trending/viral items
- Oversaturated markets

## 🔧 Configuration

Edit the `CONFIG` section in the script to customize:

```python
CONFIG = {
    "min_delay": 2,  # Minimum delay between requests
    "max_delay": 8,  # Maximum delay between requests
    "max_retries": 3,  # Retry attempts for failed searches
    "timeout": 15000,  # Page load timeout (ms)
    "enable_google_trends": True,  # Google Trends analysis
    "enable_etsy_analysis": True,  # Etsy market analysis
    "enable_amazon_analysis": False,  # Amazon analysis
    "enable_social_analysis": False,  # Social media analysis
}
```

## 🎯 Search Seeds

The script includes 100+ strategic search terms across categories:

- **Japanese Art & Culture**: ukiyo-e, zen art, cherry blossoms
- **National Parks**: Yosemite, Yellowstone, vintage park posters
- **Vintage Travel**: Retro travel posters, airline art
- **Maps & Cartography**: Antique maps, vintage cartography
- **Botanical & Scientific**: Vintage botanical prints, scientific illustrations
- **Literature & Books**: Classic book covers, Shakespeare art
- **Art Nouveau & Deco**: Vintage advertising, retro typography
- **Vintage Photography**: Historical photos, antique portraits
- **Vintage Fashion**: Retro fashion, pinup art
- **Vintage Transportation**: Classic cars, trains, airplanes
- **Vintage Americana**: Western art, patriotic posters
- **Vintage European**: French, Italian, British vintage art
- **Space & Science**: NASA posters, astronomy art
- **Personalized**: Custom gifts, personalized art

## 🚀 Advanced Features

### Google Trends Integration
- Real search volume data
- Trend direction analysis
- Related queries discovery
- Geographic trend data

### Etsy Market Analysis
- Live listing counts
- Price range analysis
- Competition level assessment
- Market saturation detection

### Resume Capability
- Automatic progress saving
- Resume from any point
- No data loss on interruption
- Checkpoint management

### Error Handling
- Automatic retries
- Exponential backoff
- Graceful failure handling
- Detailed error logging

## 🎯 Best Practices

1. **Start with a small test**: Run with `--delay 5` to test
2. **Use resume feature**: Always use `--resume` for long runs
3. **Monitor logs**: Check `scraping_log.txt` for issues
4. **Focus on high scores**: Prioritize opportunities with scores 5+
5. **Check trends**: Prefer "growing" over "declining" trends
6. **Verify competition**: Low listing counts (<1000) = better opportunities

## 🎯 Example Output

```
🎯 HIGH OPPORTUNITY FOUND: vintage botanical prints (Score: 7.2, Trend: growing, Competition: low)
Market: 847 listings, Avg: $24.50
Recommendation: 🔥 PERFECT OPPORTUNITY - Low Competition + Growing Trend
```

## 🚀 Next Steps

After running the script:

1. **Review opportunity_summary.txt** for top opportunities
2. **Filter CSV by opportunity_score >= 5** for best options
3. **Research high-scoring seeds** manually on Etsy
4. **Check price ranges** to ensure profitability
5. **Validate trends** with additional research

## 🛠️ Troubleshooting

### Common Issues:
- **"Could not find search input"**: Etsy changed selectors, check debug screenshots
- **"No related terms found"**: Search term too specific, try broader terms
- **Rate limiting**: Increase delays with `--delay 10`
- **Browser crashes**: Use `--headless` mode

### Debug Files:
- `etsy_debug_*.png`: Screenshots when selectors fail
- `etsy_search_results_*.png`: Screenshots of search results
- `scraping_log.txt`: Detailed error logs

## 📊 Data Analysis

The script provides comprehensive market intelligence to help you:

- **Identify profitable niches** with low competition
- **Spot growing trends** before they become saturated
- **Analyze price points** for optimal positioning
- **Understand market dynamics** and competition levels
- **Make data-driven decisions** about product development

---

**🎯 Find your next profitable Etsy opportunity with data-driven market research!**
