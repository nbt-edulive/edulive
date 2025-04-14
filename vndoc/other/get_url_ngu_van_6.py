from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json

def setup_driver():
	return webdriver.Chrome()

def read_json_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)
    
def save_json_file(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
def crawl_urls(data, driver):
    driver.get(data)
    hrefs = []
    urls = driver.find_elements(By.CSS_SELECTOR, ".toc-navbar a")
    for url in urls:
        href = url.get_attribute("href")
        if href:
            hrefs.append(href)
    return hrefs
if __name__ == "__main__":
    data = read_json_file("../data_6-12/class6.json")
    driver = setup_driver()
    save_json_file(crawl_urls(data, driver), "../data_6-12/data_subject/mon-van-lop-6/urls_mon_van_lop6.json")