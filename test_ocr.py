import cv2
import pytesseract
import os
import sys

# Setup Path
def get_tesseract_path() -> str | None:
    env_path = os.getenv("TESSERACT_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for path in windows_paths:
        if os.path.exists(path):
            return path
    return None

tesseract_path = get_tesseract_path()
if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
    print(f"Using Tesseract at: {tesseract_path}")
else:
    print("Tesseract not found!")
    sys.exit(1)

# Load Image
img_path = "data/captcha_processed.png"
if not os.path.exists(img_path):
    print(f"Image not found: {img_path}")
    sys.exit(1)

img = cv2.imread(img_path)
print(f"Loaded image: {img.shape}")

# Test Configurations
configs = [
    r'--psm 8 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', # Single Word
    r'--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', # Single Line
    r'--psm 10 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', # Single Char (bad)
    r'--psm 6 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', # Block
]

print("-" * 30)
for config in configs:
    try:
        text = pytesseract.image_to_string(img, config=config)
        print(f"Config: {config.split(' -c')[0]}")
        print(f"Result: '{text.strip()}'")
        print("-" * 30)
    except Exception as e:
        print(f"Error with config {config}: {e}")

# Try RGB conversion
print("Trying RGB conversion...")
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
text = pytesseract.image_to_string(img_rgb, config=configs[0])
print(f"Result (RGB): '{text.strip()}'")

# Try Inverted
print("Trying Inverted...")
img_inv = cv2.bitwise_not(img)
text = pytesseract.image_to_string(img_inv, config=configs[0])
print(f"Result (Inverted): '{text.strip()}'")
