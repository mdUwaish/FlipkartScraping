from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup

# Database setup
client = MongoClient('mongodb://localhost:27017/')
db = client['mydatabase']
collection = db['categories']

# Set up Selenium WebDriver
options = webdriver.ChromeOptions()
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://www.flipkart.com/")

# Scroll function
def scroll_to_load():
    driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
    time.sleep(3)

def append_categories():
    categories = set()
    for _ in range(10):
        try:
            # Re-fetch category elements after each scroll
            category_elements = driver.find_elements(By.CSS_SELECTOR, "div._1yQHx8._2UnIQ_._3ak8Rd a")
            for category in category_elements:
                try:
                    category_name = category.text.strip()
                    category_link = category.get_attribute('href')
                    if category_name and category_link and (category_name, category_link) not in categories:
                        categories.add((category_name, category_link))
                except Exception as e:
                    print(f"Error accessing element: {e}")
            scroll_to_load()
        except Exception as e:
            print(f"Error in scrolling or fetching categories: {e}")
            continue

    return categories


categories = append_categories()

# Processing categories and products
for category_name, category_link in categories:
    print(f"Scraping category: {category_name} | Link: {category_link}")
    driver.get(category_link)
    
    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "krHvwW"))
    )

    last_height = driver.execute_script("return document.body.scrollHeight")
    # seen_products = set()
    product_data = {}
    
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    
    for product_div in soup.find_all('div', class_='hCKiGj'):
        # Find the brand and product name within this block
        brand = product_div.find('div', class_='syl9yP')
        product_name = product_div.find('a', class_='WKTcLC')
        product_price= product_div.find('div', class_='Nx9bqj')  # Nx9bqj
        original_price=product_div.find('div', class_='yRaY8j')
        percentage_off=product_div.find('div', class_='UkUFwK')
        offer=product_div.find('div', class_='n5vj9c')
        
        if brand and product_name:
            brand_name = brand.text.strip()
            product_name_text = product_name.text.strip()
            price_text = product_price.text.strip() if product_price else "Price not available"
            price_original = original_price.text.strip() if original_price else "Original Price"
            off = percentage_off.text.strip() if percentage_off else "No off"
            special_offer = offer.text.strip() if offer else "No offer"

            
            # Create nested structure in product_data dictionary
            if brand_name not in product_data:
                product_data[brand_name] = []
            if product_name_text not in product_data[brand_name]:
                product_data[brand_name].append({
                    "product_name":product_name_text,
                    "price":price_text,
                    "Before_price":price_original,
                    "Off":off,
                    "Deal":special_offer
                })
    
    # Insert into MongoDB in the desired structure
    category_document = {
        "category": category_name,
        "brands": [
            {
                "brand_name": brand_name,
                "products": product_data[brand_name]   
            }
            for brand_name in product_data
        ]
    }
    collection.insert_one(category_document)
    print(f"Inserted category '{category_name}' into MongoDB.")

driver.quit()