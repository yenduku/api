from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException
from bs4 import BeautifulSoup
import requests
import time
import random
from flask import Flask, jsonify,request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)
# Fetch Article Links
@app.route('/fetch_links', methods=['POST'])
def fetch_links():
    data = request.get_json()
    if not data or 'source' not in data:
        return jsonify({"error": "Missing 'source' parameter"}), 400
        
    tag = data['source']
    base_url = "https://medium.com/tag/"
    url = f"{base_url}{tag}/recommended"
    #max_links = random.randint(10,40)
    max_links = 100
    chrome_options = Options()
    #chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(45)
        driver.get(url)

        links = set()
        while len(links) < max_links:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            link_elements = soup.find_all('div', role='link')
            new_links = [link['data-href'] for link in link_elements if 'data-href' in link.attrs]
            #if(link['data-href']):
            #   print("link is present")
            links.update(new_links)

            # Scroll to the bottom to load more links
            driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
            time.sleep(random.uniform(1, 3))

            # Break the loop if no new links are found
            if not new_links:
                break

        return jsonify({"links": list(links)}), 200

    except WebDriverException as e:
        return jsonify({"error": "WebDriver error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Unexpected error occurred", "details": str(e)}), 500
    finally:
        if driver:
            driver.quit()

# Fetch Blog Details
@app.route('/fetch_blog', methods=['GET'])
def fetch_blog():
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find_all('h1')[0].text.strip() if soup.find_all('h1') else None
        content = soup.find('p', class_="pw-post-body-paragraph")
        image_tag = soup.find('picture')

        image_url = None
        if image_tag:
            source_tag = image_tag.find('source')
            if source_tag and 'srcset' in source_tag.attrs:
                image_url = source_tag['srcset'].split(',')[0].strip().split(' ')[0]
            else:
                img_tag = image_tag.find('img')
                image_url = img_tag['src'] if img_tag else None

        if not title or not content:
            return jsonify({"error": "Required elements not found"}), 404

        return jsonify({
            "title": title,
            "content": content.text.strip(),
            "image_url": image_url
        }), 200

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "Request failed", "details": str(e)}), 503
    except Exception as e:
        return jsonify({"error": "Unexpected error occurred", "details": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

