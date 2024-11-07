from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

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

# Collecting individual category elements
categories = []
def append_category():
    i = 1
    while i < 10:
        data = driver.find_elements(By.CSS_SELECTOR, "div._1yQHx8._2UnIQ_._3ak8Rd")
        for category in data:
            categories.append(category)
        time.sleep(1)
        scroll_to_load()
        i += 1

append_category()

# Processing categories and products
processed_categories = set()
for category in categories:
    try:
        category_name = category.text.strip()
        if category_name in processed_categories:
            continue
        processed_categories.add(category_name)
        category_link = category.get_attribute('href')

        if category_link:
            print(f"Scraping category: {category_name}")
            driver.get(category_link)
            time.sleep(3)

            last_height = driver.execute_script("return document.body.scrollHeight")
            seen_products = set()

            while True:
                products = driver.find_elements(By.CLASS_NAME, '_58bkzq63')
                for product in products:
                    try:
                        product_name = product.text.strip()
                        if product_name in seen_products:
                            continue
                        seen_products.add(product_name)

                        product_data = {
                            "category": category_name,
                            "name": product_name,
                        }
                        collection.insert_one(product_data)
                        print(f"Inserted product: {product_name}")
                    except Exception as e:
                        print(f"Error extracting product data: {e}")
                
                scroll_to_load()
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
        else:
            product_data = {
                "category": category_name,
            }
            collection.insert_one(product_data)
            print(f"Inserted category: {category_name}")
    except Exception as e:
        print(f"Error processing category: {e}")

driver.quit()
