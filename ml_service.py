from fastapi import FastAPI, UploadFile, File
import fitz  # PyMuPDF
import nltk
from nltk.tokenize import sent_tokenize
import numpy as np
import faiss
import wikipedia
from sentence_transformers import SentenceTransformer

app = FastAPI()

# =========================
# GLOBAL VARIABLES
# =========================
model = None
index = None
system_loaded = False


# =========================
# 🔥 LOAD SYSTEM (LAZY LOAD)
# =========================
def load_system():
    global model, index

    print("🚀 Loading model...")

    # Load SBERT model
    model = SentenceTransformer("all-MiniLM-L6-v2")

    print("🌐 Fetching Wikipedia data...")

    def fetch_wiki(query):
        try:
            return wikipedia.page(query).content
        except Exception as e:
            print(f"Wiki error ({query}):", e)
            return ""

    # Corpus
    corpus_texts = [
        fetch_wiki("artificial intelligence"),
        fetch_wiki("machine learning"),
        fetch_wiki("natural language processing"),
        fetch_wiki("project management"),
        fetch_wiki("software engineering"),
    ]

    # Remove empty texts
    corpus_texts = [c for c in corpus_texts if len(c) > 100]

    print("🧠 Creating embeddings...")

    # Convert to embeddings
    corpus_embeddings = model.encode(corpus_texts, convert_to_numpy=True)

    # Build FAISS index
    dimension = corpus_embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(corpus_embeddings)

    print("✅ System ready!")


# =========================
# 🔎 SIMILARITY FUNCTION
# =========================
def get_similarity(sentence):
    emb = model.encode([sentence], convert_to_numpy=True)
    dist, _ = index.search(emb, 1)

    score = 1 / (1 + dist[0][0])
    return float(score)


# =========================
# 🏠 HOME
# =========================
@app.get("/")
def home():
    return {"message": "Plagiarism Detection API Running 🚀"}


# =========================
# 📄 UPLOAD API
# =========================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global system_loaded

    # 🔥 Load system only once
    if not system_loaded:
        print("⚡ First request → loading system...")
        load_system()
        system_loaded = True

    try:
        # Step 1: Read PDF
        pdf = fitz.open(stream=file.file.read(), filetype="pdf")

        text = ""
        for page in pdf:
            text += page.get_text()

        # Step 2: Sentence split
        sentences = sent_tokenize(text)
        sentences = [s for s in sentences if len(s) > 30]

        # Step 3: Similarity check
        results = []

        for sent in sentences:
            score = get_similarity(sent)

            results.append({
                "sentence": sent,
                "similarity": score
            })

        # Step 4: Plagiarism calculation
        THRESHOLD = 0.75

        plag_count = sum(1 for r in results if r["similarity"] > THRESHOLD)
        plag_percent = (plag_count / len(results)) * 100 if results else 0

        # Step 5: Response
        return {
            "total_sentences": len(results),
            "plagiarized_sentences": plag_count,
            "plagiarism_percentage": plag_percent,
            "sample_results": results[:5]
        }

    except Exception as e:
        print("❌ ERROR:", e)
        return {"error": str(e)}