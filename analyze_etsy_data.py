import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from collections import Counter
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Set style for better looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class EtsyDataAnalyzer:
    def __init__(self, csv_file='etsy_market_research.csv'):
        self.csv_file = csv_file
        self.df = None
        self.load_data()
    
    def load_data(self):
        """Load and clean the data"""
        try:
            self.df = pd.read_csv(self.csv_file)
            print(f"✅ Loaded {len(self.df)} data points from {self.csv_file}")
            
            # Clean up the data
            self.df = self.df.dropna(subset=['suggestion'])
            self.df['suggestion_length'] = self.df['suggestion'].str.len()
            
            # Create opportunity score based on competition level
            competition_scores = {'Low': 3, 'Moderate': 2, 'High': 1}
            self.df['competition_score'] = self.df['competition_level'].map(competition_scores)
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.df = pd.DataFrame()
    
    def create_summary_dashboard(self):
        """Create a comprehensive summary dashboard"""
        if self.df.empty:
            print("❌ No data to analyze")
            return
        
        # Create figure with subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Competition Level Distribution',
                'Top Categories by Data Points',
                'Suggestion Length Distribution',
                'Top Related Search Terms',
                'Competition vs Category Analysis',
                'Category Performance Summary'
            ),
            specs=[[{"type": "pie"}, {"type": "bar"}],
                   [{"type": "histogram"}, {"type": "bar"}],
                   [{"type": "scatter"}, {"type": "table"}]]
        )
        
        # 1. Competition Level Distribution (Pie Chart)
        competition_counts = self.df['competition_level'].value_counts()
        fig.add_trace(
            go.Pie(labels=competition_counts.index, values=competition_counts.values, name="Competition"),
            row=1, col=1
        )
        
        # 2. Top Categories (Bar Chart)
        category_counts = self.df['category'].value_counts().head(10)
        fig.add_trace(
            go.Bar(x=category_counts.index, y=category_counts.values, name="Categories"),
            row=1, col=2
        )
        
        # 3. Suggestion Length Distribution (Histogram)
        fig.add_trace(
            go.Histogram(x=self.df['suggestion_length'], name="Length"),
            row=2, col=1
        )
        
        # 4. Top Related Search Terms (Bar Chart)
        top_suggestions = self.df['suggestion'].value_counts().head(15)
        fig.add_trace(
            go.Bar(x=top_suggestions.index, y=top_suggestions.values, name="Suggestions"),
            row=2, col=2
        )
        
        # 5. Competition vs Category (Scatter)
        category_competition = self.df.groupby('category')['competition_score'].mean().reset_index()
        fig.add_trace(
            go.Scatter(
                x=category_competition['category'], 
                y=category_competition['competition_score'],
                mode='markers+text',
                text=category_competition['category'],
                textposition="top center",
                name="Category Performance"
            ),
            row=3, col=1
        )
        
        # 6. Category Performance Table
        category_summary = self.df.groupby('category').agg({
            'competition_level': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'Unknown',
            'suggestion': 'count',
            'competition_score': 'mean'
        }).round(2)
        category_summary.columns = ['Most Common Competition', 'Data Points', 'Avg Competition Score']
        category_summary = category_summary.sort_values('Avg Competition Score', ascending=False)
        
        fig.add_trace(
            go.Table(
                header=dict(values=['Category', 'Competition', 'Data Points', 'Avg Score']),
                cells=dict(values=[
                    category_summary.index,
                    category_summary['Most Common Competition'],
                    category_summary['Data Points'],
                    category_summary['Avg Competition Score']
                ])
            ),
            row=3, col=2
        )
        
        # Update layout
        fig.update_layout(
            height=1200,
            title_text="Etsy Market Research Dashboard",
            showlegend=False
        )
        
        # Save the dashboard
        fig.write_html("etsy_market_dashboard.html")
        print("✅ Created interactive dashboard: etsy_market_dashboard.html")
        
        return fig
    
    def create_opportunity_analysis(self):
        """Create detailed opportunity analysis"""
        if self.df.empty:
            return
        
        # Calculate opportunity metrics
        self.df['opportunity_score'] = (
            self.df['competition_score'] * 
            (self.df['suggestion_length'] / self.df['suggestion_length'].max())
        )
        
        # Find top opportunities
        top_opportunities = self.df.nlargest(20, 'opportunity_score')
        
        # Create opportunity chart
        fig = px.scatter(
            self.df,
            x='competition_score',
            y='suggestion_length',
            color='category',
            size='opportunity_score',
            hover_data=['seed', 'suggestion'],
            title="Market Opportunity Analysis"
        )
        
        fig.write_html("opportunity_analysis.html")
        print("✅ Created opportunity analysis: opportunity_analysis.html")
        
        return fig
    
    def create_category_insights(self):
        """Create detailed insights for each category"""
        if self.df.empty:
            return
        
        categories = self.df['category'].unique()
        
        for category in categories:
            cat_data = self.df[self.df['category'] == category]
            
            if len(cat_data) < 3:  # Skip categories with too little data
                continue
            
            # Create subplot for this category
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    f'{category} - Competition Distribution',
                    f'{category} - Top Related Terms',
                    f'{category} - Suggestion Length',
                    f'{category} - Opportunity Score Distribution'
                )
            )
            
            # Competition distribution
            comp_counts = cat_data['competition_level'].value_counts()
            fig.add_trace(
                go.Pie(labels=comp_counts.index, values=comp_counts.values),
                row=1, col=1
            )
            
            # Top related terms
            top_terms = cat_data['suggestion'].value_counts().head(10)
            fig.add_trace(
                go.Bar(x=top_terms.index, y=top_terms.values),
                row=1, col=2
            )
            
            # Suggestion length
            fig.add_trace(
                go.Histogram(x=cat_data['suggestion_length']),
                row=2, col=1
            )
            
            # Opportunity scores
            fig.add_trace(
                go.Box(y=cat_data['opportunity_score']),
                row=2, col=2
            )
            
            fig.update_layout(title_text=f"{category} Analysis")
            fig.write_html(f"category_analysis_{category.lower().replace(' ', '_')}.html")
        
        print("✅ Created category-specific analysis files")
    
    def generate_recommendations(self):
        """Generate actionable recommendations"""
        if self.df.empty:
            return
        
        print("\n" + "="*60)
        print("🎯 MARKET OPPORTUNITY RECOMMENDATIONS")
        print("="*60)
        
        # Top opportunities by category
        print("\n📊 TOP OPPORTUNITIES BY CATEGORY:")
        category_opportunities = self.df.groupby('category').agg({
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
        print("\n🎯 BEST LOW-COMPETITION OPPORTUNITIES:")
        low_comp = self.df[self.df['competition_level'] == 'Low']
        if not low_comp.empty:
            top_low_comp = low_comp.nlargest(5, 'opportunity_score')
            for idx, row in top_low_comp.iterrows():
                print(f"• {row['seed']} → {row['suggestion']}")
        else:
            print("No low-competition opportunities found")
        
        # Most popular related terms
        print("\n🔥 MOST POPULAR RELATED TERMS:")
        top_terms = self.df['suggestion'].value_counts().head(10)
        for term, count in top_terms.items():
            print(f"• {term} ({count} mentions)")
        
        # Category recommendations
        print("\n📈 CATEGORY RECOMMENDATIONS:")
        for category in category_opportunities.head(3).index:
            cat_data = self.df[self.df['category'] == category]
            avg_comp = cat_data['competition_score'].mean()
            print(f"• {category}: {'Low' if avg_comp > 2.5 else 'Moderate' if avg_comp > 1.5 else 'High'} competition")
    
    def create_quick_summary(self):
        """Create a quick summary report"""
        if self.df.empty:
            return
        
        print("\n" + "="*60)
        print("📋 QUICK SUMMARY")
        print("="*60)
        print(f"Total data points: {len(self.df)}")
        print(f"Unique search terms: {self.df['seed'].nunique()}")
        print(f"Unique suggestions: {self.df['suggestion'].nunique()}")
        print(f"Categories analyzed: {self.df['category'].nunique()}")
        
        print(f"\nCompetition breakdown:")
        comp_breakdown = self.df['competition_level'].value_counts()
        for level, count in comp_breakdown.items():
            percentage = (count / len(self.df)) * 100
            print(f"  {level}: {count} ({percentage:.1f}%)")
        
        print(f"\nTop 5 categories by data points:")
        top_cats = self.df['category'].value_counts().head(5)
        for cat, count in top_cats.items():
            print(f"  {cat}: {count}")

def main():
    """Main analysis function"""
    analyzer = EtsyDataAnalyzer()
    
    if analyzer.df.empty:
        print("❌ No data found. Please run the Etsy scraper first.")
        return
    
    # Create all visualizations
    print("\n📊 Creating visualizations...")
    analyzer.create_summary_dashboard()
    analyzer.create_opportunity_analysis()
    analyzer.create_category_insights()
    
    # Generate insights
    analyzer.create_quick_summary()
    analyzer.generate_recommendations()
    
    print("\n✅ Analysis complete! Check the generated HTML files for interactive visualizations.")

if __name__ == "__main__":
    main() 