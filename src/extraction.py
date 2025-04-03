import tkinter as tk
from tkinter import filedialog
from collections import defaultdict, Counter
import fitz
import re
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import scraping
import os
from db_handler import DatabaseHandler

# ----------------------- File Upload GUI -----------------------
class FileUploadApp:
    def __init__(self, root):
        self.root = root
        root.title("File Upload - Study Material")
        root.geometry("450x350")  # Set window size

        # Subject Name Entry
        self.subject_label = tk.Label(root, text="Enter Subject Name:", font=("Arial", 12))
        self.subject_label.pack(pady=5)

        self.subject_entry = tk.Entry(root, font=("Arial", 12), width=30)
        self.subject_entry.pack(pady=5)

        # File Upload Buttons
        self.file_paths = {"PYQ": "", "CDP": "", "Notes": ""}

        self.upload_buttons = {
            "PYQ": tk.Button(root, text="Upload Your PYQ", font=("Arial", 12), width=25, height=2,
                             command=lambda: self.upload_file("PYQ")),
            "CDP": tk.Button(root, text="Upload the CDP", font=("Arial", 12), width=25, height=2,
                             command=lambda: self.upload_file("CDP")),
            "Notes": tk.Button(root, text="Upload the Notes", font=("Arial", 12), width=25, height=2,
                               command=lambda: self.upload_file("Notes"))
        }

        for btn in self.upload_buttons.values():
            btn.pack(pady=5)  # Add spacing between buttons

        # Submit Button
        self.submit_btn = tk.Button(root, text="Submit", font=("Arial", 12, "bold"), width=25, height=2,
                                    bg="green", fg="white", command=self.process_files)
        self.submit_btn.pack(pady=10)

    def upload_file(self, file_type):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.file_paths[file_type] = file_path
            print(f"{file_type} File selected: {file_path}")

    def process_files(self):
        # Get subject name and check if it exists in the database
        subject_name = self.subject_entry.get().strip()
        if not subject_name:
            print("Please enter a subject name!")
            return

        db = DatabaseHandler()
        if db.subject_exists(subject_name):
            print(f"Subject '{subject_name}' already exists in the database. Fetching existing data...\n")
            topics = db.fetch_topics(subject_name)
            if topics:
                print(f"Topics for subject '{subject_name}':")
                for topic, file_name in topics:
                    print(f" - {topic}: {file_name}")
            else:
                print("No topics found for this subject yet.")
            # Write subject name to a temporary file for scraping module and close the GUI
            with open("subject.txt", "w") as f:
                f.write(subject_name)
            self.root.destroy()
            return

        cdp_pdf_path = self.file_paths["CDP"]
        pyq_pdf_path = self.file_paths["PYQ"]
        notes_pdf_path = self.file_paths["Notes"]

        if not all([cdp_pdf_path, pyq_pdf_path, notes_pdf_path]):
            print("\n!!! Please upload all required files!")
            return

        # Close the GUI
        self.root.destroy()

        # Insert the new subject data into the database
        db.insert_subject(subject_name, cdp_pdf_path, pyq_pdf_path, notes_pdf_path)

        # Process the PDFs
        cdp_topics = extract_topics_from_pdf(cdp_pdf_path)
        pyq_topics = extract_topics_from_pdf(pyq_pdf_path)
        notes_text = extract_text_from_pdf(notes_pdf_path)

        # Create Adjacency List and Topic Importance
        adjacency_list, importance_score = create_adjacency_list(cdp_topics, notes_text, pyq_topics)

        # Apply PageRank for final topic order
        ranked_topics = rank_topics_with_pagerank(adjacency_list)

        # Print Results
        print("\n*Final Study Order (Based on PageRank)*")
        for i, (topic, score) in enumerate(ranked_topics, 1):
            print(f"{i}. {topic} (Score: {score:.4f})")

        print("\n*Most Important Topics (Based on TF-IDF, PYQs & Mentions)*")
        for topic, count in sorted(importance_score.items(), key=lambda x: x[1], reverse=True):
            print(f"{topic}: {count:.2f} importance score")

        print("\n*Adjacency List (Topic Dependencies)*")
        for topic, related in adjacency_list.items():
            print(f"{topic}: {related}")

        # Save study order to JSON
        save_study_order_to_json(ranked_topics)

        # NOTE: We no longer insert extracted topics here.
        # Instead, scraping.py will process the top 10 topics and store scraped PDFs.

        # Write the subject name to a temporary file for scraping.py
        with open("subject.txt", "w") as f:
            f.write(subject_name)

        # Visualizations
        visualize_graph(adjacency_list)
        visualize_topic_importance(importance_score)

        scraping.scrap()

