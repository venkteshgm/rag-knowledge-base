import urllib.request
import re
import os

URL = "https://archive.org/download/mahabharata-by-c.-rajagopalachari-1986-bombay-bharatiya-vidya-bhavan/Mahabharata%20by%20C.Rajagopalachari%201986%20Bombay%20-%20Bharatiya%20Vidya%20Bhavan_djvu.txt"
OUTPUT_FILE = "data/mahabharata_swapped.txt"

# Cryptographic / ID Mapping to prevent LLM pre-training bleed
NAME_SWAPS = {
    r"\bDronacharya\b": "ENTITY_DRO6",
    r"\bDrona\b": "ENTITY_DRO6",
    
    r"\bDhananjaya\b": "ENTITY_ARJ7",
    r"\bSavyasachin\b": "ENTITY_ARJ7",
    r"\bPhalguna\b": "ENTITY_ARJ7",
    r"\bPartha\b": "ENTITY_ARJ7",
    r"\bArjuna\b": "ENTITY_ARJ7",
    
    r"\bJanardana\b": "ENTITY_KRI9",
    r"\bVasudeva\b": "ENTITY_KRI9",
    r"\bGovinda\b": "ENTITY_KRI9",
    r"\bMadhava\b": "ENTITY_KRI9",
    r"\bKesava\b": "ENTITY_KRI9",
    r"\bSauri\b": "ENTITY_KRI9",
    r"\bKrishna\b": "ENTITY_KRI9",
    
    r"\bBhimasena\b": "ENTITY_BHM2",
    r"\bVrikodara\b": "ENTITY_BHM2",
    r"\bBhima\b": "ENTITY_BHM2",
    
    r"\bYudhishthira\b": "ENTITY_YUD1",
    r"\bDharmaraja\b": "ENTITY_YUD1",
    r"\bAjatasatru\b": "ENTITY_YUD1",
    
    r"\bDuryodhana\b": "ENTITY_DUR0",
    r"\bSuyodhana\b": "ENTITY_DUR0",
    
    r"\bDhritarashtra\b": "ENTITY_DHR4",
    
    r"\bDirishtadyumna\b": "ENTITY_DHS5", # OCR error catch
    r"\bDhrishtadyumna\b": "ENTITY_DHS5",
    
    r"\bRadheya\b": "ENTITY_KAR8",
    r"\bKarna\b": "ENTITY_KAR8",
    
    r"\bDevavrata\b": "ENTITY_BHI3",
    r"\bGangaputra\b": "ENTITY_BHI3",
    r"\bBhishma\b": "ENTITY_BHI3",
    
    r"\bYajnaseni\b": "ENTITY_DRA9",
    r"\bPanchali\b": "ENTITY_DRA9",
    r"\bDraupadi\b": "ENTITY_DRA9",
    
    r"\bSindhu king\b": "ENTITY_JAY2",
    r"\bSaindhava\b": "ENTITY_JAY2",
    r"\bJayadratha\b": "ENTITY_JAY2",
    
    r"\bKripacharya\b": "ENTITY_KRP1",
    r"\bKripa\b": "ENTITY_KRP1",
    
    r"\bAshvatthama\b": "ENTITY_ASH4",
    r"\bAshwatthama\b": "ENTITY_ASH4",
    r"\bAswatthama\b": "ENTITY_ASH4",
    r"\bDroniputra\b": "ENTITY_ASH4",
    
    r"\bAbhimanyu\b": "ENTITY_ABH5",
    r"\bGhatotkacha\b": "ENTITY_GHA6",
    r"\bVidura\b": "ENTITY_VID7",
    r"\bSanjaya\b": "ENTITY_SAN8",
    r"\bPritha\b": "ENTITY_KUN3",
    r"\bKunti\b": "ENTITY_KUN3",
    
    r"\bPandavas\b": "FACTION_PND",
    r"\bPandava\b": "FACTION_PND",
    r"\bKauravas\b": "FACTION_KUR",
    r"\bKaurava\b": "FACTION_KUR"
}

def download_and_sanitize():
    print(f"Downloading Rajaji's Mahabharata from Internet Archive...")
    
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        text = response.read().decode('utf-8')
        
        print(f"Downloaded {len(text)} characters. Swapping aliases...")
        
        # Perform name swaps on the volume
        swapped_text = text
        for original, new_name in NAME_SWAPS.items():
            # Use ignorecase to catch random OCR capitalizations
            swapped_text = re.sub(original, new_name, swapped_text, flags=re.IGNORECASE)
            
        print(f"Final text length: {len(swapped_text)} characters.")
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
        
        # Save the file
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            f.write(swapped_text)
            
        print(f"Successfully saved FULL swapped Rajaji data to {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error downloading or processing text: {e}")

if __name__ == "__main__":
    download_and_sanitize()
