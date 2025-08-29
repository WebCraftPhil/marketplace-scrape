import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Manual data extraction from the successful searches we saw
data = [
    # Japanese Art
    {"seed": "japanese wall art", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Japanese Art"},
    {"seed": "japanese wall art", "suggestion": "ColorGreenBlueYellowWhiteBrownShow more", "competition_level": "Moderate", "category": "Japanese Art"},
    
    # National Parks
    {"seed": "yosemite wall art", "suggestion": "mountain photography prints", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "yosemite wall art", "suggestion": "wildlife wall hangings", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "yosemite wall art", "suggestion": "watercolor nature scenes", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "yosemite wall art", "suggestion": "nature landscape prints", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "yosemite wall art", "suggestion": "outdoor adventure art", "competition_level": "Moderate", "category": "National Parks"},
    
    {"seed": "yellowstone posters", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "High", "category": "National Parks"},
    {"seed": "yellowstone posters", "suggestion": "ColorBlackBlueWhiteBeigeBronzeShow more", "competition_level": "High", "category": "National Parks"},
    
    {"seed": "grand canyon art", "suggestion": "national park wall decor", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "grand canyon art", "suggestion": "southwestern landscape paintings", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "grand canyon art", "suggestion": "outdoor adventure posters", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "grand canyon art", "suggestion": "vintage travel posters", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "grand canyon art", "suggestion": "rustic cabin artwork", "competition_level": "Moderate", "category": "National Parks"},
    
    {"seed": "camping wall art", "suggestion": "custom camping couple print", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "camping wall art", "suggestion": "customizable camping poster", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "camping wall art", "suggestion": "custom wooden camping wall decor", "competition_level": "Moderate", "category": "National Parks"},
    {"seed": "camping wall art", "suggestion": "personalized camping map art", "competition_level": "Moderate", "category": "National Parks"},
    
    # Vintage Travel
    {"seed": "retro travel art", "suggestion": "personalized city skyline art", "competition_level": "Moderate", "category": "Vintage Travel"},
    {"seed": "retro travel art", "suggestion": "personalized travel wall decor", "competition_level": "Moderate", "category": "Vintage Travel"},
    {"seed": "retro travel art", "suggestion": "personalized travel poster", "competition_level": "Moderate", "category": "Vintage Travel"},
    {"seed": "retro travel art", "suggestion": "custom travel print", "competition_level": "Moderate", "category": "Vintage Travel"},
    
    {"seed": "old cruise ship posters", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "High", "category": "Vintage Travel"},
    {"seed": "old cruise ship posters", "suggestion": "ColorBlueWhiteBlackBeigeBronzeShow more", "competition_level": "High", "category": "Vintage Travel"},
    
    {"seed": "vintage destination art", "suggestion": "vintage destination art", "competition_level": "Moderate", "category": "Vintage Travel"},
    {"seed": "vintage destination art", "suggestion": "Applied filters\nVintage", "competition_level": "Moderate", "category": "Vintage Travel"},
    
    # Maps & Cartography
    {"seed": "vintage map prints", "suggestion": "vintage map prints", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "vintage map prints", "suggestion": "personalized travel map", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "vintage map prints", "suggestion": "custom location map", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "vintage map prints", "suggestion": "custom map for wedding", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "vintage map prints", "suggestion": "custom map print", "competition_level": "Moderate", "category": "Maps/Cartography"},
    
    {"seed": "historical maps", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "historical maps", "suggestion": "FramingUnframedFramed", "competition_level": "Moderate", "category": "Maps/Cartography"},
    
    {"seed": "old world maps", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "old world maps", "suggestion": "ColorBrownBeigeBlackGoldGreenShow more", "competition_level": "Moderate", "category": "Maps/Cartography"},
    
    {"seed": "vintage atlas prints", "suggestion": "vintage atlas prints", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "vintage atlas prints", "suggestion": "Applied filters\nVintage", "competition_level": "Moderate", "category": "Maps/Cartography"},
    
    {"seed": "antique cartography", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "antique cartography", "suggestion": "ColorBlackBrownGreenGoldBeigeShow more", "competition_level": "Moderate", "category": "Maps/Cartography"},
    
    {"seed": "vintage city plans", "suggestion": "vintage city plans", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "vintage city plans", "suggestion": "Applied filters\nVintage", "competition_level": "Moderate", "category": "Maps/Cartography"},
    
    {"seed": "historical cartography art", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Maps/Cartography"},
    {"seed": "historical cartography art", "suggestion": "ColorBlackBrownGreenGoldBeigeShow more", "competition_level": "Moderate", "category": "Maps/Cartography"},
    
    # Botanical & Scientific
    {"seed": "vintage botanical prints", "suggestion": "vintage botanical prints", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage botanical prints", "suggestion": "Applied filters\nVintage", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    
    {"seed": "old scientific illustrations", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "old scientific illustrations", "suggestion": "ColorBeigeGreenBrownWhiteBlueShow more", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    
    {"seed": "vintage medical art", "suggestion": "vintage medical art", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage medical art", "suggestion": "personalized medical art for nurse", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage medical art", "suggestion": "medical graduation gift with name", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage medical art", "suggestion": "personalized medical student gift", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage medical art", "suggestion": "personalized doctor portrait", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    
    {"seed": "antique flower prints", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "antique flower prints", "suggestion": "SubjectFlowersPlants & treesLandscape & sceneryAbstract & geometricAnimalShow more", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    
    {"seed": "vintage herbarium", "suggestion": "vintage herbarium", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage herbarium", "suggestion": "custom botanical gift", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage herbarium", "suggestion": "engraved herbarium display", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage herbarium", "suggestion": "personalized pressed flower art", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    {"seed": "vintage herbarium", "suggestion": "custom herbarium kit", "competition_level": "Moderate", "category": "Botanical/Scientific"},
    
    {"seed": "old anatomy prints", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "High", "category": "Botanical/Scientific"},
    {"seed": "old anatomy prints", "suggestion": "ColorBlackWhiteBeigeGrayPinkShow more", "competition_level": "High", "category": "Botanical/Scientific"},
    
    # Literature & Books
    {"seed": "shakespeare quotes art", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Literature/Books"},
    {"seed": "shakespeare quotes art", "suggestion": "ColorBlackGreenSilverRedWhiteShow more", "competition_level": "Moderate", "category": "Literature/Books"},
    
    # Vintage Photography
    {"seed": "vintage portrait art", "suggestion": "vintage portrait art", "competition_level": "Moderate", "category": "Vintage Photography"},
    {"seed": "vintage portrait art", "suggestion": "Applied filters\nVintage", "competition_level": "Moderate", "category": "Vintage Photography"},
    
    # Vintage Americana
    {"seed": "vintage american posters", "suggestion": "vintage american posters", "competition_level": "Moderate", "category": "Vintage Americana"},
    {"seed": "vintage american posters", "suggestion": "Applied filters\nVintage", "competition_level": "Moderate", "category": "Vintage Americana"},
    
    {"seed": "old western art", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Vintage Americana"},
    {"seed": "old western art", "suggestion": "ColorBlueBeigeBlackBronzeBrownShow more", "competition_level": "Moderate", "category": "Vintage Americana"},
    
    {"seed": "retro american style", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "Moderate", "category": "Vintage Americana"},
    {"seed": "retro american style", "suggestion": "ColorRedBlueWhiteGreenBlackShow more", "competition_level": "Moderate", "category": "Vintage Americana"},
    
    # Vintage European
    {"seed": "retro european prints", "suggestion": "Item formatAllPhysical itemsDigital downloads", "competition_level": "High", "category": "Vintage European"},
    {"seed": "retro european prints", "suggestion": "ColorWhiteBlackRedPinkBlueShow more", "competition_level": "High", "category": "Vintage European"},
    
    # Space/Science
    {"seed": "solar system art", "suggestion": "personalized space nursery art", "competition_level": "Moderate", "category": "Space/Science"},
    {"seed": "solar system art", "suggestion": "solar system wall hanging with names", "competition_level": "Moderate", "category": "Space/Science"},
    {"seed": "solar system art", "suggestion": "engraved solar system artwork", "competition_level": "Moderate", "category": "Space/Science"},
    {"seed": "solar system art", "suggestion": "custom planet map art", "competition_level": "Moderate", "category": "Space/Science"},
    {"seed": "solar system art", "suggestion": "personalized solar system print", "competition_level": "Moderate", "category": "Space/Science"},
    
    # Personalized
    {"seed": "anniversary gift custom", "suggestion": "personalized anniversary portrait", "competition_level": "High", "category": "Personalized"},
    {"seed": "anniversary gift custom", "suggestion": "personalized photo frame anniversary gift", "competition_level": "High", "category": "Personalized"},
    {"seed": "anniversary gift custom", "suggestion": "custom anniversary map print", "competition_level": "High", "category": "Personalized"},
    {"seed": "anniversary gift custom", "suggestion": "personalized song lyric print", "competition_level": "High", "category": "Personalized"},
    {"seed": "anniversary gift custom", "suggestion": "monogrammed anniversary gift", "competition_level": "High", "category": "Personalized"},
    
    {"seed": "pet portrait custom", "suggestion": "custom pet portrait from photo", "competition_level": "High", "category": "Personalized"},
    {"seed": "pet portrait custom", "suggestion": "personalized dog memorial", "competition_level": "High", "category": "Personalized"},
    {"seed": "pet portrait custom", "suggestion": "digital pet portrait custom", "competition_level": "High", "category": "Personalized"},
    {"seed": "pet portrait custom", "suggestion": "personalized cat portrait", "competition_level": "High", "category": "Personalized"},
    {"seed": "pet portrait custom", "suggestion": "custom dog portrait", "competition_level": "High", "category": "Personalized"},
]

# Create DataFrame
df = pd.DataFrame(data)

# Clean up the data
df = df[~df['suggestion'].str.contains('Item format|Color|Applied filters|Show more|Framing', na=False)]
df = df[df['suggestion'].str.len() > 10]  # Remove very short suggestions

# Add opportunity score
competition_scores = {'Low': 3, 'Moderate': 2, 'High': 1}
df['competition_score'] = df['competition_level'].map(competition_scores)
df['suggestion_length'] = df['suggestion'].str.len()
df['opportunity_score'] = df['competition_score'] * (df['suggestion_length'] / df['suggestion_length'].max())

print(f"✅ Loaded {len(df)} data points for analysis")

# Create visualizations
def create_dashboard():
    """Create comprehensive dashboard"""
    
    # 1. Competition Level Distribution
    fig1 = px.pie(
        df, 
        names='competition_level', 
        title='Competition Level Distribution',
        color_discrete_map={'Low': '#2E8B57', 'Moderate': '#FFD700', 'High': '#DC143C'}
    )
    fig1.write_html("competition_distribution.html")
    
    # 2. Category Analysis
    category_counts = df['category'].value_counts()
    fig2 = px.bar(
        x=category_counts.index, 
        y=category_counts.values,
        title='Data Points by Category',
        labels={'x': 'Category', 'y': 'Number of Suggestions'}
    )
    fig2.write_html("category_analysis.html")
    
    # 3. Opportunity Analysis
    fig3 = px.scatter(
        df,
        x='competition_score',
        y='suggestion_length',
        color='category',
        size='opportunity_score',
        hover_data=['seed', 'suggestion'],
        title='Market Opportunity Analysis',
        labels={'competition_score': 'Competition Score (Higher = Less Competition)', 
                'suggestion_length': 'Suggestion Length',
                'opportunity_score': 'Opportunity Score'}
    )
    fig3.write_html("opportunity_analysis.html")
    
    # 4. Top Suggestions
    top_suggestions = df['suggestion'].value_counts().head(15)
    fig4 = px.bar(
        x=top_suggestions.index,
        y=top_suggestions.values,
        title='Most Popular Related Search Terms',
        labels={'x': 'Search Term', 'y': 'Frequency'}
    )
    fig4.update_xaxes(tickangle=45)
    fig4.write_html("top_suggestions.html")
    
    # 5. Category Performance
    category_performance = df.groupby('category').agg({
        'competition_level': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown',
        'suggestion': 'count',
        'competition_score': 'mean',
        'opportunity_score': 'mean'
    }).round(2)
    
    fig5 = px.bar(
        x=category_performance.index,
        y=category_performance['opportunity_score'],
        title='Average Opportunity Score by Category',
        labels={'x': 'Category', 'y': 'Average Opportunity Score'}
    )
    fig5.write_html("category_performance.html")
    
    print("✅ Created 5 interactive visualizations:")
    print("   - competition_distribution.html")
    print("   - category_analysis.html") 
    print("   - opportunity_analysis.html")
    print("   - top_suggestions.html")
    print("   - category_performance.html")

def generate_insights():
    """Generate actionable insights"""
    print("\n" + "="*60)
    print("🎯 MARKET OPPORTUNITY INSIGHTS")
    print("="*60)
    
    # Competition breakdown
    print(f"\n📊 COMPETITION BREAKDOWN:")
    comp_breakdown = df['competition_level'].value_counts()
    for level, count in comp_breakdown.items():
        percentage = (count / len(df)) * 100
        print(f"  {level}: {count} ({percentage:.1f}%)")
    
    # Top opportunities by category
    print(f"\n🏆 TOP OPPORTUNITIES BY CATEGORY:")
    category_opportunities = df.groupby('category').agg({
        'opportunity_score': 'mean',
        'competition_score': 'mean',
        'suggestion': 'count'
    }).sort_values('opportunity_score', ascending=False)
    
    for idx, (category, data) in enumerate(category_opportunities.head(5).iterrows(), 1):
        print(f"{idx}. {category}")
        print(f"   Opportunity Score: {data['opportunity_score']:.2f}")
        print(f"   Competition Level: {3-data['competition_score']:.1f}/3 (Lower is better)")
        print(f"   Data Points: {data['suggestion']:.0f}")
        print()
    
    # Best low-competition opportunities
    print(f"\n🎯 BEST LOW-COMPETITION OPPORTUNITIES:")
    low_comp = df[df['competition_level'] == 'Low']
    if not low_comp.empty:
        top_low_comp = low_comp.nlargest(5, 'opportunity_score')
        for idx, row in top_low_comp.iterrows():
            print(f"• {row['seed']} → {row['suggestion']}")
    else:
        print("No low-competition opportunities found")
    
    # Most popular related terms
    print(f"\n🔥 MOST POPULAR RELATED TERMS:")
    top_terms = df['suggestion'].value_counts().head(10)
    for term, count in top_terms.items():
        print(f"• {term} ({count} mentions)")
    
    # Category recommendations
    print(f"\n📈 CATEGORY RECOMMENDATIONS:")
    for category in category_opportunities.head(3).index:
        cat_data = df[df['category'] == category]
        avg_comp = cat_data['competition_score'].mean()
        print(f"• {category}: {'Low' if avg_comp > 2.5 else 'Moderate' if avg_comp > 1.5 else 'High'} competition")

def main():
    """Main analysis function"""
    print(f"📊 Analyzing {len(df)} data points...")
    
    # Create visualizations
    create_dashboard()
    
    # Generate insights
    generate_insights()
    
    # Save cleaned data
    df.to_csv("cleaned_etsy_data.csv", index=False)
    print(f"\n✅ Saved cleaned data to: cleaned_etsy_data.csv")
    
    print(f"\n🎉 Analysis complete! Open the HTML files in your browser for interactive visualizations.")

if __name__ == "__main__":
    main() 