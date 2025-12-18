# src\services\chat_service.py
from typing import List, Dict, AsyncGenerator, Optional
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from src.services.embedding_service import EmbeddingService
from src.services.vector_store_service import VectorStoreService
from src.services.db_service import db_service
from src.core.config import settings

class ChatService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()
        self.chat_model = "gpt-4o-mini" 
        
    async def chat_stream(self, user_message: str, history: List[Dict[str, str]], selected_text: Optional[str] = None) -> AsyncGenerator[str, None]:
        # 1. Create a vector from the user message (include selected text if provided)
        search_query = user_message
        if selected_text:
            search_query = f"{user_message} {selected_text[:500]}"  # Limit selected text for embedding
        user_embedding = self.embedding_service.get_embedding(search_query)

        # 2. Search for relevant context chunks from Qdrant
        search_results = self.vector_store_service.search_vectors(user_embedding, limit=5)

        context_messages = ""
        source_documents_for_logging = [] # Collect source documents for logging
        if search_results:
            context_messages = "\n\nRelevant Context from Textbook:\n"
            for i, result in enumerate(search_results):
                context_messages += f"--- Document: {result['source_file']} (Score: {result['score']:.2f}) ---\n"
                context_messages += f"{result['text']}\n\n"
                source_documents_for_logging.append({
                    "source_file": result["source_file"],
                    "score": result["score"],
                    "text_snippet": result["text"][:200] # Log a snippet for brevity
                })
        else:
            yield "No relevant documents found in the textbook. Providing a general answer.\n\n"
            # FR-015: If no documents found, provide disclaimer

        # 3. Construct a prompt for the OpenAI API with user message, history, and context
        system_prompt = """You are a helpful assistant for a Physical AI & Humanoid Robotics textbook. 
Answer questions based on the provided context. If the context does not contain enough information, 
use your general knowledge, but clearly state when you are doing so. Keep responses concise and to the point.
You are an expert in ROS 2, Gazebo, NVIDIA Isaac, and robotics in general."""

        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
        ]

        # Add historical messages
        for turn in history:
            messages.append({"role": "user", "content": turn["user_message"]})
            messages.append({"role": "assistant", "content": turn["ai_response"]})

        # Build user message with selected text if provided
        user_content = context_messages
        if selected_text:
            user_content += f"\n\nUser Selected Text (prioritize this context):\n{selected_text}\n"
        user_content += f"\n\nUser Question: {user_message}"
        
        messages.append({"role": "user", "content": user_content})

        # 4. Call the OpenAI API to get a streaming response
        full_response_content = []
        try:
            stream = self.openai_client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                stream=True,
                temperature=0.7, # Adjust as needed
            )

            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response_content.append(content)
                    yield content
            
            # After streaming, log the interaction
            db_service.log_chat_interaction(
                user_message=user_message,
                ai_response="".join(full_response_content),
                source_documents=source_documents_for_logging
            )
        except Exception as e:
            error_message = f"An error occurred during streaming: {e}"
            print(error_message) # Log to console
            yield f"\n\n**Error:** {error_message}. Please try again later."
            # Also log this error to the database as part of AI response
            db_service.log_chat_interaction(
                user_message=user_message,
                ai_response=f"**Error:** {error_message}",
                source_documents=source_documents_for_logging
            )


    async def get_full_response(self, user_message: str, history: List[Dict[str, str]]) -> str:
        # Helper to get the full response (e.g., for logging) - this function is now less critical
        # as logging happens directly in chat_stream after full response is known.
        # However, keeping it for compatibility if other parts of the code use it.
        full_response_content = []
        async for chunk in self.chat_stream(user_message, history):
            full_response_content.append(chunk)
        return "".join(full_response_content)

if __name__ == "__main__":
    # Example usage (requires OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY, NEON_DB_URL in .env)
    # And a populated Qdrant collection, and an initialized chat_history table
    import asyncio

    async def main():
        chat_service = ChatService()
        
        # Example with history
        chat_history = [
            {"user_message": "What is physical AI?", "ai_response": "Physical AI refers to AI systems that are embodied in physical forms, enabling them to interact with the real world. This includes robots, drones, and other intelligent machines."},
        ]
        
        print("Streaming chat response (with context):")
        async for chunk in chat_service.chat_stream("How do these systems interact with their environment?", chat_history):
            print(chunk, end="")
        print("\n--- End of Stream ---")
        
        print("\nCheck your Neon Postgres database for the logged interaction!")

    asyncio.run(main())
