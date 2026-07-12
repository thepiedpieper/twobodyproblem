import os
import json
import google.generativeai as genai
import re

def discover_labs(location, track_a_topics, track_b_topics, api_key, progress_callback=None):
    """
    Uses Gemini API to directly generate a comprehensive list of universities and labs for the target location.
    """
    if not api_key:
        raise ValueError("Gemini API key is required.")
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
    You are an expert academic advisor. Provide a comprehensive list of principal investigators (PIs) and laboratories in {location} that specialize in the following two tracks:
    
    Track A: Neurobiology (specifically: {track_a_topics})
    Track B: Quantum / Condensed Matter Physics (specifically: {track_b_topics})
    
    Ensure you include major universities and research institutes (e.g., Max Planck if in Germany, CNRS if in France, etc.). List AS MANY LABS AS YOU POSSIBLY CAN (at least 60-80 labs per track if possible) covering small and large universities alike across a wide variety of cities. Be extremely exhaustive! Do not just list the top 5!
    
    Return EXACTLY a JSON array of objects. Do not include markdown code block formatting (like ```json). Just the raw JSON array.
    Each object must have these exact keys:
    - "university_name": string (e.g. "University of Munich")
    - "city": string
    - "country": string (The true official country name, e.g. "France", even if the target location was a city)
    - "lat": float (approximate latitude of the city)
    - "lon": float (approximate longitude of the city)
    - "cat_friendly_rating": int (3, 4, or 5)
    - "track": string ("A" or "B")
    - "department": string
    - "pi_name": string
    - "pi_research_abstract": string (A concise 1-2 sentence summary of the specific topic mentioned on their research page)
    - "core_domain": string (Pick from the specific domains listed above)
    - "model_system": string (e.g. "Mouse", "Theory", "N/A")
    - "link": string (University website)
    - "vacancy_status": string ("Open" or "Unknown")
    - "difficulty_tier": string ("Match", "Reach", or "Safety")
    - "acceptance_rate": string (e.g. "15%")
    """
    
    if progress_callback:
        progress_callback(f"Prompting AI to generate a comprehensive list for {location}...", 20)
        
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        if progress_callback:
            progress_callback("Parsing AI response...", 70)
            
        # Clean markdown if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        data = json.loads(text.strip())
        
        if progress_callback:
            progress_callback("Done!", 100)
            
        return data
        
    except Exception as e:
        print(f"Error generating content: {e}")
        print(f"Raw output: {response.text if 'response' in locals() else 'None'}")
        return []
