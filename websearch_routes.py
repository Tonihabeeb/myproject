from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from database import Database
from model_training import train_model
from file_routes import save_file_to_db, extract_text_from_pdf, extract_text_from_docx, extract_text_from_txt
import requests
import os
import urllib.parse
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

load_dotenv()

websearch_routes = Blueprint('websearch_routes', __name__)

google_search_url = 'https://www.googleapis.com/customsearch/v1'
duckduckgo_search_url = 'https://www.google.com/' #'https://duckduckgo.com/html/'
google_search_api_key = os.getenv('GOOGLE_API_KEY')
google_search_cx = os.getenv('GOOGLE_CX')

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

db = Database()

def download_file(url):
    response = requests.get(url)
    return response.content

def google_search(query, api_key, cx, **kwargs):
    params = {'q': query, 'key': api_key, 'cx': cx}
    params.update(kwargs)
    response = requests.get(google_search_url, params=params)
    return response.json()

def duckduckgo_search(query):
    driver = webdriver.Chrome(service=ChromeService(executable_path=ChromeDriverManager().install()))
    driver.get(duckduckgo_search_url + '?q=' + urllib.parse.quote_plus(query))
    return driver.page_source

#def duckduckgo_search(query):
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=ChromeService(executable_path=os.getenv('CHROMEDRIVER_PATH')), options=options)
    driver.get(duckduckgo_search_url + '?q=' + urllib.parse.quote_plus(query))
    return driver.page_source



def extract_links_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = [a['href'] for a in soup.find_all('a', href=True)]
    return links

@websearch_routes.route('/websearch', methods=['POST'])
@jwt_required()
def web_search():
    current_user = get_jwt_identity()
    task_id = request.json.get('task_id')
    keywords = request.json.get('keywords')
    location = request.json.get('location')

    if not task_id or not keywords or not location: 
        return jsonify({'error': 'Missing task_id, keywords or location'}), 400  

    google_results = google_search(keywords, google_search_api_key, google_search_cx, location=location)
    google_urls = [item['link'] for item in google_results.get('items', [])]

    duckduckgo_html_content = duckduckgo_search(keywords)
    duckduckgo_urls = extract_links_from_html(duckduckgo_html_content)

    urls = sorted(google_urls + duckduckgo_urls, key=lambda x: keywords in urllib.parse.unquote(x), reverse=True)[:10]
    scraped_texts = []
    downloaded_files = []

    driver = webdriver.Chrome(service=ChromeService(executable_path=ChromeDriverManager().install()))
    for url in urls:
        if any(url.endswith(extension) for extension in ALLOWED_EXTENSIONS):
            try:
                file_content = download_file(url)
                file_id = save_file_to_db(file_content, url.split('/')[-1])
                if url.endswith('.pdf'):
                    text = extract_text_from_pdf(file_content)
                elif url.endswith('.docx'):
                    text = extract_text_from_docx(file_content)
                elif url.endswith('.txt'):
                    text = extract_text_from_txt(file_content)
                downloaded_files.append({'file_id': file_id, 'text': text})
            except Exception as e:
                print(f"Error while downloading file from {url}: {e}")
            
            def scrape_data(url):
                driver = webdriver.Chrome(service=ChromeService(executable_path=os.getenv('CHROMEDRIVER_PATH')))
                driver.get(url)
                return driver.page_source
        else:
            try:
                driver.get(url)
                scraped_texts.append(driver.page_source)
            except Exception as e:
                print(f"Error while scraping {url}: {e}")

    driver.quit()

    db.insert_many('ScrapedData', [{'text': text, 'user_id': current_user, 'task_id': task_id} for text in scraped_texts])
    db.insert_many('DownloadedFiles', downloaded_files)

    return jsonify({'message': 'Data has been successfully scraped and downloaded.'}), 200
