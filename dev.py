from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import requests
import time
import random
from flask import Flask, jsonify,request
from flask_cors import CORS
app = Flask(__name__)
CORS(app)


# Fetch Links from Dev.to
@app.route('/fetch_links', methods=['POST'])
def fetch_links():
    data = request.get_json()
    if not data or 'source' not in data:
        return jsonify({"error": "Missing 'source' parameter"}), 400

    tag = data['source']
    base_url = f"https://dev.to/t/{tag}/"  # Dev.to tags URL
    max_links = 20

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    service = Service("/usr/bin/chromedriver")

    driver = None
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(15)
        driver.get(base_url)

        links = set()
        while len(links) < max_links:
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            link_elements = soup.find_all('a', class_='crayons-story__hidden-navigation-link')
            new_links = [link['href'] for link in link_elements if 'href' in link.attrs]
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


# Fetch Blog Details from Dev.to
@app.route('/fetch_blog', methods=['GET'])
def fetch_blog():
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "Missing URL parameter"}), 400

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.find('h1', class_=" fs-3xl m:fs-4xl l:fs-5xl fw-bold s:fw-heavy lh-tight mb-2 longer").text.strip() if soup.find('h1', class_=" fs-3xl m:fs-4xl l:fs-5xl fw-bold s:fw-heavy lh-tight mb-2 longer") else None
        content = soup.find('div', class_="crayons-article__body text-styles spec__body")  # Main content
        image_tag = soup.find('img', class_='crayons-article__cover__image')

        image_url = None
        if image_tag and 'src' in image_tag.attrs:
            image_url = image_tag['src']

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
