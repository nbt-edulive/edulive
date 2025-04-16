from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from webdriver_manager.chrome import ChromeDriverManager
import time
import html2text
import os
import re
import json
import urllib.parse

def login_to_onthi123(username, password, max_retries=3):
    # Thiết lập trình duyệt Chrome
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--headless")
    # Khởi tạo trình duyệt
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    print("start")
    try:
        # Truy cập trang đăng nhập
        print("Đang truy cập trang đăng nhập...")
        driver.get("https://onthi123.vn/de-luyen-so-01-mon-tieng-viet")
        
        # Chờ trang tải xong và chờ form xuất hiện
        wait = WebDriverWait(driver, 10)
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        
        # Tìm và điền thông tin đăng nhập
        print("Đang điền thông tin đăng nhập...")
        username_field.clear()
        username_field.send_keys(username)
        
        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)
        

        print("Đang nhấn nút đăng nhập...")
        
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        
        retries = 0
        success = False
        
        while not success and retries < max_retries:
            try:
                # Phương pháp 1: Click thông thường
                login_button.click()
                success = True
            except ElementClickInterceptedException:
                retries += 1
                print(f"Thử lại lần {retries}...")
                
                try:
                    # Phương pháp 2: Sử dụng JavaScript để click
                    driver.execute_script("arguments[0].click();", login_button)
                    success = True
                except Exception:
                    # Phương pháp 3: Cuộn đến phần tử và thử lại
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
                    time.sleep(1)
                    
                    try:
                        # Phương pháp 4: Nhấn Enter thay vì click
                        password_field.send_keys("\n")
                        success = True
                    except Exception:
                        # Đợi một chút và thử lại vòng lặp
                        time.sleep(2)
        
        if not success:
            print("Không thể nhấn nút đăng nhập sau nhiều lần thử.")
            return None
        
        # Chờ đăng nhập hoàn tất
        print("Đang chờ đăng nhập hoàn tất...")
        time.sleep(5)
        
        # Kiểm tra đăng nhập thành công
        if "dang-nhap" not in driver.current_url:
            print("Đăng nhập thành công!")
        else:
            print("Đăng nhập thất bại. Vui lòng kiểm tra lại thông tin đăng nhập.")
        
        return driver
        
    except Exception as e:
        print(f"Có lỗi xảy ra: {e}")
        driver.quit()
        return None

def extract_content_to_markdown(driver, url=None, output_file="output.md"):
    if url:
        try:
            print(f"Đang truy cập URL: {url}")
            driver.get(url)
            time.sleep(3)  # Đợi trang tải xong
        except Exception as e:
            print(f"Lỗi khi truy cập URL {url}: {e}")
            return False

    try:
        # Chờ cho class module-content__test xuất hiện
        print("Đang chờ nội dung tải...")
        wait = WebDriverWait(driver, 15)
        content_element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "module-content__test")))
        
        # Lấy HTML từ phần tử
        print("Đã tìm thấy nội dung, đang trích xuất...")
        html_content = content_element.get_attribute('outerHTML')
        
        # Xử lý HTML trước khi chuyển đổi để thêm domain vào src của ảnh
        
        # Thêm domain onthi123.vn vào src ảnh nếu chúng bắt đầu với /
        pattern1 = r'src="(/[^"]*)"'
        html_content = re.sub(pattern1, r'src="https://onthi123.vn\1"', html_content)
        
        # Thêm domain onthi123.vn vào src ảnh nếu chúng bắt đầu với public/
        pattern2 = r'src="(public/[^"]*)"'
        html_content = re.sub(pattern2, r'src="https://onthi123.vn/\1"', html_content)
        
        # Chuyển đổi HTML sang Markdown
        print("Đang chuyển đổi HTML sang Markdown...")
        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = False
        converter.body_width = 0  # Tắt wrapping
        
        markdown_content = converter.handle(html_content)
        
        pattern_md1 = r'!\[(.*?)\]\((/[^)]*)\)'
        markdown_content = re.sub(pattern_md1, r'![\1](https://onthi123.vn\2)', markdown_content)
        
        # Xử lý đường dẫn bắt đầu bằng public/
        pattern_md2 = r'!\[(.*?)\]\((public/[^)]*)\)'
        markdown_content = re.sub(pattern_md2, r'![\1](https://onthi123.vn/\2)', markdown_content)
        
        # Lưu nội dung vào file
        print(f"Đang lưu nội dung vào file {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Đã lưu nội dung thành công vào file {output_file}")
        return True
        
    except Exception as e:
        print(f"Có lỗi khi trích xuất nội dung: {e}")
        return False

def generate_filename_from_url(url):
    # Trích xuất phần cuối của URL
    path = urllib.parse.urlparse(url).path
    # Lấy phần cuối của đường dẫn
    filename = os.path.basename(path)
    
    # Nếu không có tên file (url kết thúc bằng /), lấy phần trước /
    if not filename:
        parts = path.strip('/').split('/')
        if parts:
            filename = parts[-1]
        else:
            # Nếu không thể trích xuất, sử dụng domain
            domain = urllib.parse.urlparse(url).netloc
            filename = domain.replace('.', '-')
    
    # Thay thế các ký tự không hợp lệ trong tên file
    filename = re.sub(r'[^\w\-\.]', '-', filename)
    
    # Nếu filename vẫn trống, dùng timestamp
    if not filename:
        filename = f"crawl-{int(time.time())}"
    
    # Thêm .md nếu không có extension
    if not filename.endswith('.md'):
        filename += '.md'
    
    return filename

