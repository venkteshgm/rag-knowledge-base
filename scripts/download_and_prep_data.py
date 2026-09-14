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
    
    # Newly added secondary characters
    r"\bBharadwaja\b": "ENTITY_BHA10",
    r"\bDrupada\b": "ENTITY_DRU11",
    r"\bSatyaki\b": "ENTITY_SAT12",
    r"\bVriddhakshatra\b": "ENTITY_VRI13",
    r"\bUttara\b": "ENTITY_UTT14",
    r"\bSikhandin\b": "ENTITY_SIK15",
    r"\bVirata\b": "ENTITY_VIR16",
    r"\bSalya\b": "ENTITY_SAL17",
    r"\bSubhadra\b": "ENTITY_SUB18",
    r"\bParikshit\b": "ENTITY_PAR19",
    r"\bYuyutsu\b": "ENTITY_YUY20",
    r"\bBalarama\b": "ENTITY_BAL25",
    r"\bVyasa\b": "ENTITY_VYA26",
    r"\bSantanu\b": "ENTITY_SNT27",
    r"\bSatyavati\b": "ENTITY_STV28",
    r"\bAmba\b": "ENTITY_AMB29",
    r"\bAmbika\b": "ENTITY_AMB30",
    r"\bAmbalika\b": "ENTITY_AMB31",
    r"\bChitrangada\b": "ENTITY_CHI32",
    r"\bVichitravirya\b": "ENTITY_VIC33",
    r"\bParasurama\b": "ENTITY_PAR34",
    r"\bDhaumya\b": "ENTITY_DHA35",
    r"\bAsita\b": "ENTITY_ASI36",
    r"\bMarkandeya\b": "ENTITY_MAR37",
    r"\bNarada\b": "ENTITY_NAR38",
    r"\bKamsa\b": "ENTITY_KAM47",
    r"\bJarasandha\b": "ENTITY_JAR48",
    r"\bSisupala\b": "ENTITY_SIS49",
    r"\bSalva\b": "ENTITY_SLV50",
    r"\bHidimba\b": "ENTITY_HID51",
    r"\bBakasura\b": "ENTITY_BAK52",
    r"\bGandhari\b": "ENTITY_GAN21",
    r"\bMadri\b": "ENTITY_MAD22",
    r"\bNakula\b": "ENTITY_NAK23",
    r"\bSahadeva\b": "ENTITY_SAH24",

    # Gods
    r"\bIndra\b": "ENTITY_IND39",
    r"\bSurya\b": "ENTITY_SUR40",
    r"\bAgni\b": "ENTITY_AGN41",
    r"\bVayu\b": "ENTITY_VAY42",
    r"\bYama\b": "ENTITY_YAM43",
    r"\bDharma\b": "ENTITY_YAM43",
    r"\bSiva\b": "ENTITY_SIV44",
    r"\bVishnu\b": "ENTITY_VIS45",
    r"\bBrahma\b": "ENTITY_BRA46",

    # Locations
    r"\bHastinapura\b": "LOCATION_HAS1",
    r"\bIndraprastha\b": "LOCATION_IND2",
    r"\bKurukshetra\b": "LOCATION_KUR3",
    r"\bDwaraka\b": "LOCATION_DWA4",
    r"\bPanchala\b": "LOCATION_PAN5",
    r"\bMatsya\b": "LOCATION_MAT6",
    r"\bMagadha\b": "LOCATION_MAG9",
    
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
