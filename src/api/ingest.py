# src\api\ingest.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from starlette.responses import JSONResponse
import os

from src.services.document_loader import DocumentLoader
from src.services.embedding_service import EmbeddingService
from src.services.vector_store_service import VectorStoreService
from src.api.security import get_api_key

router = APIRouter()

@router.post("/ingest", summary="Trigger the document ingestion process", dependencies=[Depends(get_api_key)])
async def ingest_documents(background_tasks: BackgroundTasks):
    """
    Triggers the document ingestion process.
    Reads markdown files, chunks them, creates embeddings, and stores them in Qdrant.
    The process runs in the background.
    """
    
    # Determine the path to the docs/docs directory
    # Determine the path to the docs directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # FIX: Sirf 2 baar piche jayen (api -> src -> root) aur ek baar docs mein
    textbook_docs_path = os.path.join(current_dir, "..", "..", "docs")

    if not os.path.exists(textbook_docs_path):
        raise HTTPException(status_code=404, detail=f"Document path not found: {textbook_docs_path}")

    async def run_ingestion():
        try:
            document_loader = DocumentLoader(docs_path=textbook_docs_path)
            embedding_service = EmbeddingService()
            vector_store_service = VectorStoreService()

            print("Starting document loading and chunking...")
            chunks = document_loader.load_and_chunk_documents()
            print(f"Loaded and chunked {len(chunks)} documents.")

            if not chunks:
                print("No documents found to ingest.")
                return

            print("Generating embeddings...")
            texts_to_embed = [chunk["content"] for chunk in chunks]
            embeddings = embedding_service.get_embeddings(texts_to_embed)
            print("Embeddings generated.")

            print("Recreating Qdrant collection and upserting vectors...")
            vector_store_service.recreate_collection()
            upsert_result = vector_store_service.upsert_vectors(chunks, embeddings)
            print(f"Ingestion complete. Upsert status: {upsert_result}")

        except Exception as e:
            print(f"Error during ingestion: {e}")
            # Optionally log the error to a file or monitoring system

    background_tasks.add_task(run_ingestion)
    return JSONResponse(status_code=200, content={"message": "Ingestion process started in the background."})