def load_urls_from_json(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        else:
            print(f"Lỗi: Định dạng JSON không hợp lệ. Cần là mảng URLs.")
            return []
    except Exception as e:
        print(f"Lỗi khi đọc file JSON: {e}")
        return []

def save_checkpoint(checkpoint_file, completed_urls):
    try:
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(completed_urls, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu checkpoint với {len(completed_urls)} URL hoàn thành.")
    except Exception as e:
        print(f"Lỗi khi lưu checkpoint: {e}")

def load_checkpoint(checkpoint_file):
    if not os.path.exists(checkpoint_file):
        return []
    
    try:
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            completed_urls = json.load(f)
        print(f"Đã tải checkpoint: {len(completed_urls)} URL đã hoàn thành trước đó.")
        return completed_urls
    except Exception as e:
        print(f"Lỗi khi tải checkpoint: {e}. Bắt đầu từ đầu.")
        return []

def crawl_multiple_urls(username, password, json_file, output_dir="crawled_data"):
    # Tạo thư mục output nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Tải danh sách URLs từ file JSON
    urls = load_urls_from_json(json_file)
    
    if not urls:
        print("Không có URL nào để crawl. Kiểm tra lại file JSON.")
        return
    
    # Tạo tên file checkpoint dựa trên tên file JSON
    checkpoint_file = os.path.join(output_dir, os.path.basename(json_file).replace('.json', '_checkpoint.json'))
    
    # Tải danh sách URLs đã hoàn thành từ checkpoint (nếu có)
    completed_urls = load_checkpoint(checkpoint_file)
    
    # Lọc những URL chưa xử lý
    remaining_urls = [url for url in urls if url not in completed_urls]
    
    if not remaining_urls:
        print("Tất cả URL đã được xử lý trước đó!")
        return
    
    print(f"Cần xử lý {len(remaining_urls)}/{len(urls)} URL.")
    
    # Đăng nhập vào hệ thống
    driver = login_to_onthi123(username, password)
    
    if not driver:
        print("Không thể đăng nhập. Kiểm tra lại thông tin đăng nhập.")
        return
    
    try:
        # Duyệt qua từng URL và trích xuất nội dung
        for i, url in enumerate(remaining_urls, 1):
            print(f"\n[{i}/{len(remaining_urls)}] Đang xử lý URL: {url}")
            
            # Tạo tên file dựa trên URL
            filename = generate_filename_from_url(url)
            output_path = os.path.join(output_dir, filename)
            
            # Trích xuất nội dung với cơ chế thử lại nếu phiên hết hạn
            max_retries = 3
            for attempt in range(max_retries):
                # Trích xuất nội dung
                success = extract_content_to_markdown(driver, url, output_path)
                
                if success:
                    print(f"Đã crawl thành công: {url} -> {output_path}")
                    # Thêm URL đã crawl thành công vào danh sách hoàn thành
                    completed_urls.append(url)
                    # Lưu checkpoint sau mỗi URL thành công
                    save_checkpoint(checkpoint_file, completed_urls)
                    break
                elif "dang-nhap" in driver.current_url or attempt < max_retries - 1:
                    print(f"Phiên đăng nhập có thể đã hết hạn. Đang đăng nhập lại (lần thử {attempt+1}/{max_retries})...")
                    driver.quit()
                    driver = login_to_onthi123(username, password)
                    if not driver:
                        print("Không thể đăng nhập lại. Dừng quá trình crawl.")
                        # Lưu checkpoint trước khi thoát
                        save_checkpoint(checkpoint_file, completed_urls)
                        return
                    time.sleep(3)  # Đợi đăng nhập hoàn tất
                else:
                    print(f"Không thể crawl: {url} sau {max_retries} lần thử")
            
            # Đợi một chút để tránh quá tải server
            time.sleep(2)
        
        print(f"\nĐã hoàn thành việc crawl {len(remaining_urls)} URL.")
    
    except KeyboardInterrupt:
        print("\nQuá trình crawl bị gián đoạn. Đang lưu tiến trình...")
        save_checkpoint(checkpoint_file, completed_urls)
        print(f"Đã lưu tiến trình. {len(completed_urls)}/{len(urls)} URL đã hoàn thành.")
    
    except Exception as e:
        print(f"Lỗi không mong muốn: {e}")
        save_checkpoint(checkpoint_file, completed_urls)
        print(f"Đã lưu tiến trình. {len(completed_urls)}/{len(urls)} URL đã hoàn thành.")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    # Thông tin đăng nhập
    username = "NBT03"
    password = "Taotentien123a@"
    
    # File JSON chứa danh sách URLs cần crawl
    json_file = "data/dethi_lop6_ta/dethi_tienganh.json"
    
    # Thư mục lưu trữ kết quả
    output_dir = "data/dethi_lop6_ta"
    
    # Crawl nhiều URLs
    crawl_multiple_urls(username, password, json_file, output_dir)