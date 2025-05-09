import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from PIL import Image
import pytesseract
from io import BytesIO
import re

# Disable SSL warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Set Tesseract executable path (for Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

BASE_URL = 'https://freesearchigrservice.maharashtra.gov.in/'
TIMEOUT = 10

def find_captcha_img_src():
    try:
        print("[INFO] Streaming page to find CAPTCHA image...")
        with requests.get(BASE_URL, verify=False, timeout=TIMEOUT, stream=True) as response:
            response.raise_for_status()

            # Regex pattern to match: <img id="imgCaptcha" src="...">
            captcha_src_pattern = re.compile(r'<img[^>]*id=["\']imgCaptcha["\'][^>]*src=["\']([^"\']+)["\']', re.IGNORECASE)

            for line in response.iter_lines(decode_unicode=True):
                if line:
                    match = captcha_src_pattern.search(line)
                    if match:
                        img_src = match.group(1)
                        full_url = urljoin(BASE_URL, img_src)
                        print(f"[INFO] Found CAPTCHA image URL: {full_url}")
                        return full_url

            print("[ERROR] CAPTCHA image not found in streamed HTML.")
            return None

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Failed to stream page: {e}")
        return None

def get_captcha_text(img_url):
    try:
        # Step 3: Download the CAPTCHA image
        start_time = time.time()
        print("[INFO] Step 3: Downloading CAPTCHA image...")
        img_response = requests.get(img_url, verify=False, timeout=TIMEOUT)
        img_response.raise_for_status()
        download_time = time.time() - start_time
        print(f"[TIME] Image download time: {download_time:.2f} seconds")

        # Step 4: OCR the image
        start_time = time.time()
        print("[INFO] Step 4: Performing OCR on CAPTCHA image...")
        image = Image.open(BytesIO(img_response.content))
        captcha_text = pytesseract.image_to_string(image, config = '--psm 8 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789').strip()
        ocr_time = time.time() - start_time
        print(f"[TIME] OCR processing time: {ocr_time:.2f} seconds")

        return captcha_text

    except Exception as e:
        print(f"[ERROR] {e}")
        return None

if __name__ == '__main__':
    overall_start = time.time()
    img_url = find_captcha_img_src()
    if img_url:
        text = get_captcha_text(img_url)
        print(f'[RESULT] CAPTCHA Text: {text}' if text else "[RESULT] Failed to retrieve CAPTCHA.")
    else:
        print("[RESULT] Failed to retrieve CAPTCHA image URL.")
    print(f"[TOTAL TIME] Full process took: {time.time() - overall_start:.2f} seconds")
