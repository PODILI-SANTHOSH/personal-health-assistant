from __future__ import annotations

import hashlib
from pathlib import Path

import chromadb

from backend.config import settings
from backend.services.document_loader import extract_text, is_supported_file
from backend.services.embeddings import EmbeddingService
from backend.services.safety import build_safety_notice


class RAGPipeline:
    def __init__(self, data_dir: Path | str = settings.DATA_DIR, chroma_path: Path | str = settings.CHROMA_PATH) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_service = EmbeddingService()
        self.client = chromadb.PersistentClient(path=str(chroma_path))
        try:
            self.collection = self.client.get_or_create_collection(
                name='medical_knowledge_base',
                metadata={'hnsw:space': 'cosine'},
                embedding_function=self.embedding_service,
            )
        except Exception:
            self.collection = self.client.get_or_create_collection(
                name='medical_knowledge_base',
                metadata={'hnsw:space': 'cosine'}
            )

    def _ensure_collection(self) -> None:
        try:
            self.collection.count()
        except Exception:
            self.collection = self.client.get_or_create_collection(
                name='medical_knowledge_base',
                metadata={'hnsw:space': 'cosine'}
            )

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
        paragraphs = [paragraph.strip() for paragraph in text.split('\n\n') if paragraph.strip()]
        chunks: list[str] = []
        current = ''
        for paragraph in paragraphs:
            if len(current) + len(paragraph) < chunk_size:
                current = (current + '\n\n' + paragraph).strip()
            else:
                if current:
                    chunks.append(current)
                current = paragraph
        if current:
            chunks.append(current)

        final_chunks: list[str] = []
        for idx, chunk in enumerate(chunks):
            if idx == 0:
                final_chunks.append(chunk)
                continue
            previous = final_chunks[-1]
            overlap_text = ' '.join(previous.split()[-overlap:]) if overlap else ''
            merged = (overlap_text + ' ' + chunk).strip()
            final_chunks[-1] = previous
            final_chunks.append(merged)
        return final_chunks or [text[:chunk_size]]

    def index_document(self, file_path: str | Path) -> dict:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f'Document not found: {path}')
        if not is_supported_file(path):
            raise ValueError('Only PDF and TXT files are supported.')

        text = extract_text(path)
        if not text.strip():
            raise ValueError('No readable text found in the uploaded document.')

        chunks = self._chunk_text(text)
        ids = []
        documents = []
        metadatas = []
        for index, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f'{path.name}:{index}:{chunk}'.encode('utf-8')).hexdigest()
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append({
                'source': path.name,
                'section': f'Section {index + 1}',
                'stored_at': str(path.stat().st_mtime),
            })

        existing = self.collection.get(where={'source': path.name})
        if existing and existing.get('ids'):
            self.collection.delete(ids=existing['ids'])

        embeddings = self.embedding_service(documents)
        self.collection.add(documents=documents, ids=ids, metadatas=metadatas, embeddings=embeddings)
        return {
            'document': path.name,
            'chunks': len(chunks),
            'status': 'indexed'
        }

    def search(self, question: str, top_k: int = 3) -> list[dict]:
        self._ensure_collection()
        try:
            collection_snapshot = self.collection.peek()
            if not collection_snapshot.get('ids'):
                return []
        except Exception:
            return []

        query_embeddings = self.embedding_service(question)
        results = self.collection.query(query_embeddings=query_embeddings, n_results=top_k, include=['documents', 'metadatas', 'distances'])
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        matched = []
        for idx, document in enumerate(documents):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            matched.append({
                'source': metadata.get('source', 'Unknown source'),
                'section': metadata.get('section', 'Document section'),
                'snippet': document,
                'distance': distances[idx] if idx < len(distances) else 0,
            })
        return matched

    def process_question(self, question: str, user_profile: dict | None = None, conversation_context: list | None = None) -> dict:
        evidence = self.search(question, top_k=3)
        if not evidence:
            return {
                'answer': (
                    'I could not find relevant evidence in the indexed medical knowledge base for this question. '
                    'Please ask about a topic supported by the uploaded documents or consult a licensed clinician for a personal evaluation.'
                ),
                'sources': [],
                'safety_notice': build_safety_notice(question),
            }

        context = '\n\n'.join(f"- {item['source']} ({item['section']}): {item['snippet']}" for item in evidence)
        profile_context = 'No profile was provided by the user.'
        if user_profile:
            profile_context = (
                f"User profile notes: name={user_profile.get('name', '')}, age_range={user_profile.get('age_range', '')}, "
                f"allergies={user_profile.get('allergies', '')}, conditions={user_profile.get('conditions', '')}, "
                f"medications={user_profile.get('medications', '')}."
            )

        answer = (
            'Using the source material in the uploaded medical library, the best-supported guidance is that: ' 
            f"{question.strip()} should be interpreted with the available evidence and personal context in mind. "
            f"{context[:1200]} "
            'This information is educational and not a diagnosis. For symptoms that are severe, worsening, or concerning, contact a clinician or urgent care.'
        )

        return {
            'answer': answer,
            'sources': [
                {'source': item['source'], 'section': item['section'], 'snippet': item['snippet'][:220]} for item in evidence
            ],
            'safety_notice': build_safety_notice(question),
            'profile_context': profile_context,
        }


rag_pipeline = RAGPipeline()
