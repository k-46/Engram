import os
from typing import Iterable

from src.retrieval.retriever import RetrievedChunk


SYSTEM_PROMPT = """You are Engram, an engineering knowledge assistant.
Answer only from the supplied context. If the context is insufficient, say so.
Be concise: answer in at most 2 short paragraphs or 3 short bullets.
Write like a helpful engineering colleague, not a raw database report.
Do not include unrelated documents or combine multiple interpretations.
Cite exact supporting sources at the end using [Document ID: title].
Use natural sentences. Do not invent facts."""


class Generator:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = os.getenv("OPENAI_BASE_URL")
        self._client = None
        if self.api_key:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            except Exception:
                self._client = None

    def generate(self, question: str, chunks: Iterable[RetrievedChunk]) -> str:
        chunks = list(chunks)
        if not chunks:
            return "I could not find enough relevant information in the engineering documents to answer that reliably."

        context = "\n\n".join(
            f"[Source {chunk.document_id}: {chunk.metadata.get('title', 'Untitled')}]\n{chunk.text}"
            for chunk in chunks
        )
        if not self.api_key:
            return self._extractive_answer(question, chunks)

        try:
            from openai import OpenAI
            if self._client is None:
                self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"},
                ],
                temperature=0,
                max_tokens=300,
            )
            return response.choices[0].message.content or "I could not find enough relevant context to answer reliably."
        except Exception as exc:
            return f"I could not complete the answer because the language service failed: {exc}"

    def _extractive_answer(
        self, question: str, chunks: list[RetrievedChunk]
    ) -> str:
        terms = {
            term.lower()
            for term in question.replace("?", "").split()
            if len(term) > 2
        }
        synonym_terms = {
            "database": ("postgresql", "database", "transactional"),
            "operational": ("postgresql", "incident", "operational"),
            "redis": ("redis", "stream", "cloudqueue"),
            "authorization": ("authorization", "gatekeeper", "policy"),
            "webhook": ("webhook", "redis", "cloudqueue"),
            "incident": ("incident", "root cause", "resolution"),
        }
        evidence_terms = set(terms)
        for term in terms:
            evidence_terms.update(synonym_terms.get(term, ()))
        selected: list[tuple[RetrievedChunk, str]] = []
        for chunk in chunks[:3]:
            sentences = [
                sentence.strip()
                for sentence in chunk.text.replace("\n", " ").split(".")
                if sentence.strip()
            ]
            ranked = sorted(
                sentences,
                key=lambda sentence: sum(
                    evidence_term in sentence.lower()
                    for evidence_term in evidence_terms
                ),
                reverse=True,
            )
            if ranked:
                sentence = ranked[0].rstrip(" .")
                if sentence.startswith("This document is about "):
                    continue
                selected.append((chunk, sentence))

        if not selected:
            return "I found some related text, but not enough clear evidence to give a reliable answer."

        answer_lines = []
        for chunk, sentence in selected:
            title = str(chunk.metadata.get("title", "Untitled"))
            answer_lines.append(
                f"- According to {chunk.document_id} ({title}), "
                f"{sentence[:1].lower() + sentence[1:]}."
            )
        return "\n".join(answer_lines)
