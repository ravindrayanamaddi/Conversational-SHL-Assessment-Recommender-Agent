# Conversational-SHL-Assessment-Recommender-Agent

AI-powered conversational recommendation system for SHL assessments using FastAPI, FAISS semantic search, sentence-transformer embeddings, and Groq LLM.

---

## Project Overview

This project implements a stateless conversational AI agent that recommends SHL assessments based on hiring requirements, job descriptions, candidate profiles, and conversational refinements.

The system uses:

- FastAPI for REST API endpoints
- FAISS for vector similarity search
- Sentence Transformers for semantic embeddings
- Groq LLM for conversational reasoning
- SHL assessment catalog as grounded recommendation source

---

## Features

- Clarifies vague hiring queries
- Recommends 1–10 SHL assessments
- Supports conversational refinement
- Compares assessments using catalog-grounded data
- Refuses out-of-scope requests
- Stateless conversation handling
- Semantic retrieval with FAISS vector search
- FastAPI production-ready API

---

## Tech Stack

- Python
- FastAPI
- FAISS
- Sentence Transformers
- Groq API
- Pydantic
- Uvicorn

---

## Project Structure

```text
.
├── app/
│   ├── main.py
│   ├── agent.py
│   ├── retriever.py
│   ├── catalog.py
│   ├── schemas.py
│   └── config.py
│
├── data/
│   ├── catalog.json
│   └── faiss_index.pkl
│
├── requirements.txt
├── README.md
└── .env
```

---

## Installation

Clone repository:

```bash
git clone https://github.com/ravindrayanamaddi/Conversational-SHL-Assessment-Recommender-Agent.git

cd Conversational-SHL-Assessment-Recommender-Agent
```

Create virtual environment:

```bash
python -m venv venv
```

Activate environment:

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create `.env` file:

```env
GROQ_API_KEY=your_groq_api_key
```

---

## Run Locally

Start FastAPI server:

```bash
uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

---

### Chat Endpoint

```http
POST /chat
```

Request:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hiring a Java developer who works with stakeholders"
    },
    {
      "role": "assistant",
      "content": "Sure. What is seniority level?"
    },
    {
      "role": "user",
      "content": "Mid-level, around 4 years"
    }
  ]
}
```

Response:

```json
{
  "reply": "Got it. Here are assessments that fit your requirements.",
  "recommendations": [
    {
      "name": "Core Java (Advanced Level) (New)",
      "url": "https://www.shl.com/...",
      "test_type": "K"
    }
  ],
  "end_of_conversation": false
}
```

---

## Supported Behaviors

### Clarification

Input:

```text
I need an assessment
```

Behavior:
- asks follow-up question
- no recommendations returned

---

### Recommendation

Input:

```text
Hiring a Java developer
```

Behavior:
- recommends relevant SHL assessments

---

### Refinement

Input:

```text
Actually add personality tests too
```

Behavior:
- updates recommendations
- includes OPQ/personality assessments

---

### Comparison

Input:

```text
What is the difference between OPQ and GSA?
```

Behavior:
- grounded comparison using SHL catalog

---

### Refusal

Input:

```text
Give legal hiring advice
```

Behavior:
- refuses out-of-scope request

---

## Deployment

Deployed using Render.

Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

---

## Author

Ravindra Yanamaddi

GitHub:
https://github.com/ravindrayanamaddi