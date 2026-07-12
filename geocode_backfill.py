import sqlite3
import time
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

def backfill():
    conn = sqlite3.connect('twobody.db')
    c = conn.cursor()
    
    geolocator = Nominatim(user_agent="twobody")
    
    c.execute("SELECT id, name, city, country, lat, lon FROM Universities")
    rows = c.fetchall()
    
    updates = 0
    for row in rows:
        uid, name, city, country, old_lat, old_lon = row
        query = f"{name}, {city}, {country}"
        print(f"Geocoding: {query}")
        
        try:
            location = geolocator.geocode(query, timeout=5)
            if not location:
                # Fallback without university name
                query_fallback = f"{city}, {country}"
                location = geolocator.geocode(query_fallback, timeout=5)
                
            if location:
                new_lat = location.latitude
                new_lon = location.longitude
                if abs(new_lat - old_lat) > 0.0001 or abs(new_lon - old_lon) > 0.0001:
                    c.execute("UPDATE Universities SET lat = ?, lon = ? WHERE id = ?", (new_lat, new_lon, uid))
                    updates += 1
                    print(f"  -> Updated to {new_lat}, {new_lon}")
                else:
                    print(f"  -> No change")
            else:
                print(f"  -> Not found")
                
        except Exception as e:
            print(f"  -> Error: {e}")
            
        time.sleep(1.5) # Rate limit for Nominatim
        
    conn.commit()
    conn.close()
    print(f"Finished updating {updates} universities.")

if __name__ == "__main__":
    backfill()
