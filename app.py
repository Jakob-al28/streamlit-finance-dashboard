# run this streamlit app: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import numpy as np
import streamlit.components.v1 as components
import math
from statsmodels.tsa.seasonal import seasonal_decompose
from great_tables import GT, html, style, loc 
import backend.data_fetching
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
import datetime
import yfinance as yf

# from tabs.overview import render_tab as render_overview_tab
# from tabs.quotes import render_tab as render_quotes_tab
# from tabs.charts import render_tab as render_charts_tab
# from tabs.analytics import render_tab as render_analytics_tab

# Simple fuzzy search function
def fuzzy_search(query, items, threshold=2):
    """Simple fuzzy search using Levenshtein distance"""
    if not query:
        return items
    
    def levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    matches = []
    for item in items:
        # Check ticker
        ticker_distance = levenshtein_distance(query.lower(), item["ticker"].lower())
        # Check company name
        name_distance = levenshtein_distance(query.lower(), item["name"].lower())
        
        min_distance = min(ticker_distance, name_distance)
        if min_distance <= threshold:
            matches.append((item, min_distance))
    
    # Sort by distance (closest matches first)
    return [item for item, _ in sorted(matches, key=lambda x: x[1])]

# Country data - comprehensive list
countries = [
    "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
    "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi",
    "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
    "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia",
    "Fiji", "Finland", "France",
    "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana",
    "Haiti", "Honduras", "Hungary",
    "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Ivory Coast",
    "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan",
    "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg",
    "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar",
    "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway",
    "Oman",
    "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal",
    "Qatar",
    "Romania", "Russia", "Rwanda",
    "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria",
    "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
    "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay", "Uzbekistan",
    "Vanuatu", "Vatican City", "Venezuela", "Vietnam",
    "Yemen",
    "Zambia", "Zimbabwe"
]

# Countries with major stock indices (for map data)
countries_with_indices = {
    'USA': {'index': '^GSPC', 'name': 'S&P 500', 'change_pct': 1.25, 'is_open': True, 'currency': 'USD'},
    'DEU': {'index': '^GDAXI', 'name': 'DAX', 'change_pct': -0.85, 'is_open': False, 'currency': 'EUR'},
    'JPN': {'index': '^N225', 'name': 'Nikkei 225', 'change_pct': 0.45, 'is_open': False, 'currency': 'JPY'},
    'GBR': {'index': '^FTSE', 'name': 'FTSE 100', 'change_pct': -0.32, 'is_open': False, 'currency': 'GBP'},
    'FRA': {'index': '^FCHI', 'name': 'CAC 40', 'change_pct': 0.78, 'is_open': False, 'currency': 'EUR'},
    'ITA': {'index': '^FMIB', 'name': 'FTSE MIB', 'change_pct': -1.12, 'is_open': False, 'currency': 'EUR'},
    'ESP': {'index': '^IBEX', 'name': 'IBEX 35', 'change_pct': 0.23, 'is_open': False, 'currency': 'EUR'},
    'CAN': {'index': '^GSPTSE', 'name': 'TSX', 'change_pct': 0.67, 'is_open': True, 'currency': 'CAD'},
    'AUS': {'index': '^AXJO', 'name': 'ASX 200', 'change_pct': -0.54, 'is_open': False, 'currency': 'AUD'},
    'BRA': {'index': '^BVSP', 'name': 'Bovespa', 'change_pct': 2.15, 'is_open': True, 'currency': 'BRL'},
    'CHN': {'index': '^SSEC', 'name': 'Shanghai Composite', 'change_pct': -0.89, 'is_open': False, 'currency': 'CNY'},
    'IND': {'index': '^NSEI', 'name': 'NIFTY 50', 'change_pct': 1.45, 'is_open': False, 'currency': 'INR'},
    'RUS': {'index': '^IMOEX', 'name': 'MOEX', 'change_pct': 0.12, 'is_open': False, 'currency': 'RUB'},
    'ZAF': {'index': '^JN0U', 'name': 'JSE Top 40', 'change_pct': -0.76, 'is_open': False, 'currency': 'ZAR'},
}

# Mapping from full country names to country codes
country_name_to_code = {
    'Afghanistan': 'AFG', 'Albania': 'ALB', 'Algeria': 'DZA', 'Andorra': 'AND', 'Angola': 'AGO', 
    'Antigua and Barbuda': 'ATG', 'Argentina': 'ARG', 'Armenia': 'ARM', 'Australia': 'AUS', 'Austria': 'AUT', 
    'Azerbaijan': 'AZE', 'Bahamas': 'BHS', 'Bahrain': 'BHR', 'Bangladesh': 'BGD', 'Barbados': 'BRB', 
    'Belarus': 'BLR', 'Belgium': 'BEL', 'Belize': 'BLZ', 'Benin': 'BEN', 'Bhutan': 'BTN', 
    'Bolivia': 'BOL', 'Bosnia and Herzegovina': 'BIH', 'Botswana': 'BWA', 'Brazil': 'BRA', 'Brunei': 'BRN', 
    'Bulgaria': 'BGR', 'Burkina Faso': 'BFA', 'Burundi': 'BDI', 'Cabo Verde': 'CPV', 'Cambodia': 'KHM', 
    'Cameroon': 'CMR', 'Canada': 'CAN', 'Central African Republic': 'CAF', 'Chad': 'TCD', 'Chile': 'CHL', 
    'China': 'CHN', 'Colombia': 'COL', 'Comoros': 'COM', 'Congo': 'COG', 'Costa Rica': 'CRI', 
    'Croatia': 'HRV', 'Cuba': 'CUB', 'Cyprus': 'CYP', 'Czech Republic': 'CZE', 
    'Democratic Republic of the Congo': 'COD', 'Denmark': 'DNK', 'Djibouti': 'DJI', 'Dominica': 'DMA', 
    'Dominican Republic': 'DOM', 'Ecuador': 'ECU', 'Egypt': 'EGY', 'El Salvador': 'SLV', 
    'Equatorial Guinea': 'GNQ', 'Eritrea': 'ERI', 'Estonia': 'EST', 'Eswatini': 'SWZ', 'Ethiopia': 'ETH', 
    'Fiji': 'FJI', 'Finland': 'FIN', 'France': 'FRA', 'Gabon': 'GAB', 'Gambia': 'GMB', 'Georgia': 'GEO', 
    'Germany': 'DEU', 'Ghana': 'GHA', 'Greece': 'GRC', 'Grenada': 'GRD', 'Guatemala': 'GTM', 
    'Guinea': 'GIN', 'Guinea-Bissau': 'GNB', 'Guyana': 'GUY', 'Haiti': 'HTI', 'Honduras': 'HND', 
    'Hungary': 'HUN', 'Iceland': 'ISL', 'India': 'IND', 'Indonesia': 'IDN', 'Iran': 'IRN', 'Iraq': 'IRQ', 
    'Ireland': 'IRL', 'Israel': 'ISR', 'Italy': 'ITA', 'Ivory Coast': 'CIV', 'Jamaica': 'JAM', 
    'Japan': 'JPN', 'Jordan': 'JOR', 'Kazakhstan': 'KAZ', 'Kenya': 'KEN', 'Kiribati': 'KIR', 
    'Kuwait': 'KWT', 'Kyrgyzstan': 'KGZ', 'Laos': 'LAO', 'Latvia': 'LVA', 'Lebanon': 'LBN', 
    'Lesotho': 'LSO', 'Liberia': 'LBR', 'Libya': 'LBY', 'Liechtenstein': 'LIE', 'Lithuania': 'LTU', 
    'Luxembourg': 'LUX', 'Madagascar': 'MDG', 'Malawi': 'MWI', 'Malaysia': 'MYS', 'Maldives': 'MDV', 
    'Mali': 'MLI', 'Malta': 'MLT', 'Marshall Islands': 'MHL', 'Mauritania': 'MRT', 'Mauritius': 'MUS', 
    'Mexico': 'MEX', 'Micronesia': 'FSM', 'Moldova': 'MDA', 'Monaco': 'MCO', 'Mongolia': 'MNG', 
    'Montenegro': 'MNE', 'Morocco': 'MAR', 'Mozambique': 'MOZ', 'Myanmar': 'MMR', 'Namibia': 'NAM', 
    'Nauru': 'NRU', 'Nepal': 'NPL', 'Netherlands': 'NLD', 'New Zealand': 'NZL', 'Nicaragua': 'NIC', 
    'Niger': 'NER', 'Nigeria': 'NGA', 'North Korea': 'PRK', 'North Macedonia': 'MKD', 'Norway': 'NOR', 
    'Oman': 'OMN', 'Pakistan': 'PAK', 'Palau': 'PLW', 'Panama': 'PAN', 'Papua New Guinea': 'PNG', 
    'Paraguay': 'PRY', 'Peru': 'PER', 'Philippines': 'PHL', 'Poland': 'POL', 'Portugal': 'PRT', 
    'Qatar': 'QAT', 'Romania': 'ROU', 'Russia': 'RUS', 'Rwanda': 'RWA', 'Saint Kitts and Nevis': 'KNA', 
    'Saint Lucia': 'LCA', 'Saint Vincent and the Grenadines': 'VCT', 'Samoa': 'WSM', 'San Marino': 'SMR', 
    'Sao Tome and Principe': 'STP', 'Saudi Arabia': 'SAU', 'Senegal': 'SEN', 'Serbia': 'SRB', 
    'Seychelles': 'SYC', 'Sierra Leone': 'SLE', 'Singapore': 'SGP', 'Slovakia': 'SVK', 'Slovenia': 'SVN', 
    'Solomon Islands': 'SLB', 'Somalia': 'SOM', 'South Africa': 'ZAF', 'South Korea': 'KOR', 
    'South Sudan': 'SSD', 'Spain': 'ESP', 'Sri Lanka': 'LKA', 'Sudan': 'SDN', 'Suriname': 'SUR', 
    'Sweden': 'SWE', 'Switzerland': 'CHE', 'Syria': 'SYR', 'Taiwan': 'TWN', 'Tajikistan': 'TJK', 
    'Tanzania': 'TZA', 'Thailand': 'THA', 'Timor-Leste': 'TLS', 'Togo': 'TGO', 'Tonga': 'TON', 
    'Trinidad and Tobago': 'TTO', 'Tunisia': 'TUN', 'Turkey': 'TUR', 'Turkmenistan': 'TKM', 
    'Tuvalu': 'TUV', 'Uganda': 'UGA', 'Ukraine': 'UKR', 'United Arab Emirates': 'ARE', 
    'United Kingdom': 'GBR', 'United States': 'USA', 'Uruguay': 'URY', 'Uzbekistan': 'UZB', 
    'Vanuatu': 'VUT', 'Vatican City': 'VAT', 'Venezuela': 'VEN', 'Vietnam': 'VNM', 'Yemen': 'YEM', 
    'Zambia': 'ZMB', 'Zimbabwe': 'ZWE'
}


# Main content area
st.title("Global Markets Dashboard")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Quotes", "Charts", "Analytics"])

