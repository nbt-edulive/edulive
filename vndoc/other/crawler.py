from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import json
import time

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(options=options)

def crawl_data(url, class_index):
    driver = setup_driver()
    try:
        driver.get(url)
        # Wait for the toc-navbar to be present
        wait = WebDriverWait(driver, 10)
        toc_navbar = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "toc-navbar")))
        
        # Find all priority items
        priority_items = toc_navbar.find_elements(By.CSS_SELECTOR, ".item-nav.childs.collapse.show.priority")
        
        data = []
        for priority_item in priority_items:
            # Find all childst not-col elements
            child_items = priority_item.find_elements(By.CSS_SELECTOR, ".childst.not-col")
            
            for idx, child_item in enumerate(child_items, start=1):
                try:
                    # Get the title
                    title = child_item.find_element(By.TAG_NAME, "a").text.strip()
                    # Get the href
                    href = child_item.find_element(By.TAG_NAME, "a").get_attribute("href")
                    
                    # Create new index using class number from JSON file
                    new_index = f"class {class_index}"
                    
                    data.append({
                        "class": new_index,
                        "title": title,
                        "href": href,
                        "class_number": class_index
                    })
                except Exception as e:
                    print(f"Error processing item: {e}")
                    continue
        
        return data
    except TimeoutException:
        print(f"Timeout waiting for elements on {url}")
        return []
    finally:
        driver.quit()

def main():
    # Read URLs from JSON file
    with open('link_class1-12.json', 'r', encoding='utf-8') as f:
        urls = json.load(f)
    
    all_data = []
    for index, url in enumerate(urls, start=1):
        print(f"Crawling class {index}: {url}")
        data = crawl_data(url, index)
        all_data.extend(data)
        time.sleep(2)  # Add delay between requests
    
    # Save results to JSON file
    with open('crawled_data.json', 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"Crawling completed. Total items: {len(all_data)}")

if __name__ == "__main__":
    main() 