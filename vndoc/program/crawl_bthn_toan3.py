import json
import os
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import html2text  # Thêm thư viện html2text
from datetime import datetime

def setup_driver():
    """Set up and return a configured webdriver."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    return driver

def load_links(json_file):
    """Load links from a JSON file."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File {json_file} not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: File {json_file} contains invalid JSON.")
        return []

def load_checkpoint(checkpoint_file):
    """Load the checkpoint of crawled links."""
    try:
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_checkpoint(checkpoint_file, crawled_links):
    """Save the checkpoint of crawled links."""
    with open(checkpoint_file, 'w', encoding='utf-8') as f:
        json.dump(crawled_links, f, ensure_ascii=False, indent=4)

def extract_title(driver):
    """Extract title of the quiz from the page."""
    try:
        # Trước hết, thử lấy tiêu đề từ thẻ title
        title = driver.title
        
        # Nếu không có tiêu đề hoặc tiêu đề quá chung chung, thử tìm trong các phần tử khác
        if not title or title == "VnDoc.com" or "vndoc" in title.lower():
            # Thử tìm trong phần mô tả
            try:
                description = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.mode-des.textview p"))
                )
                title = description.text
            except:
                pass
            
            # Nếu vẫn không tìm thấy, thử tìm trong tiêu đề kết quả
            if not title:
                try:
                    result_title = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "span.result-model"))
                    )
                    title = result_title.text
                except:
                    pass
        
        # Nếu vẫn không tìm thấy, trả về URL làm tiêu đề
        if not title:
            title = "Unknown Quiz"
            
        return title
    except Exception as e:
        print(f"Error extracting title: {str(e)}")
        return "Unknown Quiz"

def extract_description(driver):
    """Extract description from the page."""
    try:
        description_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.mode-des.textview p"))
        )
        return description_element.text
    except:
        return "No description available"

def save_content(url, content, title, description, output_dir):
    """Save the extracted content to a file with metadata."""
    # Tạo tên file từ URL
    filename = url.replace('://', '_').replace('/', '_').replace('?', '_').replace('&', '_') + '.md'
    filepath = os.path.join(output_dir, filename)
    
    # Tạo metadata
    now = datetime.now()
    metadata = f"""---
title: "{title}"
url: "{url}"
date_crawled: "{now.strftime('%Y-%m-%d %H:%M:%S')}"
description: "{description}"
---

"""
    
    # Lưu nội dung với metadata
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(metadata + content)
    
    print(f"Content saved to {filepath}")
    return filename

def clean_html(html_content):
    """Clean HTML content by removing unwanted elements."""
    # Xóa các script và style tags
    html_content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', html_content)
    html_content = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', html_content)
    
    # Các bước clean HTML khác nếu cần
    return html_content

def extract_markdown_content(driver):
    """Extract markdown content from the targeted div."""
    try:
        # Wait for the target div to appear
        content_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.listQuiz"))
        )
        
        # Get the HTML content
        html_content = content_div.get_attribute('innerHTML')
        
        # Clean HTML if needed
        cleaned_html = clean_html(html_content)
        
        # Convert HTML to Markdown
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.bypass_tables = False
        converter.images_to_alt = True
        converter.unicode_snob = True  # Giữ unicode
        converter.body_width = 0  # Không giới hạn độ rộng
        
        markdown_content = converter.handle(cleaned_html)
        
        return markdown_content
    except TimeoutException:
        print("Error: Timed out waiting for content div.")
        return ""
    except NoSuchElementException:
        print("Error: Content div not found.")
        return ""

