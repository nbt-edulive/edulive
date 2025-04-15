from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import json

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def get_links_from_file(file_path):
    with open(file_path, "r") as file:
        return json.load(file)  

def get_links_from_url(driver, urls):
    links = []
    for url in urls:
        driver.get(url)
        try:
            # Chờ phần tử có class là "list-group-item" xuất hiện
            element = driver.find_elements(By.CSS_SELECTOR, ".ct-text a")
            for e in element:
                links.append(e.get_attribute("href"))
        except Exception as e:
            print(f"Error getting links from {url}: {e}")
    return links

def save_links_to_file(links, file_path):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(links, file, ensure_ascii=False, indent=4)

def main():
    driver = setup_driver()
    print("start")
    file_path = "data/lop9/toan.json"
    links = get_links_from_file(file_path)
    link_lop2 = get_links_from_url(driver, links)
    save_links_to_file(link_lop2, "data/lop9/links_lop9.json")
if __name__ == "__main__":
    main()


