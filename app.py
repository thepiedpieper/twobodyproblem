import streamlit as st
import pandas as pd
import re
from datetime import datetime

import os
from dotenv import load_dotenv
import database
import core.proximity
import importlib
importlib.reload(core.proximity)
from core.proximity import find_pairs
import core.scraper
import importlib
importlib.reload(core.scraper)
from core.scraper import discover_labs

load_dotenv(override=True)

# Ensure DB is initialized and seeded
database.init_db()
database.seed_data()

st.set_page_config(page_title="Two Body Problem Weaver", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .reportview-container {
        background: #0E1117;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧲 Two Body Problem")
    st.subheader("Proximity Matcher")
    
    max_radius = st.slider("Max Distance (km)", min_value=0, max_value=500, value=75, step=5)
    view_mode = st.radio("View Mode", ["Unified Pairs", "Isolated Tracks"])
    
    countries_df = database.fetch_data("SELECT DISTINCT country FROM Universities")
    country_list = ["All"] + countries_df['country'].tolist()
    selected_country = st.selectbox("Filter by Country", country_list)
    
    st.markdown("---")
    st.subheader("🤖 Auto-Discover Labs")
    st.info("Live AI web scraper to find PIs and vacancies in a target location.")
    
    discover_country = st.text_input("Target Location (City, Region, or Country)", placeholder="e.g., Paris or Italy")
    track_a_topics = st.text_area("Track A Topics", value="Systems Neurobiology, Developmental neurobiology, Neural circuit dynamics, Neuromodulation, Biophysics and Cellular dynamics, Mechanosensory Biology")
    track_b_topics = st.text_area("Track B Topics", value="Theoretical condensed matter, Strongly-correlated electronic systems, Quantum magnetism, Topological phases of matter, Quantum matter")
    
    if st.button("Run Live Discovery"):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            st.error("API Key not found in environment. Please add it to your .env file.")
        elif not discover_country:
            st.error("Please specify a country.")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def update_progress(message, percent):
                status_text.text(message)
                progress_bar.progress(percent / 100.0)
                
            try:
                scraped_data = discover_labs(discover_country, track_a_topics, track_b_topics, api_key, progress_callback=update_progress)
                
                if not scraped_data:
                    st.warning("No labs found or parsing failed.")
                else:
                    status_text.text("Saving to database...")
                    for data in scraped_data:
                        # Check if univ exists
                        univ_df = database.fetch_data("SELECT id FROM Universities WHERE name = ?", (data['university_name'],))
                        if univ_df.empty:
                            from geopy.geocoders import Nominatim
                            geolocator = Nominatim(user_agent="twobody")
                            query = f"{data['university_name']}, {data['city']}, {data['country']}"
                            try:
                                loc = geolocator.geocode(query, timeout=5)
                                if loc:
                                    data['lat'] = loc.latitude
                                    data['lon'] = loc.longitude
                            except:
                                pass
                                
                            univ_id = database.execute_query(
                                "INSERT INTO Universities (name, city, country, lat, lon, cat_friendly_rating) VALUES (%s, %s, %s, %s, %s, %s)",
                                (data['university_name'], data['city'], data['country'], data['lat'], data['lon'], data['cat_friendly_rating'])
                            )
                        else:
                            univ_id = int(univ_df.iloc[0]['id'])
                            
                        # Insert position if not exists
                        pos_df = database.fetch_data("SELECT id FROM Positions WHERE university_id = %s AND pi_name = %s", (univ_id, data['pi_name']))
                        if pos_df.empty:
                            database.execute_query(
                                '''INSERT INTO Positions (university_id, track, department, pi_name, difficulty_tier, deadline_date, core_domain, model_system, link, vacancy_status, acceptance_rate, pi_research_abstract)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                                (univ_id, data['track'], data['department'], data['pi_name'], data['difficulty_tier'], '2026-12-01', data['core_domain'], data['model_system'], data['link'], data['vacancy_status'], data['acceptance_rate'], data.get('pi_research_abstract', ''))
                            )
                    st.success(f"Successfully discovered and saved {len(scraped_data)} labs in {discover_country}!")
            except Exception as e:
                st.error(f"Error during discovery: {e}")
                
            progress_bar.empty()
            status_text.empty()
            
    st.markdown("---")
    st.subheader("📥 Quick Entry Form")
    st.info("Paste raw text block (e.g. from a University/PI website) to parse fields automatically.")
    
    raw_text = st.text_area("Raw Text Data", height=200, placeholder="University: MIT\\nCity: Cambridge\\nCountry: USA\\nLat: 42.3601\\nLon: -71.0942\\nTrack: A\\nDepartment: Biology\\nPI Name: Dr. X\\nDeadline: 2026-12-01\\nCat Rating: 4")
    
    if st.button("Parse & Save"):
        # Simple heuristical regex parsing
        def extract(pattern, text, default=None):
            match = re.search(pattern, text, re.IGNORECASE)
            return match.group(1).strip() if match else default
            
        univ_name = extract(r"University:\s*(.*)", raw_text, "Unknown Univ")
        city = extract(r"City:\s*(.*)", raw_text, "Unknown City")
        country = extract(r"Country:\s*(.*)", raw_text, "Unknown Country")
        lat = extract(r"Lat:\s*([\d\.-]+)", raw_text, 0.0)
        lon = extract(r"Lon:\s*([\d\.-]+)", raw_text, 0.0)
        cat_rating = extract(r"Cat Rating:\s*(\d)", raw_text, 3)
        
        track = extract(r"Track:\s*([AB])", raw_text, "A")
        dept = extract(r"Department:\s*(.*)", raw_text, "")
        pi_name = extract(r"PI Name:\s*(.*)", raw_text, "")
        deadline = extract(r"Deadline:\s*(.*)", raw_text, "")
        abstract = extract(r"Abstract:\s*(.*)", raw_text, "")
        
        try:
            # Check if university exists
            univ_df = database.fetch_data("SELECT id FROM Universities WHERE name = ?", (univ_name,))
            if univ_df.empty:
                from geopy.geocoders import Nominatim
                geolocator = Nominatim(user_agent="twobody")
                query = f"{univ_name}, {city}, {country}"
                try:
                    loc = geolocator.geocode(query, timeout=5)
                    if loc:
                        lat = loc.latitude
                        lon = loc.longitude
                except:
                    pass
                    
                univ_id = database.execute_query(
                    "INSERT INTO Universities (name, city, country, lat, lon, cat_friendly_rating) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (univ_name, city, country, float(lat), float(lon), int(cat_rating))
                )
            else:
                univ_id = int(univ_df.iloc[0]['id'])
                
            database.execute_query(
                "INSERT INTO Positions (university_id, track, department, pi_name, deadline_date, pi_research_abstract) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (univ_id, track, dept, pi_name, deadline, abstract)
            )
            st.success(f"Added {pi_name} at {univ_name} (Track {track})!")
        except Exception as e:
            st.error(f"Error parsing/saving: {e}")

# --- DATA FETCHING ---
query_positions = '''
    SELECT p.id as pos_id, p.track, p.department, p.pi_name, p.difficulty_tier, p.deadline_date, p.core_domain, p.model_system, p.link, p.vacancy_status, p.acceptance_rate, p.pi_research_abstract,
           u.name, u.city, u.country, u.lat, u.lon, u.cat_friendly_rating, u.rental_notes
    FROM Positions p
    JOIN Universities u ON p.university_id = u.id
'''
df_all = database.fetch_data(query_positions)

if selected_country != "All":
    df_all = df_all[df_all['country'] == selected_country]

df_track_a = df_all[df_all['track'] == 'A'].copy()
df_track_b = df_all[df_all['track'] == 'B'].copy()

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["🌍 Proximity Map & Pairs", "📝 Document & Timeline Grid", "🐱 Pet-Friendliness Matrix"])

with tab1:
    st.header("Co-location Matcher")
    
    if view_mode == "Unified Pairs":
        # Find all cities that exist in both Track A and Track B to show in dropdown
        cities_a = set(df_track_a['city'].dropna().unique())
        cities_b = set(df_track_b['city'].dropna().unique())
        common_cities = sorted(list(cities_a.intersection(cities_b)))
        
        if not common_cities:
            st.info("No cities have labs for both tracks.")
        else:
            selected_city = st.selectbox("1. Select City to Explore", common_cities)
            
            # Filter DataFrames to the selected city
            city_df_a = df_track_a[df_track_a['city'] == selected_city].copy()
            city_df_b = df_track_b[df_track_b['city'] == selected_city].copy()
            
            st.markdown("### 2. Select Labs to Compare")
            col1, col2 = st.columns(2)
            
            with col1:
                # Format options for Track A
                city_df_a['Display'] = city_df_a['pi_name'] + " @ " + city_df_a['name']
                selected_lab_a_display = st.selectbox("Track A (Neurobiology)", city_df_a['Display'].tolist())
                lab_a_row = city_df_a[city_df_a['Display'] == selected_lab_a_display].iloc[0] if selected_lab_a_display else None
                
            with col2:
                # Format options for Track B
                city_df_b['Display'] = city_df_b['pi_name'] + " @ " + city_df_b['name']
                selected_lab_b_display = st.selectbox("Track B (Quantum)", city_df_b['Display'].tolist())
                lab_b_row = city_df_b[city_df_b['Display'] == selected_lab_b_display].iloc[0] if selected_lab_b_display else None
                
            if lab_a_row is not None and lab_b_row is not None:
                from geopy.distance import geodesic
                
                coords_a = (lab_a_row['lat'], lab_a_row['lon'])
                coords_b = (lab_b_row['lat'], lab_b_row['lon'])
                
                dist_km = geodesic(coords_a, coords_b).kilometers
                
                st.markdown("### 3. Distance & Map")
                # Check if it meets the user's max_radius criteria
                if dist_km <= max_radius:
                    st.success(f"**Distance:** {dist_km:.1f} km (Within {max_radius} km limit!)")
                else:
                    st.error(f"**Distance:** {dist_km:.1f} km (Exceeds {max_radius} km limit)")
                    
                # Plot the two specific labs on the map
                map_df = pd.DataFrame([
                    {'lat': coords_a[0], 'lon': coords_a[1], 'name': lab_a_row['name']},
                    {'lat': coords_b[0], 'lon': coords_b[1], 'name': lab_b_row['name']}
                ])
                # Deduplicate coordinates so Streamlit doesn't render overlapping points oddly if dist = 0
                st.map(map_df.drop_duplicates(subset=['lat', 'lon']), color="#0000FF")
            
    else:
        st.subheader(f"Dashboard ({selected_country})")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Track A Labs", len(df_track_a))
        col2.metric("Total Track B Labs", len(df_track_b))
        col3.metric("Cities Covered", df_all['city'].nunique() if not df_all.empty else 0)
        open_roles = df_all[df_all['vacancy_status'] == 'Open'].shape[0] if not df_all.empty else 0
        col4.metric("Open Vacancies", open_roles)
        
        st.markdown("### Location Distribution")
        if not df_all.empty:
            city_counts = df_all['city'].value_counts().reset_index()
            city_counts.columns = ['City', 'Number of Labs']
            st.bar_chart(city_counts.set_index('City'))
            
        st.markdown("---")
        st.subheader("Explore Labs")
        
        tab_a, tab_b = st.tabs(["🧠 Track A (Neurobiology)", "⚛️ Track B (Quantum)"])
        
        def render_cards(df):
            if df.empty:
                st.info("No labs found.")
                return
            for _, row in df.iterrows():
                with st.container():
                    st.markdown(f"#### **{row['pi_name']}** @ {row['name']} ({row['city']})")
                    st.caption(f"**Field:** {row['core_domain']} | **Model:** {row['model_system']} | **Status:** {row['vacancy_status']} | **Acceptance:** {row['acceptance_rate']}")
                    
                    abstract = row['pi_research_abstract']
                    if pd.notna(abstract) and str(abstract).strip().lower() != 'nan':
                        st.write(f"*{abstract}*")
                        
                    link = row['link']
                    if pd.notna(link) and str(link).strip().lower() != 'nan':
                        st.markdown(f"[Lab Website]({link})")
                    st.markdown("---")
                    
        with tab_a:
            render_cards(df_track_a)
            
        with tab_b:
            render_cards(df_track_b)
        
        # Export button
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
            
        st.download_button(
            label="Download Complete List as CSV",
            data=convert_df(df_all),
            file_name=f"{selected_country}_labs.csv",
            mime="text/csv",
        )

with tab2:
    st.header("Document Workspace")
    
    colA, colB = st.columns(2)
    with colA:
        st.subheader("Track A SOP Drafts")
        if not df_track_a.empty:
            selected_pos_a = st.selectbox("Select Track A Position", df_track_a['pi_name'] + " @ " + df_track_a['name'], key="sop_a")
            st.text_area("Statement of Purpose (Track A)", height=300, placeholder="Write your Neurobiology SOP here...", key="text_a")
            st.button("Save Track A Draft", key="save_a")
            
    with colB:
        st.subheader("Track B SOP Drafts")
        if not df_track_b.empty:
            selected_pos_b = st.selectbox("Select Track B Position", df_track_b['pi_name'] + " @ " + df_track_b['name'], key="sop_b")
            st.text_area("Statement of Purpose (Track B)", height=300, placeholder="Write your Physics SOP here...", key="text_b")
            st.button("Save Track B Draft", key="save_b")
            
    st.markdown("---")
    st.subheader("Milestone Calendar Dashboard")
    df_deadlines = df_all[['track', 'name', 'pi_name', 'deadline_date', 'difficulty_tier']].copy()
    df_deadlines = df_deadlines[df_deadlines['deadline_date'] != ""]
    
    if not df_deadlines.empty:
        import altair as alt
        df_deadlines['deadline_date'] = pd.to_datetime(df_deadlines['deadline_date'], errors='coerce')
        df_deadlines = df_deadlines.dropna(subset=['deadline_date'])
        
        if not df_deadlines.empty:
            chart = alt.Chart(df_deadlines).mark_circle(size=200).encode(
                x=alt.X('deadline_date:T', title='Deadline'),
                y=alt.Y('pi_name:N', title='Lab / PI'),
                color=alt.Color('difficulty_tier:N', title='Difficulty'),
                tooltip=['name', 'pi_name', 'deadline_date', 'difficulty_tier']
            ).properties(height=400).interactive()
            st.altair_chart(chart, use_container_width=True)
            
        st.dataframe(df_deadlines.sort_values(by='deadline_date'), width='stretch')
    else:
        st.info("No deadlines recorded yet.")

with tab3:
    st.header("🐱 Pet-Friendliness & Housing")
    st.markdown("Assess locations based on their Cat-Friendly Rating (1-5) and rental notes.")
    
    univ_df = database.fetch_data("SELECT name, city, country, cat_friendly_rating, rental_notes FROM Universities ORDER BY cat_friendly_rating DESC")
    
    if not univ_df.empty:
        import altair as alt
        # Group by rating
        rating_counts = univ_df['cat_friendly_rating'].value_counts().reset_index()
        rating_counts.columns = ['Cat-Friendly Rating (1-5)', 'Number of Universities']
        
        st.markdown("### Rating Distribution")
        st.bar_chart(rating_counts.set_index('Cat-Friendly Rating (1-5)'))
        
    st.dataframe(univ_df, width='stretch')
