from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import html2text
import json
import time
import os
import re
from bs4 import BeautifulSoup
import logging
import concurrent.futures
import random
from tqdm import tqdm

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

def setup_driver():
    """Khởi tạo và cấu hình trình duyệt Chrome"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Chạy ở chế độ không có giao diện
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-images')  # Tắt tải hình ảnh để tăng tốc
    options.add_argument('--disable-extensions')  # Tắt tiện ích mở rộng
    options.add_argument('--disable-infobars')
    options.add_argument('--disable-notifications')
    
    # Thêm User-Agent để tránh bị chặn
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    # Tùy chọn để tăng tốc độ tải trang
    prefs = {
        'profile.default_content_setting_values': {
            'images': 2,  # Không tải hình ảnh
            'plugins': 2,  # Tắt plugins
            'popups': 2,  # Chặn popups
            'geolocation': 2,  # Tắt vị trí địa lý
            'notifications': 2  # Tắt thông báo
        },
        'disk-cache-size': 52428800  # Cache 50MB
    }
    options.add_experimental_option('prefs', prefs)
    
    try:
        return webdriver.Chrome(options=options)
    except Exception as e:
        logger.error(f"Không thể khởi tạo driver: {e}")
        raise

def clean_html(html_content):
    """Làm sạch HTML bằng cách loại bỏ các phần tử không mong muốn"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Loại bỏ các phần tử có class không mong muốn
    unwanted_classes = [
        'moreTabs',
        'Banner-noads onload onready mg-b'
    ]
    
    # Xóa các phần tử theo class
    for class_name in unwanted_classes:
        elements = soup.find_all(class_=class_name)
        for element in elements:
            element.decompose()
    
    # Xóa các phần tử theo id
    unwanted_ids = [
        'articlevideoads'
    ]
    
    # Xóa các phần tử theo id
    for id_name in unwanted_ids:
        element = soup.find(id=id_name)
        if element:
            element.decompose()
    
    return str(soup)

def process_images(html_content):
    """Xử lý hình ảnh trong nội dung HTML"""
    soup = BeautifulSoup(html_content, 'html.parser')
    images = soup.find_all('img')
    
    for img in images:
        # Kiểm tra nếu src là hình ảnh được mã hóa base64
        src = img.get('src', '')
        if src.startswith('data:image'):
            img.decompose()
            continue
            
        # Cố gắng lấy URL gốc của hình ảnh từ các thuộc tính khác nhau
        original_src = img.get('data-src') or img.get('data-original') or src
        if original_src and 'holder' not in original_src and not original_src.startswith('data:image'):
            img['src'] = original_src
            # Thêm alt text nếu không có
            if not img.get('alt'):
                img['alt'] = 'image'
        else:
            img.decompose()
    
    return str(soup)

def clean_markdown(markdown_content):
    """Làm sạch và chuẩn hóa nội dung Markdown"""
    # Loại bỏ các dòng trống liên tiếp
    markdown_content = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown_content)
    
    # Loại bỏ các ký tự đặc biệt không cần thiết
    markdown_content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', markdown_content)
    
    # Loại bỏ các chuỗi mã hóa không hợp lệ
    markdown_content = re.sub(r'&#[x0-9a-fA-F]+;', '', markdown_content)
    
    # Chuẩn hóa dấu xuống dòng
    markdown_content = markdown_content.replace('\r\n', '\n')
    
    return markdown_content

def convert_to_markdown(html_content):
    """Chuyển đổi HTML sang Markdown"""
    # Làm sạch HTML trước
    cleaned_html = clean_html(html_content)
    
    # Xử lý hình ảnh
    processed_html = process_images(cleaned_html)
    
    # Cấu hình html2text
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False  # Giữ hình ảnh trong markdown
    h.body_width = 0  # Tắt ngắt dòng văn bản
    h.unicode_snob = True  # Giữ nguyên ký tự Unicode
    h.escape_snob = True  # Thoát các ký tự đặc biệt
    h.single_line_break = True  # Dòng mới đơn thay vì dòng mới kép
    h.protect_links = True  # Bảo vệ các liên kết
    
    # Chuyển đổi HTML sang Markdown
    markdown = h.handle(processed_html)
    
    # Làm sạch nội dung Markdown
    markdown = clean_markdown(markdown)
    
    return markdown

