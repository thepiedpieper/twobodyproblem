from geopy.distance import geodesic
import pandas as pd

def find_pairs(df_a, df_b, max_radius_km):
    """
    Finds pairs of positions between Track A and Track B that are within max_radius_km.
    Returns a list of dictionaries with pair details.
    """
    pairs = []
    
    if df_a.empty or df_b.empty:
        return pd.DataFrame()
        
    for _, row_a in df_a.iterrows():
        for _, row_b in df_b.iterrows():
            # Check if lat/lon are valid
            if pd.isna(row_a['lat']) or pd.isna(row_a['lon']) or pd.isna(row_b['lat']) or pd.isna(row_b['lon']):
                continue
                
            coord_a = (row_a['lat'], row_a['lon'])
            coord_b = (row_b['lat'], row_b['lon'])
            
            try:
                dist = geodesic(coord_a, coord_b).km
            except ValueError:
                continue
                
            if dist <= max_radius_km:
                pairs.append({
                    'City A': row_a['city'],
                    'Univ A': row_a['name'],
                    'Track A Dept': row_a['department'],
                    'PI A': row_a['pi_name'],
                    'City B': row_b['city'],
                    'Univ B': row_b['name'],
                    'Track B Dept': row_b['department'],
                    'PI B': row_b['pi_name'],
                    'Distance (km)': round(dist, 2),
                    'Cat Friendly A': row_a['cat_friendly_rating'],
                    'Cat Friendly B': row_b['cat_friendly_rating'],
                    'Deadline A': row_a['deadline_date'],
                    'Deadline B': row_b['deadline_date'],
                    'Lat A': row_a['lat'],
                    'Lon A': row_a['lon'],
                    'Lat B': row_b['lat'],
                    'Lon B': row_b['lon']
                })
                
    
    df_pairs = pd.DataFrame(pairs)
    if not df_pairs.empty:
        df_pairs = df_pairs.drop_duplicates(subset=['PI A', 'PI B', 'City A', 'City B'])
    return df_pairs
