from flask import Flask, render_template, request,url_for,Blueprint,jsonify
from flask_login import current_user,login_required
from apps.authentication.models import Dataset,Users
import kaggle
from bs4 import BeautifulSoup
import requests
from apps import db
import yfinance as yf
import matplotlib.pyplot as plt

bp = Blueprint('Dataset',__name__)
app = Flask(__name__)
# Mock dataset data (optional, you can remove this if you have real data)
datasets = [
    {'source_name': 'Source A (Nepal)', 'source_link': 'http://example.com/sourceA', 'file_format': 'CSV', 'author': 'Author A', 'description': 'Dataset A description about Nepal', 'updated': '2024-01-01', 'time_period': '2020-2022', 'area_covered': 'Nepal', 'topic': 'Engineering'},
    {'source_name': 'Source B (Not Nepal)', 'source_link': 'http://example.com/sourceB', 'file_format': 'JSON', 'author': 'Author B', 'description': 'Dataset B description (not about Nepal)', 'updated': '2023-01-01', 'time_period': '2018-2020', 'area_covered': 'Europe', 'topic': 'Humanities'},
]

def get_dataset_metadata(dataset_url):
    response = requests.get(dataset_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    metadata = {}

    # Extract metadata from the dataset page
    source_name_elem = soup.find(class_='ProfileHeader__displayName')
    metadata['source_name'] = source_name_elem.text.strip() if source_name_elem else None

    source_link_elem = soup.find('link', rel='canonical')
    metadata['source_link'] = source_link_elem.get('href') if source_link_elem else None

    author_elem = soup.find(class_='ProfileHeader__detailsItem--link')
    metadata['author'] = author_elem.text.strip() if author_elem else None

    return metadata

def search_kaggle_datasets(query):
    try:
        kaggle.api.authenticate()  # Authenticate if not already done
    except NameError:
        print("Kaggle API not authenticated. Please authenticate before searching.")
        return []

    search_results = kaggle.api.dataset_list(search=query)  # Use provided query for search

    datasets_with_metadata = []

    for dataset in search_results:
        # Search based on provided query, ignoring case for flexibility
        if query.lower() in dataset.title.lower():  # Modified comparison logic
            dataset_metadata = get_dataset_metadata(dataset.url)
            dataset_with_metadata = {
                "title": dataset.title,
                "metadata": dataset_metadata
            }
            datasets_with_metadata.append(dataset_with_metadata)

    return datasets_with_metadata


if __name__ == '__main__':
    app.run(debug=True)
