import os
import json
import math
import re
from bs4 import BeautifulSoup
from collections import defaultdict

PAGES_DIR = "pages"

STOPWORDS = {
    "the", "to", "and", "of", "is", "in", "for", "on", "with",
    "as", "by", "an", "at", "be", "this", "that", "it", "are",
    "from", "or", "was", "were", "has", "have"
}


documents = {}
doc_id = 0

for filename in os.listdir(PAGES_DIR):
    if filename.endswith(".html"):
        with open(os.path.join(PAGES_DIR, filename), "r", encoding="utf-8") as f:
            documents[f"doc{doc_id}"] = f.read()
            doc_id += 1
total_documents = len(documents)
print("Total documents:", total_documents)



def extract_text(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator=" ")


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    words = text.split()
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


term_frequencies = {}
document_frequency = defaultdict(int)

for doc_id, html in documents.items():
    text = extract_text(html)
    words = tokenize(text)

    tf = defaultdict(int)
    for word in words:
        tf[word] += 1

    term_frequencies[doc_id] = tf


    for word in tf.keys():
        document_frequency[word] += 1


inverted_index = defaultdict(list)
for doc_id, tf in term_frequencies.items():
    for word, freq in tf.items():
        # Ignore words appearing in all docs or only one doc
        if 1 < document_frequency[word] < total_documents:
            inverted_index[word].append((doc_id, freq))


with open("inverted_index.json", "w", encoding="utf-8") as f:
    json.dump(inverted_index, f, indent=4)



idf = {}
for word, doc_list in inverted_index.items():
    idf[word] = math.log(total_documents / len(doc_list))

with open("idf.json", "w", encoding="utf-8") as f:
    json.dump(idf, f, indent=4)

# -----------------------------
# Compute TF-IDF
# -----------------------------
tf_idf = defaultdict(dict)

for doc_id, tf in term_frequencies.items():
    for word, freq in tf.items():
        if word in idf:
            tf_idf[doc_id][word] = freq * idf[word]

with open("tf_idf.json", "w", encoding="utf-8") as f:
    json.dump(tf_idf, f, indent=4)

# -----------------------------
# Output summary
# -----------------------------
print("Number of documents indexed:", total_documents)
print("Number of unique terms:", len(inverted_index))

print("\nSample Inverted Index Entries:")
for word in list(inverted_index.keys())[:5]:
    print(word, "→", inverted_index[word])

print("\nSample IDF Values:")
for word in list(idf.keys())[:5]:
    print(word, "→", round(idf[word], 3))