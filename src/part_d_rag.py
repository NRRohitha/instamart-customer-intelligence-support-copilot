import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import mock_llm
from src.config import CHUNK_OVERLAP, CHUNK_WORDS, DATA_POLICIES, DATA_RAW

SYSTEM_PROMPT = (
    "You are a POLICY ASSISTANT. Answer the question using only the supplied "
    "policy context. If the context does not contain the answer, say that you "
    "could not find the information in the policy documents."
)


class PolicyRAG:
    def __init__(self, chunk_words=CHUNK_WORDS, overlap=CHUNK_OVERLAP):
        self.chunk_words = chunk_words
        self.overlap = overlap
        self.chunks = []
        for path in sorted(DATA_POLICIES.glob("*.txt")):
            words = path.read_text(encoding="utf-8").split()
            step = chunk_words - overlap
            start = 0
            while start < len(words):
                text = " ".join(words[start : start + chunk_words])
                self.chunks.append({"source": path.name, "text": text})
                if start + chunk_words >= len(words):
                    break
                start += step
        self.vectorizer = TfidfVectorizer()
        self.matrix = self.vectorizer.fit_transform(
            [chunk["text"] for chunk in self.chunks]
        )

    def retrieve(self, query, k=3):
        query_vector = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        order = np.argsort(-scores)[:k]
        return [
            {
                "source": self.chunks[index]["source"],
                "score": float(scores[index]),
                "text": self.chunks[index]["text"],
            }
            for index in order
        ]

    def answer(self, question):
        results = self.retrieve(question, k=3)
        context_lines = ["CONTEXT:"]
        for result in results:
            context_lines.append(f"[{result['source']}]")
            context_lines.append(result["text"])
        context_lines.extend(["QUESTION:", question])
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(context_lines)},
        ]
        response = mock_llm.chat(messages)
        return response.choices[0].message.content, [r["source"] for r in results]


_DEFAULT = PolicyRAG()


def retrieve(query, k=3):
    return _DEFAULT.retrieve(query, k)


def answer(question):
    return _DEFAULT.answer(question)


def evaluate(rag, label):
    questions = pd.read_csv(DATA_RAW / "policy_eval.csv", keep_default_na=False)
    doc_hits = 0
    fact_hits = 0
    fallbacks = 0
    answerable = 0
    document_rows = []
    for row in questions.itertuples(index=False):
        results = rag.retrieve(row.question, k=3)
        sources = [result["source"] for result in results]
        response_text, _ = rag.answer(row.question)
        if row.expected_doc == "NONE":
            ok = response_text.startswith("I could not find")
            fallbacks += int(ok)
            document_rows.append((row.question, "unanswerable", ok, response_text[:80]))
            continue
        answerable += 1
        doc_ok = row.expected_doc in sources
        fact_ok = row.expected_fact in response_text
        doc_hits += int(doc_ok)
        fact_hits += int(fact_ok)
        document_rows.append(
            (
                row.question,
                row.expected_doc,
                doc_ok and fact_ok,
                response_text[:80],
            )
        )
    print(f"\n=== {label} ===")
    print(f"chunks: {len(rag.chunks)}")
    print(f"expected doc in top 3: {doc_hits}/{answerable}")
    print(f"expected fact in answer: {fact_hits}/{answerable}")
    print(f"fallback for unanswerable: {fallbacks}/2")
    failures = [row for row in document_rows if not row[2]]
    for failure in failures:
        print(f"FAIL: {failure}")
    return doc_hits, fact_hits, fallbacks, failures


def main():
    chunks_by_source = pd.Series(
        [chunk["source"] for chunk in _DEFAULT.chunks]
    ).value_counts()
    print("=== chunk counts ===")
    print(chunks_by_source.to_string())
    print(f"total: {len(_DEFAULT.chunks)}")
    print("=== retrieval for 'refund policy late delivery' ===")
    for result in retrieve("refund policy late delivery", k=3):
        print(f"{result['source']} {result['score']:.3f} | {result['text'][:100]}")

    evaluate(_DEFAULT, "overlap 10")
    zero_overlap = PolicyRAG(overlap=0)
    evaluate(zero_overlap, "overlap 0")


if __name__ == "__main__":
    main()
