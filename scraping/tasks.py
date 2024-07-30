from celery import shared_task
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import requests
from PIL import Image
from io import BytesIO
import base64
import os
from django.core.files.base import ContentFile
from django.core.cache import cache
from .models import ScrapedImage

@shared_task
def scrape_images(search_term, num_images, task_id):
    # Set up the Chrome WebDriver for headless operation
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # Open Google Images
    driver.get('https://images.google.com/')

    # Perform a search
    search_box = driver.find_element(By.NAME, 'q')
    search_box.send_keys(search_term)
    search_box.send_keys(Keys.RETURN)

    # Wait for images to load
    time.sleep(2)

    # Locate image elements
    images = driver.find_elements(By.CSS_SELECTOR, 'img.YQ4gaf')[:num_images]

    for index, image in enumerate(images):
        try:
            # Get the image source URL
            src = image.get_attribute('src')

            # Handle base64 encoded images
            if src.startswith('data:image'):
                base64_data = src.split(',')[1]
                image_data = base64.b64decode(base64_data)
                img = Image.open(BytesIO(image_data))
            else:
                response = requests.get(src)
                img = Image.open(BytesIO(response.content))

            # Convert image to RGB mode if necessary
            if img.mode in ("P", "RGBA"):
                img = img.convert("RGB")

            # Resize the image
            img = img.resize((640, 640))

            # Save image to a BytesIO object
            img_io = BytesIO()
            img.save(img_io, format='JPEG')
            img_content = ContentFile(img_io.getvalue(), f'{search_term}_{index + 1}.jpg')

            # Save image to the Django model
            filename = f'{search_term}_{index + 1}.jpg'
            scraped_image = ScrapedImage(
                task_id=task_id,
                filename=filename,
                search_term=search_term
            )
            scraped_image.image.save(filename, img_content)
            scraped_image.save()

            # Update progress in Redis
            cache.set(f'{task_id}_progress', index + 1)

            print(f'Downloaded and saved {search_term}_{index + 1}.jpg to the database')
        except Exception as e:
            print(f'Could not download image_{index + 1}: {e}')
            continue

    # Mark task as completed
    cache.set(f'{task_id}_status', 'completed')
    driver.quit()