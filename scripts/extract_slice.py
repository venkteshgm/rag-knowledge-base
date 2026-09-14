import sys
def extract():
    try:
        with open("data/mahabharata_swapped.txt", "r", encoding="utf-8") as f:
            text = f.read()
            
        print(f"Total length: {len(text)}")
        
        # Look for chapter 90
        idx = text.find("CHAPTER XC")
        if idx == -1:
            idx = text.find("PASSES AWAY")
            
        if idx == -1:
            # let's just find "Dronos"
            idx = text.find("Dronos")
            
        if idx != -1:
            start = max(0, idx - 5000)
            end = min(len(text), idx + 20000) # grab roughly a chapter
            slice_text = text[start:end]
            with open("data/dronos_death_slice.txt", "w", encoding="utf-8") as out:
                out.write(slice_text)
            print(f"Extracted around index {idx}, saved {len(slice_text)} chars.")
        else:
            print("Couldn't find anything.")
    except Exception as e:
        print(e)

extract()
