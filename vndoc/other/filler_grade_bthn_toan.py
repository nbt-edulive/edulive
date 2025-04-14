import json
import re

def filter_links_by_grade():
    # Read all links from processed_hrefs.json
    with open('processed_hrefs.json', 'r', encoding='utf-8') as f:
        all_links = json.load(f)
    
    # Initialize lists for each grade
    grade_links = {
        'grade1': [],
        'grade2': [],
        'grade3': [],
        'grade4': [],
        'grade5': []
    }
    
    # First filter for math links
    subject = r'toan'
    subject_link = [link for link in all_links if re.search(subject, link, re.IGNORECASE)]
    bthn = r'bai-tap-hang-ngay-toan'
    bthn_link = [link1 for link1 in subject_link if re.search(bthn, link1, re.IGNORECASE)]
    # Patterns to match grade levels
    grade_patterns = {
        'grade1': r'lop-1-',
        'grade2': r'lop-2-',
        'grade3': r'lop-3-',
        'grade4': r'lop-4-',
        'grade5': r'lop-5-'
    }
    
    # Filter links for each grade
    for link in bthn_link:
        for grade, pattern in grade_patterns.items():
            if re.search(pattern, link, re.IGNORECASE):
                grade_links[grade].append(link)
                break  # Stop checking other patterns once found
    
    # Save links for each grade to separate JSON files
    for grade, links in grade_links.items():
        filename = f'../link_crawl/{grade}_links_{bthn}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(links)} links to {filename}")
    
    # Print summary
    print("\nSummary:")
    print(f"Total Vietnamese links found: {len(bthn_link)}")
    for grade, links in grade_links.items():
        print(f"{grade}: {len(links)} links")

if __name__ == "__main__":
    filter_links_by_grade() 