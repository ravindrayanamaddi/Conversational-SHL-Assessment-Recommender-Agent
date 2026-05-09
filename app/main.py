from fastapi import FastAPI
from app.schemas import ChatRequest, ChatResponse
from app.agent import agent

app = FastAPI(title="Conversational SHL Assessment Recommender Agent")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    reply, recommendations, end_of_conversation = agent.generate_reply(
        [m.model_dump() for m in request.messages]
    )

    return {
        "reply": reply,
        "recommendations": recommendations,
        "end_of_conversation": end_of_conversation
    }