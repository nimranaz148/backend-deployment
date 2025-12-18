# src/services/agent_service.py

import json
from typing import List, Dict, Optional
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
from src.services.embedding_service import EmbeddingService
from src.services.vector_store_service import VectorStoreService
from src.core.config import settings

set_tracing_disabled(True)

# --- NAVIGATION CONSTANTS ---
COURSE_NAVIGATION = {
    "intro": {"path": "/docs", "title": "Introduction"},
    "week 1": {"path": "/docs/module1/week1-intro-physical-ai", "title": "Week 1: Intro"},
    "module 1": {"path": "/docs/module1/week1-intro-physical-ai", "title": "Module 1"},
}

@function_tool
def navigate_to_page(destination: str, section: str = "") -> str:
    return json.dumps({"action": "redirect", "path": "/docs", "message": f"Navigating to {destination}"})

@function_tool
def list_available_pages() -> str:
    return json.dumps({"pages": [{"title": "Home", "path": "/docs"}]})

class TextbookAgent:
    def __init__(self):
        # OpenAI Setup
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY
        )
        
        # Using OpenAI GPT-4o-mini
        self.model = OpenAIChatCompletionsModel(
            model="gpt-4o-mini", 
            openai_client=self.client
        )
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()
    
    def _search_textbook(self, query: str) -> str:
        try:
            embedding = self.embedding_service.get_embedding(query)
            results = self.vector_store_service.search_vectors(embedding, limit=5)
            if not results: return "No relevant content found."
            
            context = "TEXTBOOK CONTENT:\n\n"
            for res in results:
                context += f"---\n{res['text']}\n"
            return context
        except Exception as e:
            print(f"Search Error: {e}")
            return ""

    async def chat_stream(self, user_message: str, history: List[Dict], selected_text: Optional[str] = None, user_id: str = None, current_page: str = None):
        context = self._search_textbook(user_message)
        
        system_prompt = f"""You are an expert AI Robotics tutor.
        Use the following textbook content to answer the student's question accurately.
        
        {context}
        
        Answer concisely and helpfully.
        """
        
        agent = Agent(name="Tutor", instructions=system_prompt, model=self.model)
        
        try:
            result = await Runner.run(agent, input=user_message)
            yield result.final_output
        except Exception as e:
            yield f"I encountered an error: {str(e)}"

# Singleton instance
textbook_agent = TextbookAgent()