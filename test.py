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

def login_to_onthi123(username, password, max_retries=3):
    """
    Hàm đăng nhập vào trang onthi123.vn sử dụng Selenium với xử lý lỗi click
    
    Args:
        username (str): Tên đăng nhập
        password (str): Mật khẩu
        max_retries (int): Số lần thử lại tối đa
    
    Returns:
        webdriver: Trình duyệt đã đăng nhập
    """
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
        driver.get("https://onthi123.vn/de-kiem-tra-giua-ki-i-toan-de-so-1")
        
        # Chờ trang tải xong và chờ form xuất hiện
        wait = WebDriverWait(driver, 10)
        username_field = wait.until(EC.presence_of_element_located((By.NAME, "username")))
        
        # Tìm và điền thông tin đăng nhập
        print("Đang điền thông tin đăng nhập...")
        username_field.clear()
        username_field.send_keys(username)
        
        # Tìm và điền password
        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        password_field.send_keys(password)
        
        # Nhấn nút đăng nhập với xử lý lỗi
        print("Đang nhấn nút đăng nhập...")
        
        # Tìm nút đăng nhập
        login_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']")))
        
        # Thử các phương pháp khác nhau để click nút
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

def extract_content_to_markdown(driver, output_file="output.md"):

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
        
        # Xử lý lại markdown để đảm bảo src ảnh đã được thêm domain
        # html2text chuyển src ảnh thành dạng ![alt](link)
        
        # Xử lý đường dẫn bắt đầu bằng /
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

if __name__ == "__main__":
    # Nhập thông tin đăng nhập
    username = "NBT03"
    password = "Taotentien123a@"
    
    # Thực hiện đăng nhập
    driver = login_to_onthi123(username, password)
    
    # Sau khi đăng nhập, bạn có thể tiếp tục với các thao tác khác
    if driver:
        try:
            # Trích xuất nội dung và chuyển sang Markdown
            print("Bắt đầu trích xuất nội dung...")
            extract_content_to_markdown(driver)
        finally:
            driver.quit()