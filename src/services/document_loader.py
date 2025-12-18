# src\services\document_loader.py
import os
import re
import hashlib
from typing import List, Dict

class DocumentLoader:
    def __init__(self, docs_path: str, min_chunk_size: int = 200, max_chunk_size: int = 2000):
        self.docs_path = docs_path
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size

    def load_documents(self) -> List[Dict[str, str]]:
        documents = []
        for root, _, files in os.walk(self.docs_path):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    documents.append({"content": content, "source_file": file_path})
        return documents

    def chunk_document(self, document: Dict[str, str]) -> List[Dict[str, str]]:
        """Chunk document by sections, keeping headers with their content."""
        content = document["content"]
        source_file = document["source_file"]
        chunks = []

        # Remove frontmatter (YAML between --- markers)
        content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
        
        # Split by H2 and H3 headers to get meaningful sections
        # This pattern captures the header and everything until the next header
        sections = re.split(r'(?=\n#{2,3}\s)', content)
        
        current_chunk = ""
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # If adding this section would exceed max size, save current chunk first
            if current_chunk and len(current_chunk) + len(section) > self.max_chunk_size:
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(self._create_chunk(current_chunk.strip(), source_file))
                current_chunk = section
            else:
                # Combine small sections together
                if current_chunk:
                    current_chunk += "\n\n" + section
                else:
                    current_chunk = section
            
            # If current chunk is large enough and section is complete, save it
            if len(current_chunk) >= self.min_chunk_size and section.endswith('\n'):
                chunks.append(self._create_chunk(current_chunk.strip(), source_file))
                current_chunk = ""
        
        # Don't forget the last chunk
        if current_chunk.strip() and len(current_chunk.strip()) >= self.min_chunk_size:
            chunks.append(self._create_chunk(current_chunk.strip(), source_file))
        elif current_chunk.strip() and chunks:
            # Append small remaining content to last chunk
            last_chunk = chunks[-1]
            combined = last_chunk["content"] + "\n\n" + current_chunk.strip()
            chunks[-1] = self._create_chunk(combined, source_file)
        elif current_chunk.strip():
            # If it's the only content, keep it regardless of size
            chunks.append(self._create_chunk(current_chunk.strip(), source_file))
        
        # If no chunks were created, use the whole document
        if not chunks and content.strip():
            chunks.append(self._create_chunk(content.strip(), source_file))

        return chunks

    def _create_chunk(self, content: str, source_file: str) -> Dict[str, str]:
        chunk_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        return {
            "content": content,
            "source_file": source_file,
            "chunk_hash": chunk_hash,
        }

    def load_and_chunk_documents(self) -> List[Dict[str, str]]:
        all_chunks = []
        documents = self.load_documents()
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks

if __name__ == "__main__":
    # Example usage:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    textbook_docs_path = os.path.join(current_dir, "..", "..", "..", "docs")

    loader = DocumentLoader(docs_path=textbook_docs_path)
    all_chunks = loader.load_and_chunk_documents()
    print(f"Loaded and chunked {len(all_chunks)} chunks.")
    for i, chunk in enumerate(all_chunks[:5]):
        print(f"--- Chunk {i+1} from {chunk['source_file']} (Hash: {chunk['chunk_hash']}) ---")
        print(f"Length: {len(chunk['content'])} chars")
        print(f"{chunk['content'][:300]}...")
        print("-" * 50)
