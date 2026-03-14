from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json
import re

app = FastAPI()

# Enable CORS (so HTML UI can call the API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load inverted index
with open("inverted_index.json", "r") as f:
    inverted_index = json.load(f)

# Load IDF values
with open("idf.json", "r") as f:
    idf = json.load(f)


# Tokenization
def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    tokens = text.split()
    return tokens


# Search using inverted index + TF-IDF
def search_documents(tokens):

    scores = {}

    for token in tokens:

        if token in inverted_index:

            postings = inverted_index[token]

            for doc, tf in postings:   

                score = tf * idf.get(token, 1)

                if doc not in scores:
                    scores[doc] = 0

                scores[doc] += score

    return scores


# Rank results
def rank_results(scores):

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    return ranked


# Search API
@app.get("/search")
def search(query: str):

    tokens = tokenize(query)

    scores = search_documents(tokens)

    ranked_results = rank_results(scores)

    return {
        "query": query,
        "tokens": tokens,
        "results": ranked_results[:5]
    }