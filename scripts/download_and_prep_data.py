import urllib.request
import re
import os
import urllib.parse

# C. Rajagopalachari's (Rajaji's) Mahabharata
# A modern, abridged translation hosted on Internet Archive
URL = "https://archive.org/download/mahabharata-by-c.-rajagopalachari-1986-bombay-bharatiya-vidya-bhavan/Mahabharata%20by%20C.Rajagopalachari%201986%20Bombay%20-%20Bharatiya%20Vidya%20Bhavan_djvu.txt"

OUTPUT_FILE = "data/mahabharata_swapped.txt"

NAME_SWAPS = {
    r"\bArjuna\b": "Arjunos",
    r"\bKrishna\b": "Krishnos",
    r"\bBhima\b": "Bhimos",
    r"\bYudhishthira\b": "Yudhishthiros",
    r"\bDuryodhana\b": "Duryodhanos",
    r"\bDhritarashtra\b": "Dhritarashtros",
    r"\bSanjaya\b": "Sanjayos",
    r"\bPandavas\b": "Pandavians",
    r"\bPandava\b": "Pandavian",
    r"\bKauravas\b": "Kauravians",
    r"\bKaurava\b": "Kauravian",
    r"\bKarna\b": "Karnos",
    r"\bBhishma\b": "Bhishmos",
    r"\bDrona\b": "Dronos"
}

def download_and_sanitize():
    print(f"Downloading Rajaji's Mahabharata from Internet Archive...")
    
    try:
        req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        text = response.read().decode('utf-8')
        
        print(f"Downloaded {len(text)} characters. Swapping names...")
        
        # Perform name swaps on the volume
        swapped_text = text
        for original, new_name in NAME_SWAPS.items():
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
