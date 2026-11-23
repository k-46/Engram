# Engram

An AI-powered Engineering Knowledge Assistant built using Retrieval-Augmented Generation (RAG).

## Overview

Engram helps engineering teams retrieve technical knowledge from architecture decision records, design specifications, and incident reports.

It provides context-aware answers grounded in existing documents, with source citations for verification.

## Features

- Document ingestion and processing
- Semantic search
- AI-powered question answering
- Source citations
- Context-aware responses

## Tech Stack

- Python
- LLM API
- Embeddings API
- Vector Database
- Next.js / Streamlit


## Quick Start

From the `Engram` directory:

```powershell
py -3.13 -m pip install -r requirements.txt
Copy-Item .env.example .env
$env:PYTHONPATH = "src"
py -3.13 app.py
```

Set `OPENAI_API_KEY` in `.env` to enable LLM-generated answers. If no key or model is available, Engram uses a grounded extractive fallback.

## Workflow

1. Load and validate JSON documents with Pydantic schemas.
2. Clean and flatten document fields into readable text.
3. Split documents into overlapping chunks.
4. Embed chunks locally with `sentence-transformers`.
5. Persist embeddings and metadata in ChromaDB.
6. Embed a question and retrieve the most relevant chunks.
7. Generate a concise answer from retrieved context, or report insufficient context.

## Test

```powershell
$env:PYTHONPATH = "src"
py -3.13 -m pytest -q
```

