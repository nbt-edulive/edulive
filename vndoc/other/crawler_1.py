import json
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import random
import traceback

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawl_navbar.log'),
        logging.StreamHandler()
    ]
)

class NavbarCrawler:
    def __init__(self, json_file='all_hrefs.json'):
        self.json_file = json_file
        self.index = 1
        self.results = []
        self.setup_driver()

    def setup_driver(self):
        """Thiết lập WebDriver với các tùy chọn phù hợp"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Random user agent
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36'
        ]
        chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.set_page_load_timeout(30)
        self.wait = WebDriverWait(self.driver, 30)

    def load_urls(self):
        """Đọc danh sách URLs từ file JSON"""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Lỗi khi đọc file JSON: {str(e)}")
            return []

    def extract_navbar_data(self, url):
        """Trích xuất dữ liệu từ navbar theo cấu trúc phân cấp"""
        try:
            self.driver.get(url)
            time.sleep(random.uniform(2, 5))  # Random delay

            # Đợi navbar chính xuất hiện
            navbar = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "toc-navbar"))
            )

            # Lấy tất cả các item-nav childs
            item_navs = navbar.find_elements(By.CLASS_NAME, "item-nav.childs.collapse.show")
            
            for item_nav in item_navs:
                # Lấy các ul-one trong mỗi item-nav
                ul_ones = item_nav.find_elements(By.CLASS_NAME, "ul-one")
                
                for ul_one in ul_ones:
                    # Lấy các childst not-col trong mỗi ul-one
                    childsts = ul_one.find_elements(By.CLASS_NAME, "childst.not-col")
                    
                    for childst in childsts:
                        try:
                            # Lấy title và href từ mỗi childst
                            title = childst.find_element(By.TAG_NAME, "a").text.strip()
                            href = childst.find_element(By.TAG_NAME, "a").get_attribute("href")
                            
                            # Thêm vào kết quả với index
                            self.results.append({
                                "index": self.index,
                                "title": title,
                                "href": href,
                                "url": url
                            })
                            self.index += 1
                            logging.info(f"Đã thêm: {title}")
                        except Exception as e:
                            logging.error(f"Lỗi khi xử lý childst: {str(e)}")
                            continue

        except Exception as e:
            logging.error(f"Lỗi khi xử lý URL {url}: {str(e)}")
            logging.error(traceback.format_exc())

    def save_results(self):
        """Lưu kết quả vào file JSON"""
        try:
            with open('navbar_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logging.info(f"Đã lưu {len(self.results)} kết quả vào navbar_data.json")
        except Exception as e:
            logging.error(f"Lỗi khi lưu kết quả: {str(e)}")

    def crawl(self):
        """Thực hiện quá trình crawl"""
        urls = self.load_urls()
        total_urls = len(urls)
        
        for i, url in enumerate(urls, 1):
            logging.info(f"Đang xử lý URL {i}/{total_urls}: {url}")
            self.extract_navbar_data(url)
            
            # Lưu checkpoint sau mỗi 5 URL
            if i % 5 == 0:
                self.save_results()
                logging.info(f"Đã lưu checkpoint sau {i} URL")
            
            # Random delay giữa các request
            time.sleep(random.uniform(2, 5))

        self.save_results()
        self.driver.quit()

def main():
    crawler = NavbarCrawler()
    crawler.crawl()

if __name__ == "__main__":
    main() 