def crawl_website(links_file, checkpoint_file, output_dir):
    """Main function to crawl the website."""
    # Load links and checkpoint
    links = load_links(links_file)
    crawled_links = load_checkpoint(checkpoint_file)
    
    # Tính toán số lượng links đã crawl và tổng số
    total_links = len(links)
    initial_crawled_count = len(crawled_links)
    current_crawled_count = initial_crawled_count
    
    print(f"=== CRAWLING PROGRESS ===")
    print(f"Total links to crawl: {total_links}")
    print(f"Links already crawled: {initial_crawled_count}")
    print(f"Links remaining: {total_links - initial_crawled_count}")
    print(f"Progress: {initial_crawled_count}/{total_links} ({initial_crawled_count/total_links*100:.2f}%)")
    print(f"=======================")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Tạo file log cho metadata
    log_file = os.path.join(output_dir, "metadata_log.txt")
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\n=== NEW CRAWLING SESSION: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
    
    # Set up the webdriver
    driver = setup_driver()
    
    # Thời gian bắt đầu
    start_time = time.time()
    
    try:
        for i, url in enumerate(links):
            # Skip if already crawled
            if url in crawled_links:
                print(f"[{i+1}/{total_links}] Skipping {url} (already crawled)")
                continue
            
            # Hiển thị tiến trình hiện tại
            print(f"[{i+1}/{total_links}] Crawling {url}...")
            
            try:
                # Load the page
                driver.get(url)
                
                # Wait for the page to load
                time.sleep(2)
                
                # Lấy title và description trước khi click
                page_title = extract_title(driver)
                page_description = extract_description(driver)
                
                # Find and click the section-start element
                section_start = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "section-start"))
                )
                section_start.click()
                
                # Wait for the content to load after clicking
                time.sleep(3)
                
                # Extract the markdown content
                content = extract_markdown_content(driver)
                
                if content:
                    # Save the content with metadata
                    saved_filename = save_content(url, content, page_title, page_description, output_dir)
                    
                    # Update checkpoint
                    crawled_links.append(url)
                    save_checkpoint(checkpoint_file, crawled_links)
                    
                    # Lưu metadata vào log
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f"URL: {url}\n")
                        f.write(f"Filename: {saved_filename}\n")
                        f.write(f"Title: {page_title}\n")
                        f.write(f"Description: {page_description}\n")
                        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write("---\n")
                    
                    # Cập nhật số lượng đã crawl
                    current_crawled_count += 1
                    
                    # Tính toán thời gian ước tính còn lại
                    elapsed_time = time.time() - start_time
                    links_done = current_crawled_count - initial_crawled_count
                    if links_done > 0:
                        time_per_link = elapsed_time / links_done
                        remaining_links = total_links - current_crawled_count
                        estimated_time_remaining = time_per_link * remaining_links
                        
                        # Chuyển đổi sang giờ:phút:giây
                        hours, remainder = divmod(estimated_time_remaining, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        print(f"Progress: {current_crawled_count}/{total_links} ({current_crawled_count/total_links*100:.2f}%)")
                        print(f"Estimated time remaining: {int(hours)}:{int(minutes):02d}:{int(seconds):02d}")
                
            except Exception as e:
                print(f"Error crawling {url}: {str(e)}")
                
                # Ghi lỗi vào log
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f"ERROR on {url}: {str(e)}\n")
                    f.write("---\n")
            
            # Add a small delay between requests to be polite
            time.sleep(3)
        
        # Hiển thị tổng kết sau khi hoàn thành
        total_time = time.time() - start_time
        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        print(f"\n=== CRAWLING COMPLETE ===")
        print(f"Total links: {total_links}")
        print(f"Links crawled this session: {current_crawled_count - initial_crawled_count}")
        print(f"Total links crawled: {current_crawled_count}")
        print(f"Total time: {int(hours)}:{int(minutes):02d}:{int(seconds):02d}")
        print(f"=========================")
        
        # Ghi tổng kết vào log
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n=== SESSION SUMMARY ===\n")
            f.write(f"Total links: {total_links}\n")
            f.write(f"Links crawled this session: {current_crawled_count - initial_crawled_count}\n")
            f.write(f"Total links crawled: {current_crawled_count}\n")
            f.write(f"Total time: {int(hours)}:{int(minutes):02d}:{int(seconds):02d}\n")
            f.write("======================\n\n")
        
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    # Configuration
    LINKS_FILE = "../link_crawl/grade3_links_bai-tap-hang-ngay-toan.json"  # JSON file containing the links to crawl
    CHECKPOINT_FILE = "../checkpoint/checkpoint_bthn_toan3.json"  # File to store crawled links
    OUTPUT_DIR = "../data_markdown/markdown_bthn_toan3"  # Directory to save extracted content
    
    # Run the crawler
    crawl_website(LINKS_FILE, CHECKPOINT_FILE, OUTPUT_DIR)