# ----------------------- PDF Processing -----------------------
def extract_text_from_pdf(pdf_path):
    """Extracts text from a given PDF file."""
    doc = fitz.open(pdf_path)
    full_text = " ".join(page.get_text("text") for page in doc)
    return full_text.lower()

def extract_topics_from_pdf(pdf_path):
    """Extracts topics from CDP or PYQ PDF."""
    text = extract_text_from_pdf(pdf_path)
    topics = re.split(r"[,.()\n]", text)
    cleaned_topics = [topic.strip().lower() for topic in topics if topic.strip()]
    return list(set(cleaned_topics))  # Remove duplicates

# ----------------------- TF-IDF Calculation -----------------------
def calculate_tfidf(notes_text, topics):
    """Calculates TF-IDF scores for topics in the notes."""
    vectorizer = TfidfVectorizer(vocabulary=topics)
    tfidf_matrix = vectorizer.fit_transform([notes_text])
    scores = dict(zip(vectorizer.get_feature_names_out(), tfidf_matrix.toarray()[0]))
    return scores

# ----------------------- Topic Matching -----------------------
def match_topics(cdp_topics, pyq_topics):
    """Matches topics between CDP and PYQs and assigns weights."""
    topic_weight = Counter()
    for topic in cdp_topics:
        if topic in pyq_topics:
            topic_weight[topic] += 10  # High priority if found in PYQ
    return topic_weight

# ----------------------- Adjacency List & Ranking -----------------------
def create_adjacency_list(cdp_topics, notes_text, pyq_topics):
    """Creates topic dependencies & calculates importance scores."""
    adjacency_list = defaultdict(list)
    topic_mention_count = Counter()

    pyq_weights = match_topics(cdp_topics, pyq_topics)
    tfidf_scores = calculate_tfidf(notes_text, cdp_topics)

    for topic in cdp_topics:
        topic_pattern = r"\b" + re.escape(topic) + r"\b"
        count = len(re.findall(topic_pattern, notes_text))

        topic_mention_count[topic] = (
                count * 1.5 +
                pyq_weights.get(topic, 0) +
                tfidf_scores.get(topic, 0) * 5
        )

        for other_topic in cdp_topics:
            if topic != other_topic and re.search(r"\b" + re.escape(other_topic) + r"\b", notes_text):
                adjacency_list[topic].append(other_topic)

    return dict(adjacency_list), topic_mention_count

# ----------------------- PageRank for Study Order -----------------------
def rank_topics_with_pagerank(adjacency_list):
    """Applies PageRank to determine topic importance."""
    G = nx.DiGraph()

    for topic, related_topics in adjacency_list.items():
        for related_topic in related_topics:
            G.add_edge(topic, related_topic)

    page_rank_scores = nx.pagerank(G, alpha=0.85)
    return sorted(page_rank_scores.items(), key=lambda x: x[1], reverse=True)

# ----------------------- Visualization -----------------------
def visualize_graph(adjacency_list):
    """Visualizes the topic dependency graph."""
    G = nx.DiGraph()
    for topic, related_topics in adjacency_list.items():
        for related_topic in related_topics:
            G.add_edge(topic, related_topic)

    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)
    nx.draw(G, pos, with_labels=True, node_size=2000, node_color="lightblue", edge_color="gray", font_size=10)
    plt.title("Topic Dependency Graph")
    plt.show()

def visualize_topic_importance(importance_score):
    """Plots the top 10 most important topics."""
    sorted_topics = sorted(importance_score.items(), key=lambda x: x[1], reverse=True)[:10]
    topics, counts = zip(*sorted_topics) if sorted_topics else ([], [])

    plt.figure(figsize=(12, 6))
    sns.barplot(x=list(counts), y=list(topics), palette="viridis")
    plt.xlabel("Importance Score")
    plt.ylabel("Topics")
    plt.title("Top 10 Most Important Topics")
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.show()

def save_study_order_to_json(ranked_topics):
    """Saves the final study order to a JSON file with a proper structure."""
    study_order = {
        "study_order": [{"topic": topic, "score": score} for topic, score in ranked_topics]
    }
    with open("study_order.json", "w") as json_file:
        json.dump(study_order, json_file, indent=4)

def extract():
    root = tk.Tk()
    app = FileUploadApp(root)
    root.mainloop()

if __name__ == "__main__":
    extract()
