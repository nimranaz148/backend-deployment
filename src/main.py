# src\main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.ingest import router as ingest_router
from src.api.chat import router as chat_router
from src.api.content import router as content_router
from src.api.auth import router as auth_router

app = FastAPI(title="Physical AI Textbook RAG Chatbot")

# CORS middleware for frontend integration - configured for mobile browser compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,
    allow_methods=["*"],  # Sab methods allow karein (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # <--- YEH HAI FIX (Sab headers allow karein)
    expose_headers=["Content-Type", "Content-Length"],
    max_age=86400,
)

app.include_router(ingest_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(content_router, prefix="/api")
app.include_router(auth_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Physical AI Textbook RAG Chatbot API"}