def sanitize_filename(url):
    """Tạo tên file an toàn từ URL"""
    # Trích xuất tên file từ URL và loại bỏ các ký tự không hợp lệ
    filename = re.sub(r'https?://', '', url)
    filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    # Giới hạn độ dài tên file
    if len(filename) > 100:
        filename = filename[:100]
    
    if not filename.endswith('.md'):
        filename += '.md'
    
    return filename

def extract_metadata(driver, url):
    """Trích xuất metadata từ trang web"""
    metadata = {
        'url': url,
        'title': driver.title,
        'date_extracted': time.strftime('%Y-%m-%d %H:%M:%S'),
    }
    
    # Cố gắng trích xuất thời gian xuất bản, tác giả, v.v.
    try:
        # Tìm kiếm thẻ meta để lấy thông tin
        for meta in driver.find_elements(By.TAG_NAME, 'meta'):
            name = meta.get_attribute('name') or meta.get_attribute('property') or ''
            content = meta.get_attribute('content') or ''
            
            if name.lower() in ['author', 'publication_date', 'date', 'description', 'keywords']:
                metadata[name.lower()] = content
    except Exception as e:
        logger.warning(f"Không thể trích xuất metadata đầy đủ: {e}")
    
    return metadata

def save_file(filepath, content, metadata=None):
    """Lưu nội dung vào file với metadata (nếu có)"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            if metadata:
                f.write('---\n')
                for key, value in metadata.items():
                    if value:
                        f.write(f'{key}: {value}\n')
                f.write('---\n\n')
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Lỗi khi lưu file {filepath}: {e}")
        return False

def process_url(url, output_dir, retry_count=3, timeout=30):
    """Xử lý một URL và chuyển đổi nội dung sang Markdown"""
    driver = None
    for attempt in range(retry_count):
        try:
            driver = setup_driver()
            driver.set_page_load_timeout(timeout)  # Đặt thời gian chờ
            
            # Thêm độ trễ ngẫu nhiên để tránh bị chặn
            time.sleep(random.uniform(1.0, 3.0))
            
            driver.get(url)
            
            # Đợi nội dung chính xuất hiện
            wait = WebDriverWait(driver, 10)
            main_content = None
            
            # Thử tìm nội dung chính bằng nhiều bộ chọn khác nhau
            try:
                main_content = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "maincontent.textview.padingads")))
            except TimeoutException:
                # Thử các bộ chọn thay thế
                selectors = [
                    ".maincontent",
                    ".textview",
                    "article",
                    "#content",
                    ".content",
                    "main"
                ]
                
                for selector in selectors:
                    try:
                        main_content = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        break
                    except:
                        continue
                
                if not main_content:
                    # Lấy toàn bộ nội dung trang nếu không tìm thấy bộ chọn cụ thể
                    main_content = driver.find_element(By.TAG_NAME, "body")
            
            # Cuộn để tải tất cả nội dung
            driver.execute_script("""
                function scrollToBottom() {
                    window.scrollTo(0, document.body.scrollHeight);
                    return document.body.scrollHeight;
                }
                
                let lastHeight = 0;
                let newHeight = scrollToBottom();
                
                while (lastHeight !== newHeight) {
                    lastHeight = newHeight;
                    setTimeout(() => {
                        newHeight = scrollToBottom();
                    }, 1000);
                }
            """)
            time.sleep(2)  # Đợi nội dung tải
            
            # Lấy nội dung HTML
            html_content = main_content.get_attribute('outerHTML')
            
            # Trích xuất metadata
            metadata = extract_metadata(driver, url)
            
            # Chuyển đổi sang Markdown
            markdown_content = convert_to_markdown(html_content)
            
            if markdown_content:
                # Tạo tên file từ URL
                filename = sanitize_filename(url)
                
                # Lưu vào file markdown
                filepath = os.path.join(output_dir, filename)
                if save_file(filepath, markdown_content, metadata):
                    return True
            return False
            
        except TimeoutException:
            logger.warning(f"Timeout khi truy cập {url}, lần thử {attempt+1}/{retry_count}")
            if attempt == retry_count - 1:
                logger.error(f"Đã hết số lần thử cho {url}")
                return False
            
            # Tăng thời gian chờ cho lần thử tiếp theo
            timeout += 10
            
        except WebDriverException as e:
            if "page crash" in str(e).lower() or "connection refused" in str(e).lower():
                logger.warning(f"Trang web bị crash hoặc từ chối kết nối: {url}, lần thử {attempt+1}/{retry_count}")
                time.sleep(random.uniform(5.0, 10.0))  # Đợi lâu hơn
            else:
                logger.error(f"Lỗi trình duyệt khi xử lý {url}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Lỗi khi xử lý {url}: {str(e)}")
            return False
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    return False

def process_batch(urls_batch, output_dir):
    """Xử lý một batch các URL"""
    results = []
    for url in urls_batch:
        success = process_url(url, output_dir)
        results.append((url, success))
    return results

def main():
    # Tạo thư mục đầu ra nếu chưa tồn tại
    output_dir = '../data_markdown/markdown_files_tv4'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Thư mục cho các URL thất bại
    failed_dir = os.path.join(output_dir, 'failed')
    if not os.path.exists(failed_dir):
        os.makedirs(failed_dir)
    
    # Đọc URL từ file JSON
    try:
        with open('../link_crawl/grade4_links_tieng-viet.json', 'r', encoding='utf-8') as f:
            urls = json.load(f)
        
        # Tạo file cho việc nối tiếp
        checkpoint_file = '../checkpoint/checkpoint_tv4.json'
        processed_urls = set()
        
        # Kiểm tra xem đã có tiến độ được lưu trước đó không
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    checkpoint_data = json.load(f)
                    processed_urls = set(checkpoint_data.get('processed_urls', []))
                    logger.info(f"Đã tải {len(processed_urls)} URL đã xử lý từ checkpoint")
            except:
                logger.warning("Không thể tải checkpoint, bắt đầu từ đầu")
        
        # Lọc ra các URL chưa được xử lý
        urls_to_process = [url for url in urls if url not in processed_urls]
        
        total_urls = len(urls_to_process)
        if total_urls == 0:
            logger.info("Tất cả các URL đã được xử lý!")
            return
            
        logger.info(f"Bắt đầu xử lý {total_urls} URLs...")
        
        # Các biến theo dõi
        processed_count = 0
        failed_count = 0
        failed_urls = []
        
        # Số lượng worker và kích thước batch
        max_workers = min(10, os.cpu_count() * 2)  # Điều chỉnh theo tài nguyên có sẵn
        batch_size = 5  # Số lượng URL mỗi batch
        
        # Chia URLs thành các batch
        url_batches = [urls_to_process[i:i+batch_size] for i in range(0, len(urls_to_process), batch_size)]
        
        with tqdm(total=total_urls, desc="Crawling URLs") as pbar:
            for batch in url_batches:
                batch_results = []
                
                # Xử lý batch hiện tại
                for url in batch:
                    result = process_url(url, output_dir)
                    batch_results.append((url, result))
                    
                    # Cập nhật trạng thái
                    if result:
                        processed_count += 1
                        processed_urls.add(url)
                    else:
                        failed_count += 1
                        failed_urls.append(url)
                    
                    pbar.update(1)
                    
                    # Lưu checkpoint sau mỗi URL
                    try:
                        with open(checkpoint_file, 'w', encoding='utf-8') as f:
                            checkpoint_data = {
                                'processed_urls': list(processed_urls),
                                'failed_urls': failed_urls
                            }
                            json.dump(checkpoint_data, f)
                    except Exception as e:
                        logger.warning(f"Không thể lưu tiến độ: {e}")
                
                # Đợi một chút giữa các batch để tránh bị chặn
                time.sleep(random.uniform(2.0, 5.0))
                
        # Lưu danh sách các URL thất bại
        failed_file = os.path.join(failed_dir, 'failed_urls.json')
        try:
            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_urls, f)
        except Exception as e:
            logger.error(f"Không thể lưu danh sách URL thất bại: {e}")
        
        logger.info("\nĐã hoàn thành xử lý!")
        logger.info(f"Tất cả các file được lưu trong thư mục '{output_dir}'")
        logger.info(f"\nTóm tắt:")
        logger.info(f"Tổng URL: {total_urls}")
        logger.info(f"Xử lý thành công: {processed_count}")
        logger.info(f"Thất bại: {failed_count}")
        logger.info(f"Danh sách URL thất bại được lưu tại: {failed_file}")
        
    except Exception as e:
        logger.error(f"Lỗi trong quá trình chính: {str(e)}")

if __name__ == "__main__":
    main()