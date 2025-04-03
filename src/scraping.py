import os
import requests
import cleaning
from bs4 import BeautifulSoup
import time
import random
import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
from fpdf import FPDF
import json
import unicodedata

from db_handler import DatabaseHandler

def scrape_data(topics):
    results = []
    for topic in topics:
        try:
            formatted_topic = topic.replace(' ', '_')
            url = f"https://en.wikipedia.org/wiki/{formatted_topic}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                content_div = soup.find('div', {'id': 'mw-content-text'})
                if content_div:
                    paragraphs = content_div.find_all('p')
                    text_content = " ".join([p.get_text() for p in paragraphs])
                    # Remove citation references like [1], [23], etc.
                    text_content = re.sub(r'\[\d+\]', '', text_content)
                    summarized_content = summarize_text(text_content)
                    results.append({
                        'topic': topic,
                        'content': summarized_content,
                        'url': url
                    })
                    print(f"Successfully scraped and summarized: {topic}")
                else:
                    print(f"Could not find content for: {topic}")
                    results.append({'topic': topic, 'content': "No content found", 'url': url})
            else:
                print(f"Failed to retrieve page for: {topic}. Status code: {response.status_code}")
                results.append({'topic': topic, 'content': f"Failed to retrieve. Status code: {response.status_code}", 'url': url})
            time.sleep(random.uniform(1, 3))
        except Exception as e:
            print(f"Error scraping {topic}: {str(e)}")
            results.append({'topic': topic, 'content': f"Error: {str(e)}", 'url': url if 'url' in locals() else None})
    return results

def summarize_text(text, num_sentences=5):
    sentences = sent_tokenize(text)
    if len(sentences) <= num_sentences:
        return text
    words = word_tokenize(text.lower())
    word_frequencies = Counter(words)
    sentence_scores = {
        sentence: sum(word_frequencies[word] for word in word_tokenize(sentence.lower()) if word in word_frequencies)
        for sentence in sentences}
    summarized_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    return " ".join(summarized_sentences)

def fetch_top_youtube_videos(topic):
    YOUTUBE_API_KEY = os.getenv('YOUTUBE_API')
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": topic,
        "maxResults": 5,
        "type": "video",
        "key": YOUTUBE_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        video_results = []
        for item in data.get("items", []):
            title = item["snippet"]["title"]
            video_id = item["id"]["videoId"]
            link = f"https://www.youtube.com/watch?v={video_id}"
            video_results.append((title, link))
        return video_results
    else:
        print(f"Failed to fetch YouTube videos: {response.status_code}")
        return []

def remove_unicode(text):
    # Normalize Unicode characters to ASCII-compatible form
    return ''.join(c if ord(c) < 128 else unicodedata.normalize('NFKD', c).encode('ASCII', 'ignore').decode() for c in text)

def save_to_pdf(topic, content, youtube_videos):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Normalize text to remove Unicode issues
    topic = remove_unicode(topic)
    content = remove_unicode(content)
    youtube_videos = [(remove_unicode(title), remove_unicode(link)) for title, link in youtube_videos]
    # Title
    pdf.set_font("Arial", style='', size=16)
    pdf.cell(200, 10, topic, ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, content)
    pdf.ln(10)
    pdf.set_font("Arial", style='', size=14)
    pdf.cell(0, 10, "Top YouTube Videos:", ln=True)
    pdf.set_font("Arial", size=12)
    for title, link in youtube_videos:
        pdf.multi_cell(0, 10, f"{title}\n{link}\n")
        pdf.ln(10)
    # Save PDF in records folder
    if not os.path.exists("records"):
        os.makedirs("records")
    file_name = f"records/{topic.replace(' ', '_')}.pdf"
    pdf.output(file_name, "F")
    print(f"Saved: {file_name}")
    return file_name  # Return PDF file path for DB insertion

def extract_topics_from_json(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        if "study_order" in data and isinstance(data["study_order"], list):
            return [entry["topic"] for entry in data["study_order"] if "topic" in entry]
        else:
            raise ValueError("JSON file format is incorrect.")
    except (json.JSONDecodeError, FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return []

def scrap():
    # Read subject name from temporary file generated by extraction.py
    if os.path.exists("subject.txt"):
        with open("subject.txt", "r") as f:
            subject_name = f.read().strip()
    else:
        subject_name = "unknown_subject"
    topics = extract_topics_from_json("study_order.json")
    topics = cleaning.clean_list(topics)
    topics = sorted(topics[:10])
    scraped_data = scrape_data(topics)

    db = DatabaseHandler()  # Initialize DB handler
    for data in scraped_data:
        youtube_videos = fetch_top_youtube_videos(data['topic'])
        pdf_path = save_to_pdf(data['topic'], data['content'], youtube_videos)
        # Insert scraped data into the subject-specific table (with two columns: topic_name and file_name)
        db.insert_scraped_topic(subject_name, data['topic'], pdf_path)
    print("\nAll topics have been saved.")

if __name__ == "__main__":
    scrap()
