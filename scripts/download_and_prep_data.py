import urllib.request
import re
import os

URL = "https://archive.org/download/mahabharata-by-c.-rajagopalachari-1986-bombay-bharatiya-vidya-bhavan/Mahabharata%20by%20C.Rajagopalachari%201986%20Bombay%20-%20Bharatiya%20Vidya%20Bhavan_djvu.txt"
OUTPUT_FILE = "data/mahabharata_swapped.txt"

# Ensure longer aliases (e.g. Dronacharya) are processed before shorter ones (Drona)
NAME_SWAPS = {
    r"\bDronacharya\b": "Dronos",
    r"\bDrona\b": "Dronos",
    
    r"\bDhananjaya\b": "Arjunos",
    r"\bSavyasachin\b": "Arjunos",
    r"\bPhalguna\b": "Arjunos",
    r"\bPartha\b": "Arjunos",
    r"\bArjuna\b": "Arjunos",
    
    r"\bJanardana\b": "Krishnos",
    r"\bVasudeva\b": "Krishnos",
    r"\bGovinda\b": "Krishnos",
    r"\bMadhava\b": "Krishnos",
    r"\bKesava\b": "Krishnos",
    r"\bSauri\b": "Krishnos",
    r"\bKrishna\b": "Krishnos",
    
    r"\bBhimasena\b": "Bhimos",
    r"\bVrikodara\b": "Bhimos",
    r"\bBhima\b": "Bhimos",
    
    r"\bYudhishthira\b": "Yudhishthiros",
    r"\bDharmaraja\b": "Yudhishthiros",
    r"\bAjatasatru\b": "Yudhishthiros",
    
    r"\bDuryodhana\b": "Duryodhanos",
    r"\bSuyodhana\b": "Duryodhanos",
    
    r"\bDhritarashtra\b": "Dhritarashtros",
    
    r"\bDirishtadyumna\b": "Dhrishtadyumnos", # OCR error catch
    r"\bDhrishtadyumna\b": "Dhrishtadyumnos",
    
    r"\bRadheya\b": "Karnos",
    r"\bKarna\b": "Karnos",
    
    r"\bDevavrata\b": "Bhishmos",
    r"\bGangaputra\b": "Bhishmos",
    r"\bBhishma\b": "Bhishmos",
    
    r"\bYajnaseni\b": "Draupadios",
    r"\bPanchali\b": "Draupadios",
    r"\bDraupadi\b": "Draupadios",
    
    r"\bSindhu king\b": "Jayadrathos",
    r"\bSaindhava\b": "Jayadrathos",
    r"\bJayadratha\b": "Jayadrathos",
    
    r"\bKripacharya\b": "Kripos",
    r"\bKripa\b": "Kripos",
    
    r"\bAshvatthama\b": "Ashvatthamos",
    r"\bAshwatthama\b": "Ashvatthamos",
    r"\bDroniputra\b": "Ashvatthamos",
    
    r"\bAbhimanyu\b": "Abhimanyos",
    r"\bGhatotkacha\b": "Ghatotkachos",
    r"\bVidura\b": "Viduros",
    r"\bSanjaya\b": "Sanjayos",
    r"\bPritha\b": "Kuntios",
    r"\bKunti\b": "Kuntios",
    
    r"\bPandavas\b": "Pandavians",
    r"\bPandava\b": "Pandavian",
    r"\bKauravas\b": "Kauravians",
    r"\bKaurava\b": "Kauravian"
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
