import json
import re

def filter_links_by_grade():
    # Read all links from processed_hrefs.json
    with open('processed_hrefs.json', 'r', encoding='utf-8') as f:
        all_links = json.load(f)
    
    # Initialize lists for each grade
    grade_links = {
        'grade6': [],
        'grade7': [],
        'grade8': [],
        'grade9': [],
        'grade10': [],
        'grade11': [],
        'grade12': [],
    }
    
    # First filter for Vietnamese language links
    subject = r'tieng-viet'
    subject_link = [link for link in all_links if re.search(subject, link, re.IGNORECASE)]
    
    # Patterns to match grade levels
    grade_patterns = {
        'grade6': r'lop-6-',
        'grade7': r'lop-7-',
        'grade8': r'lop-8-',
        'grade9': r'lop-9-',
        'grade10': r'lop-10-',
        'grade11': r'lop-11-',
        'grade12': r'lop-12-'
    }
    
    # Filter links for each grade
    for link in subject_link:
        for grade, pattern in grade_patterns.items():
            if re.search(pattern, link, re.IGNORECASE):
                grade_links[grade].append(link)
                break  # Stop checking other patterns once found
    
    # Save links for each grade to separate JSON files
    for grade, links in grade_links.items():
        filename = f'../data_6-12/{grade}_links_{subject}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(links, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(links)} links to {filename}")
    
    # Print summary
    print("\nSummary:")
    print(f"Total Vietnamese links found: {len(subject_link)}")
    for grade, links in grade_links.items():
        print(f"{grade}: {len(links)} links")

if __name__ == "__main__":
    filter_links_by_grade() 