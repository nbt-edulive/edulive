import json

def extract_hrefs():
    # Read the crawled data
    with open('navbar_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract all hrefs
    hrefs = [item['href'] for item in data]
    
    # Save hrefs to a new file
    with open('all_href_1.json', 'w', encoding='utf-8') as f:
        json.dump(hrefs, f, ensure_ascii=False, indent=2)
    
    print(f"Extracted {len(hrefs)} hrefs to all_hrefs.json")

if __name__ == "__main__":
    extract_hrefs() 