# with tab1:
#     render_overview_tab()
# with tab2:
#     render_quotes_tab()
# with tab3:
#     render_charts_tab()
# with tab4:
#     render_analytics_tab()

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        metric = st.selectbox(
            "Metric ▼",
            [
                "Stock Indices % Change", 
                "Currency vs USD % Change", 
                "Market Status (Open/Closed)"
            ],
            index=0
        )
    with col2:
        # Single date picker instead of range
        selected_date = st.date_input(
            "Select Date",
            value=datetime.date.today(),
            min_value=datetime.date(2000, 1, 1),
            max_value=datetime.date.today(),
            key="date_picker"
        )
        
        # Handle the single date
        start_date = end_date = selected_date

    # Optional: Add time inputs for hour/minute precision
    if start_date and end_date:
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input(
                "Start Time",
                value=datetime.time(9, 30),  # Market open time (9:30 AM ET)
                key="start_time"
            )
        with col2:
            end_time = st.time_input(
                "End Time", 
                value=datetime.time(16, 0),  # Market close time (4:00 PM ET)
                key="end_time"
            )
        
        # Combine date and time
        start_datetime = datetime.datetime.combine(start_date, start_time)
        end_datetime = datetime.datetime.combine(end_date, end_time)
    else:
        start_datetime = end_datetime = None

    st.markdown("---")

    # — Global Choropleth Placeholder —
    st.subheader("World Market Overview")
    
    # Sample country data that would come from API endpoints
    country_data = countries_with_indices
    
    # Determine what data to show based on selected metric
    if metric == "Stock Indices % Change":
        z_values = [country_data[country]['change_pct'] for country in country_data.keys()]
        title = "Stock Market Performance (%)"
        colorscale = 'RdYlGn'
    elif metric == "Currency vs USD % Change":
        # Simulate currency changes vs USD
        currency_changes = [0.0, -0.15, 0.08, -0.22, -0.15, -0.15, -0.15, -0.05, -0.12, 0.45, 0.02, -0.08, 0.18, -0.25]
        z_values = currency_changes
        title = "Currency Performance vs USD (%)"
        colorscale = 'RdYlGn'
    elif metric == "Market Status (Open/Closed)":
        z_values = [1 if country_data[country]['is_open'] else 0 for country in country_data.keys()]
        title = "Market Status (1=Open, 0=Closed)"
        colorscale = 'Blues'
    else:
        # Default to stock indices
        z_values = [country_data[country]['change_pct'] for country in country_data.keys()]
        title = "Stock Market Performance (%)"
        colorscale = 'RdYlGn'
    
    # Create the world map
    fig = go.Figure(data=go.Choropleth(
        locations=list(country_data.keys()),
        z=z_values,
        locationmode='ISO-3',
        colorscale=colorscale,
        showscale=True,
        marker_line_color='rgba(0,0,0,0.2)',
        marker_line_width=0.5,
        colorbar=dict(
            title=title
        ),
        hovertemplate="<b>%{location}</b><br>" +
                     f"{title}: %{{z:.2f}}<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        title=f"{metric}",
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular',
            showland=True,
            landcolor='lightgray',
            showocean=True,
            oceancolor='lightblue',
            coastlinecolor='white',
            coastlinewidth=1,
        ),
        height=500,
        margin=dict(l=0, r=0, t=50, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

    # — Detail Panel Placeholder (on "click") —
    if 'clicked_country' not in st.session_state:
        st.session_state.clicked_country = ""
    # simulate a click by picking from a dropdown (remove in real version)
    country = st.selectbox(
        "Select Country",
        [""] + countries,
        key="country_sim"
    )
    if country:
        st.session_state.clicked_country = country

    if st.session_state.clicked_country:
        st.markdown(f"#### Market Details for {st.session_state.clicked_country}")
        
        # Check if country has stock index data
        country_code = None
        # Use the mapping to get country code from full country name
        if st.session_state.clicked_country in country_name_to_code:
            country_code = country_name_to_code[st.session_state.clicked_country]
        
        st.write(f"Country code: {country_code}")
        if country_code and country_code in countries_with_indices:
            # Country has stock index - show detailed market data
            country_data = countries_with_indices[country_code]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Stock Market**")
                st.write(f"- **Index**: {country_data['name']} ({country_data['index']})")
                st.write(f"- **Current**: {country_data['change_pct']:+.2f}%")
                st.write(f"- **Status**: {'Open' if country_data['is_open'] else '🔴 Closed'}")
                st.write(f"- **Currency**: {country_data['currency']}")
            
            with col2:
                st.markdown("**Currency vs USD**")
                # Simulate currency data from /exchange_rate endpoint
                if country_data['currency'] != 'USD':
                    currency_pair = f"{country_data['currency']}/USD"
                    st.write(f"- **Pair**: {currency_pair}")
                    st.write(f"- **Rate**: 1.0850")  # Would come from /exchange_rate
                    st.write(f"- **Change**: -0.15%")  # Would come from /exchange_rate
                else:
                    st.write("- **Base Currency**: USD")
                    st.write("- **No conversion needed**")
            
            # Market movers for this country
            st.markdown("**Top Market Movers**")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("*Top Gainers*")
                st.write("- **Stock A**: +4.2%")
                st.write("- **Stock B**: +3.1%")
                st.write("- **Stock C**: +2.8%")
            with col2:
                st.markdown("*Top Losers*")
                st.write("- **Stock X**: -2.1%")
                st.write("- **Stock Y**: -1.8%")
                st.write("- **Stock Z**: -1.5%")
            
            # Historical performance sparkline
            st.markdown("**7-Day Performance**")
            # Generate sample data for sparkline
            import random
            sparkline_data = [100 + random.uniform(-5, 5) for _ in range(7)]
            st.line_chart(sparkline_data)
            
        else:
            # Country without stock index - show basic info
            st.markdown("**Country Information**")
            st.write(f"- **ISO Code**: {country_code}")
            st.write("- **Market Data**: Limited availability")
            st.write("- **Currency**: Available via forex pairs")
            st.write("- **Trading**: Check individual exchanges")
            
            # Show currency data if available
            st.markdown("**Currency Information**")
            # This would use /countries endpoint to get currency info
            st.write("- **Local Currency**: Available via API")
            st.write("- **Exchange Rate**: Check forex pairs")
            st.write("- **Market Status**: Varies by exchange")
                    
    st.markdown("---")

    # — Top Movers / KPIs Placeholders —
    st.subheader("Market Summary")
    g1, g2, g3 = st.columns(3)
    with g1:
        st.markdown("**Top Gainers**")
        st.write("- **TSLA**: +5.28%")
        st.write("- **NVDA**: +3.24%")
        st.write("- **META**: +1.72%")
        st.write("- **GOOGL**: +0.55%")
        st.write("- **AAPL**: +1.34%")
    with g2:
        st.markdown("**Top Losers**")
        st.write("- **AMZN**: -2.10%")
        st.write("- **NFLX**: -1.68%")
        st.write("- **MSFT**: -0.32%")
        st.write("- **BRK.A**: -0.15%")
        st.write("- **JPM**: -0.08%")
    with g3:
        st.markdown("**Regional Performance**")
        st.write("- **US Markets**: +0.8%")
        st.write("- **European Markets**: -0.3%")
        st.write("- **Asian Markets**: +1.2%")
        st.write("- **African Markets**: +0.5%")
        
        # Subtle methodology note
        st.caption("*Based on major indices: US (S&P 500, NASDAQ, Dow), Europe (DAX, FTSE, CAC), Asia (Nikkei, Shanghai, NIFTY), Africa (JSE Top 40, EGX 30)*")

with tab2:    
    # Initialize session state for settings
    if 'rows_per_page' not in st.session_state:
        st.session_state.rows_per_page = 25
    if 'search_filter' not in st.session_state:
        st.session_state.search_filter = ""
    if 'sort_column' not in st.session_state:
        st.session_state.sort_column = "ticker"
    if 'sort_direction' not in st.session_state:
        st.session_state.sort_direction = "asc"
    if 'selected_stock' not in st.session_state:
        st.session_state.selected_stock = None
    if 'show_stock_modal' not in st.session_state:
        st.session_state.show_stock_modal = False
    
    # Static sample data (no real-time fetching)
    sample_quotes = [
        {"ticker": "AAPL", "name": "Apple Inc.", "last_price": 185.92, "change": 2.45, "change_pct": 1.34, "volume": 1250000, "bid": 185.90, "ask": 185.95, "day_high": 186.45, "day_low": 184.20, "year_high": 198.23, "year_low": 124.17, "market_cap": "2.89T"},
        {"ticker": "MSFT", "name": "Microsoft Corp.", "last_price": 378.85, "change": -1.23, "change_pct": -0.32, "volume": 890000, "bid": 378.80, "ask": 378.90, "day_high": 379.50, "day_low": 377.20, "year_high": 420.00, "year_low": 280.00, "market_cap": "2.81T"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "last_price": 142.56, "change": 0.78, "change_pct": 0.55, "volume": 2100000, "bid": 142.50, "ask": 142.60, "day_high": 143.20, "day_low": 141.80, "year_high": 150.00, "year_low": 120.00, "market_cap": "1.79T"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "last_price": 145.24, "change": -3.12, "change_pct": -2.10, "volume": 3400000, "bid": 145.20, "ask": 145.30, "day_high": 148.50, "day_low": 144.80, "year_high": 160.00, "year_low": 100.00, "market_cap": "1.51T"},
        {"ticker": "TSLA", "name": "Tesla Inc.", "last_price": 248.50, "change": 12.45, "change_pct": 5.28, "volume": 5600000, "bid": 248.40, "ask": 248.60, "day_high": 250.00, "day_low": 240.00, "year_high": 300.00, "year_low": 150.00, "market_cap": "789B"},
        {"ticker": "META", "name": "Meta Platforms Inc.", "last_price": 334.69, "change": 5.67, "change_pct": 1.72, "volume": 1800000, "bid": 334.60, "ask": 334.80, "day_high": 335.50, "day_low": 330.00, "year_high": 380.00, "year_low": 200.00, "market_cap": "851B"},
        {"ticker": "NVDA", "name": "NVIDIA Corp.", "last_price": 485.09, "change": 15.23, "change_pct": 3.24, "volume": 4200000, "bid": 485.00, "ask": 485.20, "day_high": 490.00, "day_low": 480.00, "year_high": 500.00, "year_low": 300.00, "market_cap": "1.20T"},
        {"ticker": "NFLX", "name": "Netflix Inc.", "last_price": 492.98, "change": -8.45, "change_pct": -1.68, "volume": 950000, "bid": 492.90, "ask": 493.10, "day_high": 500.00, "day_low": 490.00, "year_high": 550.00, "year_low": 400.00, "market_cap": "218B"},
    ]

    # Controls Row
    quotes_df = backend.data_fetching.get_top_stocks_quotes()
    quotes_df = quotes_df.drop(columns=['open'])
    search_filter = st.text_input(
        "Search (Ticker/Name)",
        placeholder="AAPL, Apple...",
        key="search_control"
    )
    if search_filter:
        search = search_filter.lower()
        quotes_df = quotes_df[
            quotes_df['ticker'].str.lower().str.contains(search) |
            quotes_df['name'].str.lower().str.contains(search)
        ]

    
    # Price Grid
    st.markdown("### Price Grid")
    st.markdown("**Click on the stock to view details**")
    # --- AG Grid setup ---
    # Before building the grid, drop unnecessary columns for display
    columns_to_drop = ['currency', 'bid', 'ask', 'year_high', 'year_low', 'market_cap']
    display_df = quotes_df.drop(columns=[col for col in columns_to_drop if col in quotes_df.columns], errors='ignore')

    gb = GridOptionsBuilder.from_dataframe(display_df)
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    gb.configure_default_column(editable=False, groupable=False)
    gb.configure_selection('single', use_checkbox=False)
    gb.configure_column(
        "last_price",
        header_name="Last Price",
        type=["numericColumn"],
        valueFormatter="`$${x.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`"
    )
    gb.configure_column(
        "day_high",
        header_name="Day High",
        type=["numericColumn"],
        valueFormatter="`$${x.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`"
    )
    gb.configure_column(
        "day_low",
        header_name="Day Low",
        type=["numericColumn"],
        valueFormatter="`$${x.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`"
    )
    gb.configure_column("change", header_name="Change", type=["numericColumn"], valueFormatter="x.toFixed(2)")
    gb.configure_column("change_pct", header_name="% Change", type=["numericColumn"], valueFormatter="x.toFixed(2) + '%'")
    gb.configure_column("volume", header_name="Volume", type=["numericColumn"])
    gb.configure_column(
        "volume",
        header_name="Volume",
        type=["numericColumn"],
        valueFormatter="x.toLocaleString()"
    )
    gridOptions = gb.build()
    gridOptions['enableRangeSelection'] = True
    gridOptions['enableCellTextSelection'] = True
    # --- AG Grid display ---
    
    response = AgGrid(
        display_df,
        gridOptions=gridOptions,
        update_mode=GridUpdateMode.MODEL_CHANGED | GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True,
        theme='streamlit',
        fit_columns_on_grid_load=True,
        height=400
    )
    selected_rows = response['selected_rows']
    if isinstance(selected_rows, pd.DataFrame) and len(selected_rows) > 0:
        selected_ticker = selected_rows.iloc[0]['ticker']
        st.session_state.selected_stock = selected_ticker
        st.session_state.show_stock_modal = True
    else:
        pass
        

    st.session_state.search_filter = search_filter
    
    # Default to 25 rows
    st.session_state.rows_per_page = 5
    
    # st.markdown("---")
    
    # Filter and sort data
    filtered_quotes = sample_quotes
    if st.session_state.search_filter:
        # Use fuzzy search instead of simple contains
        filtered_quotes = fuzzy_search(st.session_state.search_filter, sample_quotes, threshold=2)
    
    # Show fuzzy search indicator
    if st.session_state.search_filter and len(filtered_quotes) < len(sample_quotes):
        st.caption(f"Found {len(filtered_quotes)} matches for '{st.session_state.search_filter}'")
    st.caption(f"Data source: Yahoo Finance | Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")    # --- Handle ticker button click ---

    # # Sorting controls
    # sort_col1, sort_col2 = st.columns(2)
    # with sort_col1:
    #     sort_column = st.selectbox(
    #         "Sort by",
    #         ["Ticker", "Name", "Last Price", "% Change", "Volume"],
    #         index=0,
    #         key="sort_column_control"
    #     )
    #     st.session_state.sort_column = sort_column.lower().replace(" ", "_")
    
    # with sort_col2:
    #     sort_direction = st.selectbox(
    #         "Direction",
    #         ["Ascending", "Descending"],
    #         index=0,
    #         key="sort_direction_control"
    #     )
    #     st.session_state.sort_direction = "asc" if sort_direction == "Ascending" else "desc"
    
    # # Sort data
    # reverse_sort = st.session_state.sort_direction == "desc"
    # if st.session_state.sort_column == "ticker":
    #     filtered_quotes.sort(key=lambda x: x["ticker"], reverse=reverse_sort)
    # elif st.session_state.sort_column == "name":
    #     filtered_quotes.sort(key=lambda x: x["name"], reverse=reverse_sort)
    # elif st.session_state.sort_column == "last_price":
    #     filtered_quotes.sort(key=lambda x: x["last_price"], reverse=reverse_sort)
    # elif st.session_state.sort_column == "change_pct":
    #     filtered_quotes.sort(key=lambda x: x["change_pct"], reverse=reverse_sort)
    # elif st.session_state.sort_column == "volume":
    #     filtered_quotes.sort(key=lambda x: x["volume"], reverse=reverse_sort)
    
    # # Pagination
    # total_rows = len(filtered_quotes)
    # total_pages = (total_rows + st.session_state.rows_per_page - 1) // st.session_state.rows_per_page
    
    # if 'current_page' not in st.session_state:
    #     st.session_state.current_page = 0
    
    # # Get current page data
    # start_idx = st.session_state.current_page * st.session_state.rows_per_page
    # end_idx = min(start_idx + st.session_state.rows_per_page, total_rows)
    # current_page_data = filtered_quotes[start_idx:end_idx]

    
    # # Create the data grid using st.dataframe
    # if len(current_page_data) > 0:
    #     # Prepare data for display
    #     display_data = []
    #     for quote in current_page_data:
    #         # Format volume
    #         if quote["volume"] >= 1000000:
    #             volume_str = f"{quote['volume']/1000000:.1f}M"
    #         elif quote["volume"] >= 1000:
    #             volume_str = f"{quote['volume']/1000:.1f}K"
    #         else:
    #             volume_str = str(quote["volume"])
            
    #         # Determine color for change
    #         change_color = "🟢" if quote["change"] >= 0 else "🔴"
            
    #         display_data.append({
    #             "Ticker": quote["ticker"],
    #             "Name": quote["name"],
    #             "Last Price": f"${quote['last_price']:.2f}",
    #             "Change": f"{change_color} {quote['change']:+.2f}",
    #             "% Change": f"{quote['change_pct']:+.2f}%",
    #             "Volume": volume_str,
    #             "Bid": f"${quote['bid']:.2f}",
    #             "Ask": f"${quote['ask']:.2f}"
    #         })
        
    #     # Create dataframe
    #     df = pd.DataFrame(display_data)
        
    #     # Display as clickable table rows using buttons

    #     # Header row
    #     col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 3, 2, 2, 2, 2, 2, 2])
    #     with col1:
    #         st.markdown("**Ticker**")
    #     with col2:
    #         st.markdown("**Name**")
    #     with col3:
    #         st.markdown("**Last Price**")
    #     with col4:
    #         st.markdown("**Change**")
    #     with col5:
    #         st.markdown("**% Change**")
    #     with col6:
    #         st.markdown("**Volume**")
    #     with col7:
    #         st.markdown("**Bid**")
    #     with col8:
    #         st.markdown("**Ask**")
        
    #     # Data rows as clickable buttons
    #     for i, quote in enumerate(current_page_data):
    #         col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2, 3, 2, 2, 2, 2, 2, 2])
            
    #         with col1:
    #             if st.button(f"**{quote['ticker']}**", key=f"ticker_{quote['ticker']}_{i}", use_container_width=True):
    #                 st.session_state.selected_stock = quote['ticker']
    #                 st.session_state.show_stock_modal = True
    #                 st.rerun()
            
    #         with col2:
    #             st.write(quote['name'])
    #         with col3:
    #             st.write(f"${quote['last_price']:.2f}")
    #         with col4:
    #             st.write(f"{quote['change']:+.2f}")
    #         with col5:
    #             st.write(f"{quote['change_pct']:+.2f}%")
    #         with col6:
    #             st.write(quote['volume'])
    #         with col7:
    #             st.write(f"${quote['bid']:.2f}")
    #         with col8:
    #             st.write(f"${quote['ask']:.2f}")
        
    #     # Pagination - moved below the table but above the stock selector
    #     if total_pages > 1:        
    #         # Calculate which page numbers to show
    #         current = st.session_state.current_page + 1
    #         max_pages = total_pages
            
    #         # Show page numbers (Google-style)
    #         page_numbers = []
            
    #         # Always show first page
    #         page_numbers.append(1)
            
    #         # Show pages around current page
    #         start_page = max(2, current - 2)
    #         end_page = min(max_pages - 1, current + 2)
            
    #         # Add ellipsis if there's a gap
    #         if start_page > 2:
    #             page_numbers.append("...")
            
    #         # Add middle pages
    #         for page in range(start_page, end_page + 1):
    #             if page not in page_numbers:
    #                 page_numbers.append(page)
            
    #         # Add ellipsis if there's a gap
    #         if end_page < max_pages - 1:
    #             page_numbers.append("...")
            
    #         # Always show last page
    #         if max_pages not in page_numbers:
    #             page_numbers.append(max_pages)
            
    #         # Create elegant pagination using Streamlit's built-in functions
    #         total_buttons = len(page_numbers) + 2  # +2 for Previous/Next
            
    #         # Center the pagination with proper spacing
    #         # Use more columns for better centering
    #         if total_buttons <= 7:
    #             # Small pagination: [space] [buttons] [space]
    #             cols = st.columns([1] + [1] * total_buttons + [1])
    #         else:
    #             # Large pagination: [more space] [buttons] [more space]
    #             cols = st.columns([2] + [1] * total_buttons + [2])
            
    #         # Previous button
    #         with cols[1]:
    #             if st.button("◀", disabled=current == 1, key="prev_page", type="secondary"):
    #                 st.session_state.current_page = max(0, current - 2)
    #                 st.rerun()
            
    #         # Page number buttons
    #         for i, page_num in enumerate(page_numbers):
    #             with cols[i + 2]:
    #                 if page_num == "...":
    #                     st.write("...")
    #                 elif page_num == current:
    #                     # Current page - highlighted with Streamlit styling
    #                     st.write(f"**{page_num}**")
    #                 else:
    #                     # Other pages - clickable
    #                     if st.button(str(page_num), key=f"page_{page_num}", type="secondary"):
    #                         st.session_state.current_page = page_num - 1
    #                         st.rerun()
            
    #         # Next button
    #         with cols[-2]:
    #             if st.button("▶", disabled=current == max_pages, key="next_page", type="secondary"):
    #                 st.session_state.current_page = min(max_pages - 1, current)
    #                 st.rerun()
            
    #         # Page info
    #         st.caption(f"Showing {total_rows} results across {total_pages} pages")
    #         st.caption("**Source:** Data retrieved from 12data API on June 10, 2024.")

    # else:
    #     st.warning("No stocks found matching your search criteria.")

    st.markdown("---")
    
    # Detail Modal
    if st.session_state.show_stock_modal and st.session_state.selected_stock:
        # Find the selected stock data from quotes_df
        selected_row = quotes_df[quotes_df['ticker'] == st.session_state.selected_stock]
        selected_stock_data = None
        if not selected_row.empty:
            selected_stock_data = selected_row.iloc[0]
        
        if selected_stock_data is not None:
            with st.container():
                # Header with close button
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"### {selected_stock_data['ticker']} - {selected_stock_data['name']} (Detail View)")
                with col2:
                    if st.button("Close", key="close_modal"):
                        st.session_state.show_stock_modal = False
                        st.session_state.selected_stock = None
                        st.rerun()
                
                # Time interval selector
                interval_map = {
                    "1 minute": ("1m", "1d"),
                    "5 minutes": ("5m", "1d"),
                    "15 minutes": ("15m", "1d"),
                    "1 hour": ("1h", "1mo"),
                    "1 day": ("1d", "1y"),
                }
                interval_label = st.selectbox(
                    "Time Interval:",
                    list(interval_map.keys()),
                    index=1,  # Default to 5 minutes
                    key="time_interval"
                )
                interval, period = interval_map[interval_label]
                
                # Fetch real OHLC data from Yahoo Finance
                try:
                    data = yf.Ticker(selected_stock_data['ticker']).history(interval=interval, period=period)
                except Exception as e:
                    data = None
                    st.warning(f"Error fetching data: {e}")
                
                if data is not None and not data.empty:
                    fig_candlestick = go.Figure(data=[go.Candlestick(
                        x=data.index,
                        open=data['Open'],
                        high=data['High'],
                        low=data['Low'],
                        close=data['Close'],
                        increasing_line_color='#26a69a',
                        decreasing_line_color='#ef5350',
                        increasing_fillcolor='#26a69a',
                        decreasing_fillcolor='#ef5350',
                        name=selected_stock_data['ticker']
                    )])
                    fig_candlestick.update_layout(
                        title=f"{selected_stock_data['ticker']} Candlestick Chart ({interval_label})",
                        xaxis_title="Time",
                        yaxis_title="Price ($)",
                        height=500,
                        xaxis_rangeslider_visible=False,
                        template="plotly_white"
                    )
                    # Add volume bars
                    fig_candlestick.add_trace(go.Bar(
                        x=data.index,
                        y=data['Volume'],
                        name="Volume",
                        yaxis="y2",
                        opacity=0.3,
                        marker_color='lightblue'
                    ))
                    fig_candlestick.update_layout(
                        yaxis2=dict(
                            title="Volume",
                            overlaying="y",
                            side="right"
                        )
                    )
                    st.plotly_chart(fig_candlestick, use_container_width=True)
                else:
                    st.warning("No candlestick data available for this interval.")
                
                # Stats
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Current Price", f"${selected_stock_data['last_price']:.2f}")
                with col2:
                    st.metric("Day High", f"${selected_stock_data['day_high']:.2f}")
                with col3:
                    st.metric("Day Low", f"${selected_stock_data['day_low']:.2f}")
                with col4:
                    st.metric("Volume", f"{selected_stock_data['volume']:,}")
                
                # Key stats panel
                st.markdown("### Key Statistics")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Bid/Ask:** ${selected_stock_data['bid']:.2f} / ${selected_stock_data['ask']:.2f}")
                    st.write(f"**52W High:** ${selected_stock_data['year_high']:.2f}")
                    st.write(f"**52W Low:** ${selected_stock_data['year_low']:.2f}")
                with col2:
                    st.write(f"**Market Cap:** {selected_stock_data['market_cap']}")
                    st.write(f"**Volume:** {selected_stock_data['volume']:,}")
                    st.write(f"**Change:** {selected_stock_data['change']:+.2f} ({selected_stock_data['change_pct']:+.2f}%)")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    # Create sample CSV data for download
                    if data is not None and not data.empty:
                        df_export = data.reset_index()[['Datetime' if 'Datetime' in data.reset_index().columns else data.index.name, 'Open', 'High', 'Low', 'Close', 'Volume']]
                        st.download_button(
                            label="Download CSV",
                            data=df_export.to_csv(index=False),
                            file_name=f"{selected_stock_data['ticker']}_{interval.replace(' ', '_')}.csv",
                            mime="text/csv"
                        )
                with col2:
                    # Empty column for layout balance
                    st.write("")
                # Footer with external link
                st.markdown("---")
                st.markdown(f"[View {selected_stock_data['ticker']} on Yahoo Finance](https://finance.yahoo.com/quote/{selected_stock_data['ticker']})")
                st.markdown('</div>', unsafe_allow_html=True)


with tab3:
    st.subheader("Charts & Technical Analysis")
    
    # Initialize session state for chart settings
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = ""
    if 'selected_interval' not in st.session_state:
        st.session_state.selected_interval = "1 day"
    if 'selected_date_range' not in st.session_state:
        st.session_state.selected_date_range = "1 M"
    if 'chart_type' not in st.session_state:
        st.session_state.chart_type = "OHLC"
    if 'show_volume' not in st.session_state:
        st.session_state.show_volume = True
    if 'show_sma' not in st.session_state:
        st.session_state.show_sma = False
    if 'show_ema' not in st.session_state:
        st.session_state.show_ema = False
    if 'show_bollinger' not in st.session_state:
        st.session_state.show_bollinger = False
    if 'show_rsi' not in st.session_state:
        st.session_state.show_rsi = False
    
    # Sample symbols data (in real app, this would come from API)
    sample_symbols = [
        {"ticker": "AAPL", "name": "Apple Inc.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "MSFT", "name": "Microsoft Corp.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "TSLA", "name": "Tesla Inc.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "META", "name": "Meta Platforms Inc.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "NVDA", "name": "NVIDIA Corp.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "NFLX", "name": "Netflix Inc.", "country": "USA", "asset_class": "Equity"},
        {"ticker": "^GSPC", "name": "S&P 500 Index", "country": "USA", "asset_class": "Index"},
        {"ticker": "^DJI", "name": "Dow Jones Industrial Average", "country": "USA", "asset_class": "Index"},
        {"ticker": "^IXIC", "name": "NASDAQ Composite", "country": "USA", "asset_class": "Index"},
        {"ticker": "EURUSD", "name": "Euro / US Dollar", "country": "Global", "asset_class": "Forex"},
        {"ticker": "GBPUSD", "name": "British Pound / US Dollar", "country": "Global", "asset_class": "Forex"},
        {"ticker": "GC=F", "name": "Gold Futures", "country": "Global", "asset_class": "Commodity"},
        {"ticker": "BTC-USD", "name": "Bitcoin", "country": "Global", "asset_class": "Crypto"},
    ]
    
    # Favorites (in real app, this would come from watchlist)
    favorites = ["AAPL", "MSFT", "TSLA"]
    
    # Chart Controls Section    
    # Symbol & Interval Selector Row
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col1:
        # Symbol Dropdown with built-in search functionality
        # Create symbol options with favorites at top
        symbol_options = []
        symbol_options.append("")  # Empty option
        
        # Add favorites first
        for fav in favorites:
            for symbol in sample_symbols:
                if symbol["ticker"] == fav:
                    symbol_options.append(f"{symbol['ticker']} - {symbol['name']}")
                    break
        
        # Add remaining symbols
        for symbol in sample_symbols:
            if symbol["ticker"] not in favorites:
                symbol_options.append(f"{symbol['ticker']} - {symbol['name']}")
        
        selected_symbol_full = st.selectbox(
            "Symbol",
            symbol_options,
            key="symbol_selector"
        )
        
        # Extract ticker from selection
        if selected_symbol_full and selected_symbol_full != "":
            if selected_symbol_full.startswith("⭐ "):
                st.session_state.selected_symbol = selected_symbol_full.split(" - ")[0][2:]  # Remove "⭐ "
            else:
                st.session_state.selected_symbol = selected_symbol_full.split(" - ")[0]
        else:
            st.session_state.selected_symbol = ""
    
    with col2:
        # Interval Picker with dynamic filtering based on date range
        # Define valid intervals for each date range
        interval_mapping = {
            "1 D": ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour", "1 day"],
            "5 D": ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour", "1 day", "1 week"],
            "1 M": ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour", "1 day", "1 week", "1 month"],
            "3 M": ["1 hour", "1 day", "1 week", "1 month"],
            "6 M": ["1 day", "1 week", "1 month"],
            "YTD": ["1 day", "1 week", "1 month"],
            "1 Y": ["1 day", "1 week", "1 month"],
            "5 Y": ["1 day", "1 week", "1 month"],
            "Max": ["1 day", "1 week", "1 month"],
            "Custom": ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour", "1 day", "1 week", "1 month"]
        }
        
        # Get valid intervals for current date range
        current_date_range = st.session_state.selected_date_range if 'selected_date_range' in st.session_state else "1 M"
        valid_intervals = interval_mapping.get(current_date_range, ["1 day"])
        
        # Find the index of the current selected interval in valid intervals
        current_interval = st.session_state.selected_interval if 'selected_interval' in st.session_state else "1 day"
        if current_interval in valid_intervals:
            default_index = valid_intervals.index(current_interval)
        else:
            default_index = 0  # Default to first valid interval
        
        st.session_state.selected_interval = st.selectbox(
            "Interval",
            valid_intervals,
            index=default_index,
            key="interval_selector"
        )
    
    with col3:
        # Date Range Picker
        date_range_options = ["1 D", "5 D", "1 M", "3 M", "6 M", "YTD", "1 Y", "5 Y", "Max", "Custom"]
        st.session_state.selected_date_range = st.selectbox(
            "Date Range",
            date_range_options,
            index=2,  # Default to 1 M
            key="date_range_selector"
        )
        
        # Custom date range picker
        if st.session_state.selected_date_range == "Custom":
            custom_start = st.date_input("Start Date", value=datetime.date.today() - datetime.timedelta(days=30))
            custom_end = st.date_input("End Date", value=datetime.date.today())
    
    st.markdown("---")
    
    # Chart Type & Indicators Row
    col1, col2, col3 = st.columns([2, 2, 2])
    
    with col1:
        # Chart Type
        chart_types = ["OHLC", "Line"]
        st.session_state.chart_type = st.selectbox(
            "Chart Type",
            chart_types,
            key="chart_type_selector"
        )
        
        # Volume Toggle
        st.session_state.show_volume = st.checkbox(
            "Show Volume",
            value=True,
            key="volume_toggle"
        )
    
    with col2:
        # Technical Indicators
        st.markdown("**Indicators**")
        st.session_state.show_sma = st.checkbox("SMA", key="sma_toggle")
        st.session_state.show_ema = st.checkbox("EMA", key="ema_toggle")
        st.session_state.show_wma = st.checkbox("WMA", key="wma_toggle")
        st.session_state.show_hma = st.checkbox("HMA", key="hma_toggle")
        st.session_state.show_vwap = st.checkbox("VWAP", key="vwap_toggle")
    
    with col3:
        st.markdown("**Advanced**")
        st.session_state.show_bollinger = st.checkbox("Bollinger Bands", key="bollinger_toggle")
        st.session_state.show_rsi = st.checkbox("RSI", key="rsi_toggle")
        st.session_state.show_macd = st.checkbox("MACD", key="macd_toggle")
        st.session_state.show_stochastic = st.checkbox("Stochastic", key="stochastic_toggle")
        st.session_state.show_williams_r = st.checkbox("Williams %R", key="williams_r_toggle")
        st.session_state.show_atr = st.checkbox("ATR", key="atr_toggle")

    
    # Indicator Parameters (when enabled)
    if (st.session_state.show_sma or st.session_state.show_ema or st.session_state.show_wma or 
        st.session_state.show_hma or st.session_state.show_vwap or st.session_state.show_bollinger or 
        st.session_state.show_rsi or st.session_state.show_macd or st.session_state.show_stochastic or 
        st.session_state.show_williams_r or st.session_state.show_atr):
        
        st.markdown("### Indicator Parameters")
        indicator_col1, indicator_col2, indicator_col3, indicator_col4 = st.columns(4)
        
        with indicator_col1:
            if st.session_state.show_sma:
                sma_period = st.number_input("SMA Period", min_value=5, max_value=200, value=20, key="sma_period")
            if st.session_state.show_ema:
                ema_period = st.number_input("EMA Period", min_value=5, max_value=200, value=20, key="ema_period")
            if st.session_state.show_wma:
                wma_period = st.number_input("WMA Period", min_value=5, max_value=200, value=20, key="wma_period")
            if st.session_state.show_hma:
                hma_period = st.number_input("HMA Period", min_value=5, max_value=200, value=20, key="hma_period")
        
        with indicator_col2:
            if st.session_state.show_bollinger:
                bb_period = st.number_input("BB Period", min_value=5, max_value=200, value=20, key="bb_period")
                bb_std = st.number_input("BB Std Dev", min_value=0.5, max_value=3.0, value=2.0, step=0.1, key="bb_std")
            if st.session_state.show_rsi:
                rsi_period = st.number_input("RSI Period", min_value=5, max_value=50, value=14, key="rsi_period")
            if st.session_state.show_macd:
                macd_fast = st.number_input("MACD Fast", min_value=5, max_value=50, value=12, key="macd_fast")
                macd_slow = st.number_input("MACD Slow", min_value=10, max_value=100, value=26, key="macd_slow")
                macd_signal = st.number_input("MACD Signal", min_value=5, max_value=50, value=9, key="macd_signal")
        
        with indicator_col3:
            if st.session_state.show_stochastic:
                stoch_k = st.number_input("Stoch %K", min_value=5, max_value=50, value=14, key="stoch_k")
                stoch_d = st.number_input("Stoch %D", min_value=3, max_value=20, value=3, key="stoch_d")
            if st.session_state.show_williams_r:
                williams_r_period = st.number_input("Williams %R Period", min_value=5, max_value=50, value=14, key="williams_r_period")
            if st.session_state.show_atr:
                atr_period = st.number_input("ATR Period", min_value=5, max_value=50, value=14, key="atr_period")
        
        with indicator_col4:
            # Additional parameters can go here
            st.write("")
    
    #st.markdown("---")
    
    # Main Chart Area
    if st.session_state.selected_symbol:
        st.markdown(f"### {st.session_state.selected_symbol} Chart")
        
        # Generate sample data based on selected parameters
        current_time = pd.Timestamp.now()
        
        # Determine number of periods based on date range and interval
        if st.session_state.selected_date_range == "1 D":
            if "hour" in st.session_state.selected_interval:
                periods = 24
            elif "minute" in st.session_state.selected_interval:
                if st.session_state.selected_interval == "1 minute":
                    periods = 1440  # 24 hours * 60 minutes
                elif st.session_state.selected_interval == "5 minutes":
                    periods = 288   # 24 hours * 12 (5-min intervals)
                elif st.session_state.selected_interval == "15 minutes":
                    periods = 96    # 24 hours * 4 (15-min intervals)
                else:
                    periods = 48    # 24 hours * 2 (30-min intervals)
            else:
                periods = 1  # 1 day
        elif st.session_state.selected_date_range == "5 D":
            if "hour" in st.session_state.selected_interval:
                periods = 120  # 5 days * 24 hours
            elif "minute" in st.session_state.selected_interval:
                if st.session_state.selected_interval == "1 minute":
                    periods = 7200  # 5 days * 24 hours * 60 minutes
                elif st.session_state.selected_interval == "5 minutes":
                    periods = 1440  # 5 days * 24 hours * 12
                elif st.session_state.selected_interval == "15 minutes":
                    periods = 480   # 5 days * 24 hours * 4
                else:
                    periods = 240   # 5 days * 24 hours * 2
            else:
                periods = 5  # 5 days
        elif st.session_state.selected_date_range == "1 M":
            if "hour" in st.session_state.selected_interval:
                periods = 720  # ~30 days * 24 hours
            elif "minute" in st.session_state.selected_interval:
                if st.session_state.selected_interval == "1 minute":
                    periods = 43200  # ~30 days * 24 hours * 60 minutes
                elif st.session_state.selected_interval == "5 minutes":
                    periods = 8640   # ~30 days * 24 hours * 12
                elif st.session_state.selected_interval == "15 minutes":
                    periods = 2880   # ~30 days * 24 hours * 4
                else:
                    periods = 1440   # ~30 days * 24 hours * 2
            elif st.session_state.selected_interval == "1 day":
                periods = 30  # ~30 days
            elif st.session_state.selected_interval == "1 week":
                periods = 4   # ~4 weeks
            elif st.session_state.selected_interval == "1 month":
                periods = 1   # 1 month
            else:
                periods = 30
        elif st.session_state.selected_date_range == "3 M":
            if "hour" in st.session_state.selected_interval:
                periods = 2160  # ~90 days * 24 hours
            elif "minute" in st.session_state.selected_interval:
                periods = 129600  # ~90 days * 24 hours * 60 minutes (too many, cap it)
            elif st.session_state.selected_interval == "1 day":
                periods = 90
            elif st.session_state.selected_interval == "1 week":
                periods = 12
            elif st.session_state.selected_interval == "1 month":
                periods = 3
            else:
                periods = 90
        elif st.session_state.selected_date_range == "6 M":
            if st.session_state.selected_interval == "1 day":
                periods = 180
            elif st.session_state.selected_interval == "1 week":
                periods = 26
            elif st.session_state.selected_interval == "1 month":
                periods = 6
            else:
                periods = 180
        elif st.session_state.selected_date_range == "1 Y":
            if st.session_state.selected_interval == "1 day":
                periods = 365
            elif st.session_state.selected_interval == "1 week":
                periods = 52
            elif st.session_state.selected_interval == "1 month":
                periods = 12
            else:
                periods = 365
        elif st.session_state.selected_date_range == "5 Y":
            if st.session_state.selected_interval == "1 day":
                periods = 1825
            elif st.session_state.selected_interval == "1 week":
                periods = 260
            elif st.session_state.selected_interval == "1 month":
                periods = 60
            else:
                periods = 1825
        else:  # Max
            if st.session_state.selected_interval == "1 day":
                periods = 3650
            elif st.session_state.selected_interval == "1 week":
                periods = 520
            elif st.session_state.selected_interval == "1 month":
                periods = 120
            else:
                periods = 3650
        
        # Generate time series
        if "minute" in st.session_state.selected_interval:
            if st.session_state.selected_interval == "1 minute":
                freq = "1min"
            elif st.session_state.selected_interval == "5 minutes":
                freq = "5min"
            elif st.session_state.selected_interval == "15 minutes":
                freq = "15min"
            elif st.session_state.selected_interval == "30 minutes":
                freq = "30min"
            else:
                freq = "1min"  # default fallback
        elif "hour" in st.session_state.selected_interval:
            if st.session_state.selected_interval == "1 hour":
                freq = "1H"
            elif st.session_state.selected_interval == "2 hours":
                freq = "2H"
            elif st.session_state.selected_interval == "4 hours":
                freq = "4H"
            else:
                freq = "1H"  # default fallback
        else:
            if st.session_state.selected_interval == "1 day":
                freq = "1D"
            elif st.session_state.selected_interval == "1 week":
                freq = "1W"
            elif st.session_state.selected_interval == "1 month":
                freq = "1M"
            else:
                freq = "1D"  # default fallback
        
        times = pd.date_range(end=current_time, periods=periods, freq=freq)
        
        # Generate OHLC data
        base_price = 100.0 + np.random.randint(0, 900)  # Make base_price float
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        current_price = base_price
        for i in range(periods):
            # Simulate price movement
            price_change = np.random.normal(0, base_price * 0.02)
            current_price += price_change
            
            # Create OHLC for this period
            open_price = current_price
            high_price = open_price + abs(np.random.normal(0, base_price * 0.01))
            low_price = open_price - abs(np.random.normal(0, base_price * 0.01))
            close_price = open_price + np.random.normal(0, base_price * 0.005)
            
            # Ensure high >= max(open, close) and low <= min(open, close)
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            opens.append(open_price)
            highs.append(high_price)
            lows.append(low_price)
            closes.append(close_price)
            volumes.append(np.random.randint(100000, 1000000))
            
            current_price = close_price
        
        # Create main chart
        fig = go.Figure()
        
        # Add main price data
        if st.session_state.chart_type == "OHLC":
            fig.add_trace(go.Candlestick(
                x=times,
                open=opens,
                high=highs,
                low=lows,
                close=closes,
                name=st.session_state.selected_symbol,
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350',
                increasing_fillcolor='#26a69a',
                decreasing_fillcolor='#ef5350'
            ))
        else:  # Line chart
            fig.add_trace(go.Scatter(
                x=times,
                y=closes,
                mode='lines',
                name=st.session_state.selected_symbol,
                line=dict(color='#1f77b4', width=2)
            ))
        
        # Add technical indicators
        if st.session_state.show_sma:
            sma_values = pd.Series(closes).rolling(window=sma_period).mean()
            fig.add_trace(go.Scatter(
                x=times,
                y=sma_values,
                mode='lines',
                name=f'SMA({sma_period})',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        if st.session_state.show_ema:
            ema_values = pd.Series(closes).ewm(span=ema_period).mean()
            fig.add_trace(go.Scatter(
                x=times,
                y=ema_values,
                mode='lines',
                name=f'EMA({ema_period})',
                line=dict(color='purple', width=1, dash='dash')
            ))
        
        if st.session_state.show_wma:
            # Calculate WMA (Weighted Moving Average)
            wma_values = []
            for i in range(len(closes)):
                if i < wma_period - 1:
                    wma_values.append(np.nan)
                else:
                    weights = list(range(1, wma_period + 1))
                    weighted_sum = sum(closes[i-j] * weights[j] for j in range(wma_period))
                    weight_sum = sum(weights)
                    wma_values.append(weighted_sum / weight_sum)
            
            fig.add_trace(go.Scatter(
                x=times,
                y=wma_values,
                mode='lines',
                name=f'WMA({wma_period})',
                line=dict(color='green', width=1, dash='dash')
            ))
        
        if st.session_state.show_hma:
            # Calculate HMA (Hull Moving Average)
            # HMA = WMA(2*WMA(n/2) - WMA(n)), where n is the period
            half_period = hma_period // 2
            sqrt_period = int(np.sqrt(hma_period))
            
            # Calculate WMA(n/2)
            wma_half = []
            for i in range(len(closes)):
                if i < half_period - 1:
                    wma_half.append(np.nan)
                else:
                    weights = list(range(1, half_period + 1))
                    weighted_sum = sum(closes[i-j] * weights[j] for j in range(half_period))
                    weight_sum = sum(weights)
                    wma_half.append(weighted_sum / weight_sum)
            
            # Calculate WMA(n)
            wma_full = []
            for i in range(len(closes)):
                if i < hma_period - 1:
                    wma_full.append(np.nan)
                else:
                    weights = list(range(1, hma_period + 1))
                    weighted_sum = sum(closes[i-j] * weights[j] for j in range(hma_period))
                    weight_sum = sum(weights)
                    wma_full.append(weighted_sum / weight_sum)
            
            # Calculate 2*WMA(n/2) - WMA(n)
            raw_hma = []
            for i in range(len(closes)):
                if pd.isna(wma_half[i]) or pd.isna(wma_full[i]):
                    raw_hma.append(np.nan)
                else:
                    raw_hma.append(2 * wma_half[i] - wma_full[i])
            
            # Calculate final HMA using WMA on the raw HMA values
            hma_values = []
            for i in range(len(raw_hma)):
                if i < sqrt_period - 1 or pd.isna(raw_hma[i]):
                    hma_values.append(np.nan)
                else:
                    weights = list(range(1, sqrt_period + 1))
                    weighted_sum = sum(raw_hma[i-j] * weights[j] for j in range(sqrt_period))
                    weight_sum = sum(weights)
                    hma_values.append(weighted_sum / weight_sum)
            
            fig.add_trace(go.Scatter(
                x=times,
                y=hma_values,
                mode='lines',
                name=f'HMA({hma_period})',
                line=dict(color='blue', width=1, dash='dash')
            ))
        
        if st.session_state.show_vwap:
            # Calculate VWAP (Volume Weighted Average Price)
            typical_prices = [(opens[i] + highs[i] + lows[i] + closes[i]) / 4 for i in range(len(opens))]
            vwap_values = []
            cumulative_tpv = 0  # Total Price Volume
            cumulative_volume = 0
            
            for i in range(len(typical_prices)):
                cumulative_tpv += typical_prices[i] * volumes[i]
                cumulative_volume += volumes[i]
                vwap_values.append(cumulative_tpv / cumulative_volume if cumulative_volume > 0 else typical_prices[i])
            
            fig.add_trace(go.Scatter(
                x=times,
                y=vwap_values,
                mode='lines',
                name='VWAP',
                line=dict(color='orange', width=1, dash='dash')
            ))
        
        if st.session_state.show_bollinger:
            bb_sma = pd.Series(closes).rolling(window=bb_period).mean()
            bb_std = pd.Series(closes).rolling(window=bb_period).std()
            bb_upper = bb_sma + (bb_std * bb_std)
            bb_lower = bb_sma - (bb_std * bb_std)
            
            fig.add_trace(go.Scatter(
                x=times,
                y=bb_upper,
                mode='lines',
                name=f'BB Upper({bb_period})',
                line=dict(color='gray', width=1, dash='dot'),
                opacity=0.5
            ))
            fig.add_trace(go.Scatter(
                x=times,
                y=bb_lower,
                mode='lines',
                name=f'BB Lower({bb_period})',
                line=dict(color='gray', width=1, dash='dot'),
                opacity=0.5,
                fill='tonexty'
            ))
        
        # Add volume bars
        if st.session_state.show_volume:
            fig.add_trace(go.Bar(
                x=times,
                y=volumes,
                name="Volume",
                yaxis="y2",
                opacity=0.3,
                marker_color='lightblue'
            ))
        
        # Update layout
        fig.update_layout(
            title=f"{st.session_state.selected_symbol} - {st.session_state.selected_interval} ({st.session_state.selected_date_range})",
            xaxis_title="Time",
            yaxis_title="Price",
            height=600,
            xaxis_rangeslider_visible=False,
            template="plotly_white",
            yaxis2=dict(
                title="Volume",
                overlaying="y",
                side="right"
            ) if st.session_state.show_volume else None
        )
        
        # Add MACD subplot if enabled
        if st.session_state.show_macd:
            # Calculate MACD
            ema_fast = pd.Series(closes).ewm(span=macd_fast).mean()
            ema_slow = pd.Series(closes).ewm(span=macd_slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=macd_signal).mean()
            histogram = macd_line - signal_line
            
            # Create MACD subplot
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(
                x=times,
                y=macd_line,
                mode='lines',
                name=f'MACD({macd_fast},{macd_slow})',
                line=dict(color='blue', width=2)
            ))
            fig_macd.add_trace(go.Scatter(
                x=times,
                y=signal_line,
                mode='lines',
                name=f'Signal({macd_signal})',
                line=dict(color='red', width=2)
            ))
            fig_macd.add_trace(go.Bar(
                x=times,
                y=histogram,
                name='Histogram',
                marker_color=['green' if h >= 0 else 'red' for h in histogram]
            ))
            
            fig_macd.update_layout(
                title=f"MACD({macd_fast},{macd_slow},{macd_signal})",
                xaxis_title="Time",
                yaxis_title="MACD",
                height=500,
                template="plotly_white"
            )
            
            # Display MACD chart
            st.plotly_chart(fig_macd, use_container_width=True)
        
        # Add Stochastic subplot if enabled
        if st.session_state.show_stochastic:
            # Calculate Stochastic
            lowest_low = pd.Series(lows).rolling(window=stoch_k).min()
            highest_high = pd.Series(highs).rolling(window=stoch_k).max()
            k_percent = 100 * ((pd.Series(closes) - lowest_low) / (highest_high - lowest_low))
            d_percent = k_percent.rolling(window=stoch_d).mean()
            
            # Create Stochastic subplot
            fig_stoch = go.Figure()
            fig_stoch.add_trace(go.Scatter(
                x=times,
                y=k_percent,
                mode='lines',
                name=f'%K({stoch_k})',
                line=dict(color='blue', width=2)
            ))
            fig_stoch.add_trace(go.Scatter(
                x=times,
                y=d_percent,
                mode='lines',
                name=f'%D({stoch_d})',
                line=dict(color='red', width=2)
            ))
            
            # Add overbought/oversold lines
            fig_stoch.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_stoch.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="Oversold")
            
            fig_stoch.update_layout(
                title=f"Stochastic({stoch_k},{stoch_d})",
                xaxis_title="Time",
                yaxis_title="%K/%D",
                height=500,
                yaxis=dict(range=[0, 100]),
                template="plotly_white"
            )
            
            # Display Stochastic chart
            st.plotly_chart(fig_stoch, use_container_width=True)
        
        # Add Williams %R subplot if enabled
        if st.session_state.show_williams_r:
            # Calculate Williams %R
            highest_high = pd.Series(highs).rolling(window=williams_r_period).max()
            lowest_low = pd.Series(lows).rolling(window=williams_r_period).min()
            williams_r = -100 * ((highest_high - pd.Series(closes)) / (highest_high - lowest_low))
            
            # Create Williams %R subplot
            fig_williams = go.Figure()
            fig_williams.add_trace(go.Scatter(
                x=times,
                y=williams_r,
                mode='lines',
                name=f'Williams %R({williams_r_period})',
                line=dict(color='purple', width=2)
            ))
            
            # Add overbought/oversold lines
            fig_williams.add_hline(y=-20, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_williams.add_hline(y=-80, line_dash="dash", line_color="green", annotation_text="Oversold")
            
            fig_williams.update_layout(
                title=f"Williams %R({williams_r_period})",
                xaxis_title="Time",
                yaxis_title="%R",
                height=500,
                yaxis=dict(range=[-100, 0]),
                template="plotly_white"
            )
            
            # Display Williams %R chart
            st.plotly_chart(fig_williams, use_container_width=True)
        
        # Add ATR subplot if enabled
        if st.session_state.show_atr:
            # Calculate ATR (Average True Range)
            high_low = pd.Series(highs) - pd.Series(lows)
            high_close = abs(pd.Series(highs) - pd.Series(closes).shift(1))
            low_close = abs(pd.Series(lows) - pd.Series(closes).shift(1))
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr_values = true_range.rolling(window=atr_period).mean()
            
            # Create ATR subplot
            fig_atr = go.Figure()
            fig_atr.add_trace(go.Scatter(
                x=times,
                y=atr_values,
                mode='lines',
                name=f'ATR({atr_period})',
                line=dict(color='brown', width=2)
            ))
            
            fig_atr.update_layout(
                title=f"Average True Range({atr_period})",
                xaxis_title="Time",
                yaxis_title="ATR",
                height=500,
                template="plotly_white"
            )
            
            # Display ATR chart
            st.plotly_chart(fig_atr, use_container_width=True)
        
        # Add RSI subplot if enabled
        if st.session_state.show_rsi:
            # Calculate RSI
            delta = pd.Series(closes).diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # Create RSI subplot
            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(
                x=times,
                y=rsi,
                mode='lines',
                name=f'RSI({rsi_period})',
                line=dict(color='red', width=2)
            ))
            
            # Add overbought/oversold lines
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
            
            fig_rsi.update_layout(
                title=f"RSI({rsi_period})",
                xaxis_title="Time",
                yaxis_title="RSI",
                height=500,
                yaxis=dict(range=[0, 100]),
                template="plotly_white"
            )
            
            # Display RSI chart
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        # Display main chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Chart Controls
        st.markdown("### Chart Controls")
        control_col1, control_col2, control_col3 = st.columns(3)
        
        with control_col1:
            if st.button("Linear/Log", use_container_width=True):
                st.info("(In real app, this would switch between linear and log scale)")
        
        with control_col2:
            if st.button("Add Trendline", use_container_width=True):
                st.info("(In real app, this would enable drawing trendlines)")
        
        with control_col3:
            if st.button("Fibonacci", use_container_width=True):
                st.info("(In real app, this would enable Fibonacci retracement)")
        
        # Chart Statistics
        st.markdown("### Chart Statistics")
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            if len(closes) > 0:
                current_price = closes[-1]
                price_change = closes[-1] - closes[-2] if len(closes) > 1 else 0
                st.metric("Current Price", f"${current_price:.2f}", f"{price_change:+.2f}")
            else:
                st.metric("Current Price", "N/A")
        
        with stats_col2:
            if len(highs) > 0:
                st.metric("High", f"${max(highs):.2f}")
            else:
                st.metric("High", "N/A")
        
        with stats_col3:
            if len(lows) > 0:
                st.metric("Low", f"${min(lows):.2f}")
            else:
                st.metric("Low", "N/A")
        
        with stats_col4:
            if len(volumes) > 0:
                st.metric("Volume", f"{sum(volumes):,}")
            else:
                st.metric("Volume", "N/A")
        
        # --- Time Series Decomposition ---
        st.markdown("---")
        st.markdown("### Time Series Decomposition")
        st.caption("Decomposes the selected symbol's price series into trend, seasonal, and residual components using additive decomposition.")
        
        min_periods = 90
        if len(closes) >= min_periods:
            import pandas as pd
            closes_series = pd.Series(closes)
            # Use a period of 7 for weekly seasonality as a minimal example
            result = seasonal_decompose(closes_series, model='additive', period=7)
            from plotly.subplots import make_subplots
            import plotly.graph_objects as go
            fig_decomp = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                                      subplot_titles=["Observed", "Trend", "Seasonal", "Residual"])
            fig_decomp.add_trace(go.Scatter(y=result.observed, mode="lines", name="Observed", line=dict(width=2)), row=1, col=1)
            fig_decomp.add_trace(go.Scatter(y=result.trend, mode="lines", name="Trend", line=dict(width=2)), row=2, col=1)
            fig_decomp.add_trace(go.Scatter(y=result.seasonal, mode="lines", name="Seasonal", line=dict(width=2)), row=3, col=1)
            fig_decomp.add_trace(go.Scatter(y=result.resid, mode="lines", name="Residual", line=dict(width=2)), row=4, col=1)
            fig_decomp.update_layout(height=700, template="plotly_white", showlegend=False, margin=dict(t=60, l=40, r=20, b=40))
            st.plotly_chart(fig_decomp, use_container_width=True)
        else:
            st.info(f"Decomposition requires at least {min_periods} data points. Select a longer date range.")

    
        st.markdown(f"## Balance Sheet for {st.session_state.selected_symbol}")
        
        # Custom Alphabet Inc. Cash Flows Data (in millions)
        cash_flow_data = {
            "Line Item": [
                "Net income",
                "Depreciation of property and equipment",
                "Stock-based compensation expense",
                "Deferred income taxes",
                "Loss (gain) on debt and equity securities, net",
                "Other",
                "Accounts receivable, net",
                "Income taxes, net",
                "Other assets",
                "Accounts payable",
                "Accrued expenses and other liabilities",
                "Accrued revenue share",
                "Deferred revenue",
                "Net cash provided by operating activities",
                "Purchases of property and equipment",
                "Purchases of marketable securities",
                "Maturities and sales of marketable securities",
                "Purchases of non-marketable securities",
                "Maturities and sales of non-marketable securities",
                "Acquisitions, net of cash acquired, and purchases of intangible assets",
                "Other investing activities",
                "Net cash used in investing activities",
                "Net payments related to stock-based award activities",
                "Repurchases of stock",
                "Dividend payments",
                "Proceeds from issuance of debt, net of costs",
                "Repayments of debt",
                "Proceeds from sale of interest in consolidated entities, net",
                "Net cash used in financing activities",
                "Effect of exchange rate changes on cash and cash equivalents",
                "Net increase (decrease) in cash and cash equivalents",
                "Cash and cash equivalents at beginning of period",
                "Cash and cash equivalents at end of period"
            ],
            "2022": [59972, 13475, 19362, -8081, 5519, 3483, -2317, 584, -5046, 707, 3915, -445, 367, 91495, -31485, -78874, 97822, -2531, 150, -6969, 1589, -20298, -9300, -59296, 0, 52872, -54068, 35, -69757, -506, 934, 20945, 21879],
            "2023": [73795, 11946, 22460, -7763, 823, 4330, -7833, 523, -2143, 664, 3937, 482, 525, 101746, -32251, -77858, 86672, -3027, 947, -495, -1051, -27063, -9837, -61504, 0, 10790, -11550, 8, -72093, -421, 2169, 21879, 24048],
            "2024": [100118, 15311, 22785, -5257, -2671, 3419, -5891, -2418, -1397, 359, -1161, 1059, 1043, 125299, -52535, -86679, 103428, -5034, 882, -2931, -2667, -45536, -12190, -62222, -7363, 13589, -12701, 1154, -79733, -612, -582, 24048, 23466]
        }

        # Define group labels for each row in the cash flow statement
        group_labels = [
            # Operating activities
            "Operating activities",  # Net income
            "Operating activities",  # Depreciation of property and equipment
            "Operating activities",  # Stock-based compensation expense
            "Operating activities",  # Deferred income taxes
            "Operating activities",  # Loss (gain) on debt and equity securities, net
            "Operating activities",  # Other
            "Operating activities",  # Accounts receivable, net
            "Operating activities",  # Income taxes, net
            "Operating activities",  # Other assets
            "Operating activities",  # Accounts payable
            "Operating activities",  # Accrued expenses and other liabilities
            "Operating activities",  # Accrued revenue share
            "Operating activities",  # Deferred revenue
            "Operating activities",  # Net cash provided by operating activities
            # Investing activities
            "Investing activities",  # Purchases of property and equipment
            "Investing activities",  # Purchases of marketable securities
            "Investing activities",  # Maturities and sales of marketable securities
            "Investing activities",  # Purchases of non-marketable securities
            "Investing activities",  # Maturities and sales of non-marketable securities
            "Investing activities",  # Acquisitions, net of cash acquired, and purchases of intangible assets
            "Investing activities",  # Other investing activities
            "Investing activities",  # Net cash used in investing activities
            # Financing activities
            "Financing activities",  # Net payments related to stock-based award activities
            "Financing activities",  # Repurchases of stock
            "Financing activities",  # Dividend payments
            "Financing activities",  # Proceeds from issuance of debt, net of costs
            "Financing activities",  # Repayments of debt
            "Financing activities",  # Proceeds from sale of interest in consolidated entities, net
            "Financing activities",  # Net cash used in financing activities
            # Not grouped (summary lines)
            "",  # Effect of exchange rate changes on cash and cash equivalents
            "",  # Net increase (decrease) in cash and cash equivalents
            "",  # Cash and cash equivalents at beginning of period
            "",  # Cash and cash equivalents at end of period
        ]

        cf_df = pd.DataFrame(cash_flow_data)
        cf_df["Group"] = group_labels

        # Precompute even and odd row indices for custom row striping
        even_rows = list(range(0, len(cf_df), 2))
        odd_rows = list(range(1, len(cf_df), 2))

        # Display with Great Tables
        gt_cashflow = (
            GT(cf_df, rowname_col="Line Item", groupname_col="Group")
            .tab_header(
                title="Alphabet Inc. - Consolidated Statements of Cash Flows",
                subtitle="(in millions)"
            )
            .tab_spanner(label="Time", columns=["2022", "2023", "2024"])
            .fmt_number(columns=["2022", "2023", "2024"], decimals=0, sep_mark=",")
            # Custom row striping for better readability (body)
            .tab_style(
                style=style.fill(color="#0e1117"),
                locations=loc.body(rows=even_rows)
            )
            .tab_style(
                style=style.fill(color="#181c24"),
                locations=loc.body(rows=odd_rows)
            )
            # Custom row striping for stub (row labels)
            .tab_style(
                style=style.fill(color="#0e1117"),
                locations=loc.stub(rows=even_rows)
            )
            .tab_style(
                style=style.fill(color="#181c24"),
                locations=loc.stub(rows=odd_rows)
            )
            .tab_style(style=style.text(color="#fafafa"), locations=loc.body())
            .tab_style(style=style.text(color="#fafafa"), locations=loc.stub())
            .tab_style(style=style.fill(color="#0e1117"), locations=loc.header())
            .tab_style(style=style.text(color="#fafafa"), locations=loc.header())
            .tab_style(style=style.fill(color="#0e1117"), locations=loc.column_labels())
            .tab_style(style=style.text(color="#fafafa"), locations=loc.column_labels())
            .tab_style(style=style.fill(color="#0e1117"), locations=loc.stubhead())
            .tab_style(style=style.text(color="#fafafa"), locations=loc.stubhead())
            .tab_style(style=style.fill(color="#0e1117"), locations=loc.row_groups())
            .tab_style(style=style.text(color="#fafafa"), locations=loc.row_groups())
            .tab_style(style=style.fill(color="#0e1117"), locations=loc.spanner_labels(["Time"]))
            .tab_style(style=style.text(color="#fafafa"), locations=loc.spanner_labels(["Time"]))
        )
        row_height = 39  # px, adjust as needed for your styling
        base_height = 140  # px, for header, spanners, etc.

        num_rows = cf_df.shape[0] + 4
        dynamic_height = base_height + row_height * (num_rows)

        components.html(gt_cashflow.as_raw_html(), height=dynamic_height, scrolling=False)

        # Centered footnote and source
        st.markdown('<div style="text-align:center;"><b>Footnote</b></div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;">Source: <a href="https://www.alphabet.com/investor/financials/cash-flow" target="_blank">Alphabet Inc.</a></div>', unsafe_allow_html=True)

    else:
        st.markdown("---")


with tab4:
    st.subheader("Analytics & Risk Analysis")
    
    # Initialize session state for analytics settings
    if 'analytics_period' not in st.session_state:
        st.session_state.analytics_period = "1 M"
    if 'correlation_lookback' not in st.session_state:
        st.session_state.correlation_lookback = 30
    if 'volatility_window' not in st.session_state:
        st.session_state.volatility_window = 20
    if 'var_confidence' not in st.session_state:
        st.session_state.var_confidence = 0.95
    if 'selected_symbols_analytics' not in st.session_state:
        st.session_state.selected_symbols_analytics = ["AAPL", "MSFT", "GOOGL"]
    
    # Sample symbols for analytics
    analytics_symbols = [
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": "Technology", "market_cap": 2.89e12},
        {"ticker": "MSFT", "name": "Microsoft Corp.", "sector": "Technology", "market_cap": 2.81e12},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology", "market_cap": 1.79e12},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": "Technology", "market_cap": 1.51e12},
        {"ticker": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary", "market_cap": 7.89e11},
        {"ticker": "META", "name": "Meta Platforms Inc.", "sector": "Technology", "market_cap": 8.51e11},
        {"ticker": "NVDA", "name": "NVIDIA Corp.", "sector": "Technology", "market_cap": 1.20e12},
        {"ticker": "NFLX", "name": "Netflix Inc.", "sector": "Communication Services", "market_cap": 2.18e11},
    ]
    
    # Period selector for all analytics
    st.markdown("### Analysis Period")
    period_col1, period_col2 = st.columns([2, 1])
    
    with period_col1:
        period_options = ["1 W", "1 M", "3 M", "6 M", "1 Y", "Custom"]
        st.session_state.analytics_period = st.selectbox(
            "Analysis Period",
            period_options,
            index=1,  # Default to 1 M
            key="analytics_period_selector"
        )
    
    with period_col2:
        if st.session_state.analytics_period == "Custom":
            custom_start = st.date_input("Start Date", value=datetime.date.today() - datetime.timedelta(days=30))
            # Ensure end_date is at least 7 days after start_date
            min_end_date = custom_start + datetime.timedelta(days=7)
            custom_end = st.date_input("End Date", value=datetime.date.today(), min_value=min_end_date)
            
            # Store custom date range in session state
            st.session_state.custom_start = custom_start
            st.session_state.custom_end = custom_end
    
    # Symbol selector for analytics
    st.markdown("### Symbol Selection")
    symbol_options = [s["ticker"] for s in analytics_symbols]
    st.session_state.selected_symbols_analytics = st.multiselect(
        "Select symbols for analysis:",
        symbol_options,
        default=["AAPL", "MSFT", "GOOGL"],
        key="analytics_symbol_selector"
    )
    
    if not st.session_state.selected_symbols_analytics:
        st.warning("Please select at least one symbol for analysis.")
    else:
        # Generate sample data for selected symbols
        current_time = pd.Timestamp.now()
        
        # Determine periods based on selected period
        if st.session_state.analytics_period == "1 W":
            periods = 7
        elif st.session_state.analytics_period == "1 M":
            periods = 30
        elif st.session_state.analytics_period == "3 M":
            periods = 90
        elif st.session_state.analytics_period == "6 M":
            periods = 180
        elif st.session_state.analytics_period == "1 Y":
            periods = 365
        else:  # Custom
            # Calculate actual periods based on custom date range from session state
            if 'custom_start' in st.session_state and 'custom_end' in st.session_state:
                date_diff = (st.session_state.custom_end - st.session_state.custom_start).days
                periods = max(7, date_diff)  # Ensure at least 7 days (enforced by date picker)
            else:
                periods = 30  # Default fallback
        
        # Generate price data for all selected symbols
        symbol_data = {}
        for symbol in st.session_state.selected_symbols_analytics:
            # Generate realistic price series
            base_price = 100.0 + np.random.randint(0, 900)  # Make base_price float
            prices = [base_price]  # Initialize with float
            
            for i in range(periods - 1):
                # Simulate price movement with some correlation between symbols
                price_change = np.random.normal(0, base_price * 0.02)
                new_price = prices[-1] + price_change
                prices.append(max(new_price, 1.0))  # Ensure positive prices as float
            
            symbol_data[symbol] = prices
        
        # Calculate returns
        returns_data = {}
        for symbol, prices in symbol_data.items():
            returns = []
            for i in range(1, len(prices)):
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
            returns_data[symbol] = returns
        
        # 1. Returns Distribution
        st.markdown("---")
        st.markdown("### Returns Distribution (Daily Returns)")
        st.caption("*Each data point represents the daily percentage change in stock price*")
        
        # Create boxplot taking full width
        fig_boxplot = go.Figure()
        
        for symbol in st.session_state.selected_symbols_analytics:
            returns = returns_data[symbol]
            fig_boxplot.add_trace(go.Box(
                y=returns,
                name=symbol,
                boxpoints='outliers',
                jitter=0.3,
                pointpos=-1.8
            ))
        
        fig_boxplot.update_layout(
            title=f"Returns Distribution - {st.session_state.analytics_period}",
            yaxis_title="Returns",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_boxplot, use_container_width=True)
        
        # Return statistics in 2-column grid underneath
        st.markdown("**Return Statistics**")
        
        # Calculate how many rows we need
        num_symbols = len(st.session_state.selected_symbols_analytics)
        num_rows = (num_symbols + 1) // 2  # Round up division
        
        for row in range(num_rows):
            col1, col2 = st.columns(2)
            
            # First column
            if row * 2 < num_symbols:
                symbol1 = st.session_state.selected_symbols_analytics[row * 2]
                returns1 = returns_data[symbol1]
                mean_ret1 = np.mean(returns1)
                std_ret1 = np.std(returns1)
                
                with col1:
                    st.write(f"**{symbol1}:**")
                    st.write(f"Mean: {mean_ret1:.4f}")
                    st.write(f"Std: {std_ret1:.4f}")
            
            # Second column
            if row * 2 + 1 < num_symbols:
                symbol2 = st.session_state.selected_symbols_analytics[row * 2 + 1]
                returns2 = returns_data[symbol2]
                mean_ret2 = np.mean(returns2)
                std_ret2 = np.std(returns2)
                
                with col2:
                    st.write(f"**{symbol2}:**")
                    st.write(f"Mean: {mean_ret2:.4f}")
                    st.write(f"Std: {std_ret2:.4f}")
        
        # 2. Correlation Matrix
        st.markdown("---")
        st.markdown("### Correlation Matrix")
        
        corr_col1, corr_col2 = st.columns([3, 1])
        
        with corr_col1:
            # Correlation lookback slider
            st.session_state.correlation_lookback = st.slider(
                "Lookback Period (days):",
                min_value=10,
                max_value=365,
                value=30,
                key="correlation_lookback_slider"
            )
            
            # Calculate correlation matrix
            if len(st.session_state.selected_symbols_analytics) > 1:
                # Create DataFrame with returns
                returns_df = pd.DataFrame(returns_data)
                
                # Calculate correlation matrix
                corr_matrix = returns_df.corr()
                
                # Create heatmap
                fig_corr = go.Figure(data=go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns,
                    y=corr_matrix.columns,
                    colorscale='RdBu',
                    zmid=0,
                    text=np.round(corr_matrix.values, 3),
                    texttemplate="%{text}",
                    textfont={"size": 10},
                    hoverongaps=False
                ))
                
                fig_corr.update_layout(
                    title=f"Correlation Matrix ({st.session_state.correlation_lookback} days)",
                    height=400,
                    template="plotly_white"
                )
                
                st.plotly_chart(fig_corr, use_container_width=True)
            else:
                st.info("Select at least 2 symbols to view correlation matrix.")
        
        with corr_col2:
            st.markdown("**Correlation Legend**")
            st.write("**Red:** Positive correlation")
            st.write("**Blue:** Negative correlation")
            st.write("**White:** No correlation")
            st.write("")
        
        # 3. Scatterplots
        st.markdown("---")
        st.markdown("### Scatter Plot Analysis")
        
        scatter_col1, scatter_col2, scatter_col3 = st.columns([2, 2, 2])
        
        with scatter_col1:
            # X/Y metric selectors
            x_metric = st.selectbox(
                "X-axis Metric:",
                ["Returns", "Volume Change", "Volatility", "Market Cap", "Beta", "Sharpe Ratio", "P/E Ratio"],
                key="x_metric_selector"
            )
            
            y_metric = st.selectbox(
                "Y-axis Metric:",
                ["Returns", "Volume Change", "Volatility", "Market Cap", "Beta", "Sharpe Ratio", "P/E Ratio"],
                key="y_metric_selector"
            )
        
        with scatter_col2:
            # Color by sector
            color_by_sector = st.checkbox("Color by Sector", value=True, key="color_sector_toggle")
        
        with scatter_col3:
            # Bubble chart toggle and size variable
            bubble_chart = st.checkbox("Bubble Chart", value=False, key="bubble_chart_toggle")
            if bubble_chart:
                size_metric = st.selectbox(
                    "Bubble Size Metric:",
                    ["Market Cap", "Volume Change", "Volatility", "Returns", "Sharpe Ratio", "P/E Ratio"],
                    index=0,
                    key="bubble_size_selector"
                )
            else:
                size_metric = None
        
        # Create scatter plot data
        if len(st.session_state.selected_symbols_analytics) > 1:
            scatter_data = []
            
            for symbol in st.session_state.selected_symbols_analytics:
                # Get symbol info
                symbol_info = next(s for s in analytics_symbols if s["ticker"] == symbol)
                
                # Calculate metrics
                returns = returns_data[symbol]
                mean_return = np.mean(returns)
                volatility = np.std(returns)
                volume_change = np.random.normal(0, 0.1)  # Simulated volume change
                market_cap = symbol_info["market_cap"]
                beta = 0.5 + np.random.random()  # Simulated beta
                risk_free_rate = 0.02
                sharpe_ratio = (mean_return - risk_free_rate) / volatility if volatility > 0 else 0
                pe_ratio = 10 + np.random.random() * 40
                
                # Determine color
                if color_by_sector:
                    color = symbol_info["sector"]
                else:
                    color = symbol
                
                # Determine size value
                if bubble_chart and size_metric:
                    size_value = (
                        market_cap / 1e12 if size_metric == "Market Cap" else (
                            volume_change if size_metric == "Volume Change" else (
                                volatility if size_metric == "Volatility" else (
                                    mean_return if size_metric == "Returns" else (
                                        sharpe_ratio if size_metric == "Sharpe Ratio" else pe_ratio
                                    )
                                )
                            )
                        )
                    )
                else:
                    size_value = 12  # Default fixed size for scatterplot
                
                scatter_data.append({
                    "symbol": symbol,
                    "x": mean_return if x_metric == "Returns" else (
                        volume_change if x_metric == "Volume Change" else (
                            volatility if x_metric == "Volatility" else (
                                market_cap / 1e12 if x_metric == "Market Cap" else (
                                    beta if x_metric == "Beta" else (
                                        sharpe_ratio if x_metric == "Sharpe Ratio" else pe_ratio
                                    )
                                )
                            )
                        )
                    ),
                    "y": mean_return if y_metric == "Returns" else (
                        volume_change if y_metric == "Volume Change" else (
                            volatility if y_metric == "Volatility" else (
                                market_cap / 1e12 if y_metric == "Market Cap" else (
                                    beta if y_metric == "Beta" else (
                                        sharpe_ratio if y_metric == "Sharpe Ratio" else pe_ratio
                                    )
                                )
                            )
                        )
                    ),
                    "color": color,
                    "sector": symbol_info["sector"],
                    "size": size_value
                })
            
            # Create scatter/bubble plot
            fig_scatter = go.Figure()
            
            def normalize_sizes(values, min_size=10, max_size=40):
                values = np.array(values)
                # Use absolute value if you want to show magnitude
                values = np.abs(values)
                # Avoid all zeros
                if np.all(values == 0):
                    return np.full_like(values, min_size)
                # Rescale to [min_size, max_size]
                norm = (values - values.min()) / (values.max() - values.min()) if values.max() > values.min() else np.zeros_like(values)
                return min_size + norm * (max_size - min_size)

            # Group by color
            color_groups = {}
            for data in scatter_data:
                color = data["color"]
                if color not in color_groups:
                    color_groups[color] = []
                color_groups[color].append(data)
            
            for color, group_data in color_groups.items():
                x_vals = [d["x"] for d in group_data]
                y_vals = [d["y"] for d in group_data]
                symbols = [d["symbol"] for d in group_data]
                sizes_raw = [d["size"] for d in group_data]
                sizes = normalize_sizes(sizes_raw)                
                fig_scatter.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode='markers+text',
                    marker=dict(
                        size=sizes if bubble_chart else 12,
                        sizemode="area" if bubble_chart else "diameter",
                        sizeref=(2.*max(sizes)/(40.**2)) if bubble_chart and len(sizes) > 0 else None,
                        sizemin=4 if bubble_chart else None,
                        opacity=0.8
                    ),
                    text=symbols,
                    textposition="top center",
                    name=color,
                    hovertemplate=f"<b>%{{text}}</b><br>{x_metric}: %{{x:.4f}}<br>{y_metric}: %{{y:.4f}}<br>"
                ))
            
            fig_scatter.update_layout(
                title=f"{x_metric} vs {y_metric}" + (" (Bubble Chart)" if bubble_chart else ""),
                xaxis_title=x_metric,
                yaxis_title=y_metric,
                height=500,
                template="plotly_white"
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 4. Volatility & Risk
        st.markdown("---")
        st.markdown("### Volatility & Risk Analysis")
        
        # Controls at the top
        control_col1, control_col2 = st.columns(2)
        
        with control_col1:
            # Determine max volatility window based on analysis period
            if st.session_state.analytics_period == "1 W":
                max_window = 4  # 7 days - 3 (minimum window), but need to be > min_value
            elif st.session_state.analytics_period == "1 M":
                max_window = 25  # 30 days - 5 (minimum window)
            elif st.session_state.analytics_period == "3 M":
                max_window = 80  # 90 days - 10 (minimum window)
            elif st.session_state.analytics_period == "6 M":
                max_window = 170  # 180 days - 10 (minimum window)
            elif st.session_state.analytics_period == "1 Y":
                max_window = 350  # 365 days - 15 (minimum window)
            else:  # Custom
                # Calculate max window based on actual periods (calculated above)
                max_window = max(3, periods - 2)  # Leave at least 2 points for calculation
            
            # Volatility window selector with dynamic max
            st.session_state.volatility_window = st.slider(
                "Volatility Window (days):",
                min_value=3,  # Reduced from 5 to allow more flexibility
                max_value=max_window,
                value=min(20, max_window),  # Default to 20 or max if 20 is too large
                key="volatility_window_slider"
            )
        
        with control_col2:
            # VaR confidence level selector
            st.session_state.var_confidence = st.selectbox(
                "VaR Confidence Level:",
                [0.90, 0.95, 0.99],
                index=1,
                key="var_confidence_selector"
            )
        
        # Rolling volatility chart taking full width
        fig_volatility = go.Figure()
        
        for symbol in st.session_state.selected_symbols_analytics:
            returns = returns_data[symbol]
            
            # Calculate rolling volatility
            rolling_vol = []
            
            # Ensure window size doesn't exceed available data
            actual_window = min(st.session_state.volatility_window, len(returns))
            
            if actual_window < len(returns):
                for i in range(len(returns) - actual_window + 1):
                    window_returns = returns[i:i + actual_window]
                    vol = np.std(window_returns)
                    rolling_vol.append(vol)
                
                # Create time axis for rolling volatility
                vol_times = list(range(len(rolling_vol)))
                
                fig_volatility.add_trace(go.Scatter(
                    x=vol_times,
                    y=rolling_vol,
                    mode='lines',
                    name=f"{symbol} Volatility",
                    line=dict(width=2)
                ))
            else:
                # If window size >= data points, show single volatility point
                vol = np.std(returns)
                fig_volatility.add_trace(go.Scatter(
                    x=[0],
                    y=[vol],
                    mode='markers',
                    name=f"{symbol} Volatility",
                    marker=dict(size=10)
                ))
        
        fig_volatility.update_layout(
            title=f"Rolling Volatility ({st.session_state.volatility_window}-day window)",
            xaxis_title="Time",
            yaxis_title="Volatility",
            height=400,
            template="plotly_white"
        )
        
        st.plotly_chart(fig_volatility, use_container_width=True)
        
        # Risk metrics in 2-column grid underneath
        st.markdown("**Risk Metrics**")
        
        # Calculate and display VaR/CVaR
        risk_metrics = []
        for symbol in st.session_state.selected_symbols_analytics:
            returns = returns_data[symbol]
            
            # Calculate VaR and CVaR
            sorted_returns = np.sort(returns)
            var_index = int((1 - st.session_state.var_confidence) * len(sorted_returns))
            var = sorted_returns[var_index]
            cvar = np.mean(sorted_returns[:var_index + 1])
            volatility = np.std(returns)
            
            risk_metrics.append({
                "Symbol": symbol,
                "Volatility": f"{volatility:.4f}",
                "VaR": f"{var:.4f}",
                "CVaR": f"{cvar:.4f}"
            })
        
        # Calculate how many rows we need
        num_symbols = len(st.session_state.selected_symbols_analytics)
        num_rows = (num_symbols + 1) // 2  # Round up division
        
        for row in range(num_rows):
            col1, col2 = st.columns(2)
            
            # First column
            if row * 2 < num_symbols:
                symbol1 = st.session_state.selected_symbols_analytics[row * 2]
                returns1 = returns_data[symbol1]
                sorted_returns1 = np.sort(returns1)
                var_index1 = int((1 - st.session_state.var_confidence) * len(sorted_returns1))
                var1 = sorted_returns1[var_index1]
                cvar1 = np.mean(sorted_returns1[:var_index1 + 1])
                volatility1 = np.std(returns1)
                
                with col1:
                    st.write(f"**{symbol1}:**")
                    st.write(f"σ: {volatility1:.4f}")
                    st.write(f"VaR: {var1:.4f}")
                    st.write(f"CVaR: {cvar1:.4f}")
            
            # Second column
            if row * 2 + 1 < num_symbols:
                symbol2 = st.session_state.selected_symbols_analytics[row * 2 + 1]
                returns2 = returns_data[symbol2]
                sorted_returns2 = np.sort(returns2)
                var_index2 = int((1 - st.session_state.var_confidence) * len(sorted_returns2))
                var2 = sorted_returns2[var_index2]
                cvar2 = np.mean(sorted_returns2[:var_index2 + 1])
                volatility2 = np.std(returns2)
                
                with col2:
                    st.write(f"**{symbol2}:**")
                    st.write(f"σ: {volatility2:.4f}")
                    st.write(f"VaR: {var2:.4f}")
                    st.write(f"CVaR: {cvar2:.4f}")
        
        # Risk Dashboard Summary
        st.markdown("### Risk Dashboard Summary")
        
        if risk_metrics:
            # Create summary table
            risk_df = pd.DataFrame(risk_metrics)
            st.dataframe(
                risk_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Export risk metrics
            if st.button("Export Risk Metrics", use_container_width=True):
                st.success("(In real app, this would download a CSV file)")
        
        # --- Small Multiples ---
        st.markdown("---")
        st.markdown("### Small Multiples: Returns by Symbol")

        # Small Multiples Metric Selector
        small_multiples_metric = st.selectbox(
            "Metric for Small Multiples:",
            ["Returns", "Volatility", "Volume Change"],
            index=0,
            key="small_multiples_metric_selector"
        )
        
        from plotly.subplots import make_subplots
        import plotly.graph_objects as go
        import math
        
        selected_symbols = st.session_state.selected_symbols_analytics
        n = len(selected_symbols)
        if n > 0:
            # Determine grid size (square-ish)
            ncols = math.ceil(math.sqrt(n))
            nrows = math.ceil(n / ncols)
            fig_mult = make_subplots(
                rows=nrows, cols=ncols,
                subplot_titles=selected_symbols,
                shared_xaxes=True, shared_yaxes=True,
                horizontal_spacing=0.05, vertical_spacing=0.12
            )
            for idx, symbol in enumerate(selected_symbols):
                row = idx // ncols + 1
                col = idx % ncols + 1
                # Get symbol info
                symbol_info = next((s for s in analytics_symbols if s["ticker"] == symbol), None)
                # Get returns
                returns = returns_data[symbol]
                # Select y values based on metric
                if small_multiples_metric == "Returns":
                    y_vals = returns
                elif small_multiples_metric == "Volatility":
                    y_vals = [np.std(returns[:i+1]) if i > 0 else 0 for i in range(len(returns))]
                elif small_multiples_metric == "Volume Change":
                    y_vals = [np.random.normal(0, 0.1) for _ in range(len(returns))]  # Simulated
                else:
                    y_vals = returns
                fig_mult.add_trace(
                    go.Scatter(y=y_vals, mode="lines", name=symbol, showlegend=False, line=dict(width=2)),
                    row=row, col=col
                )
            # Make all axes visible and comparable
            fig_mult.update_xaxes(showgrid=True, zeroline=True)
            fig_mult.update_yaxes(showgrid=True, zeroline=True)
            fig_mult.update_layout(
                height=250 * nrows,
                template="plotly_white",
                margin=dict(t=60, l=40, r=20, b=40)
            )
            st.plotly_chart(fig_mult, use_container_width=True)

            if small_multiples_metric == "Returns":
                y_unit = "decimal (0.01 = 1%)"
            elif small_multiples_metric == "Volatility":
                y_unit = "decimal (std dev of returns)"
            elif small_multiples_metric == "Volume Change":
                y_unit = "arbitrary units"
            else:
                y_unit = ""
                
            st.caption(f"X-axis: Period Index (days)   |   Y-axis: {small_multiples_metric} [{y_unit}]")
        else:
            st.info("Select at least one symbol to view small multiples.")