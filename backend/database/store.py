from __future__ import annotations

from copy import deepcopy
from threading import Lock
from typing import Any


class InMemoryStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.users = {}
        self.conversations = {}
        self.documents = {}

    def get_or_create_profile(self, user_id: str) -> dict[str, Any]:
        with self._lock:
            profile = self.users.setdefault(user_id, {
                'user_id': user_id,
                'name': '',
                'age_range': '',
                'allergies': '',
                'conditions': '',
                'medications': '',
                'preferences': '',
            })
            return deepcopy(profile)

    def update_profile(self, user_id: str, updates: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            profile = self.users.setdefault(user_id, {
                'user_id': user_id,
                'name': '',
                'age_range': '',
                'allergies': '',
                'conditions': '',
                'medications': '',
                'preferences': '',
            })
            for key, value in updates.items():
                if key in profile:
                    profile[key] = value
            self.users[user_id] = profile
            return deepcopy(profile)

    def get_conversations(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return deepcopy(self.conversations.get(user_id, []))

    def create_conversation(self, user_id: str, conversation_id: str, question: str, answer: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
        with self._lock:
            thread = self.conversations.setdefault(user_id, [])
            entry = {
                'conversation_id': conversation_id,
                'messages': [
                    {'role': 'user', 'content': question, 'created_at': 'just now'},
                    {'role': 'assistant', 'content': answer, 'created_at': 'just now'}
                ],
                'title': question[:48] or 'New conversation',
                'updated_at': 'just now',
                'sources': sources,
            }
            thread.append(entry)
            return deepcopy(entry)

    def append_turn(self, user_id: str, conversation_id: str, question: str, answer: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
        with self._lock:
            thread = self.conversations.setdefault(user_id, [])
            match = None
            for item in thread:
                if item['conversation_id'] == conversation_id:
                    match = item
                    break
            if match is None:
                return self.create_conversation(user_id, conversation_id, question, answer, sources)
            match['messages'].append({'role': 'user', 'content': question, 'created_at': 'just now'})
            match['messages'].append({'role': 'assistant', 'content': answer, 'created_at': 'just now'})
            match['updated_at'] = 'just now'
            match['title'] = match['title'] or question[:48]
            match['sources'] = sources
            return deepcopy(match)

    def delete_conversation(self, user_id: str, conversation_id: str) -> bool:
        with self._lock:
            conversations = self.conversations.get(user_id, [])
            remaining = [item for item in conversations if item['conversation_id'] != conversation_id]
            if len(remaining) == len(conversations):
                return False
            self.conversations[user_id] = remaining
            return True

    def list_documents(self, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            user_docs = self.documents.get(user_id, [])
            return deepcopy(user_docs)

    def add_document(self, user_id: str, document_id: str, filename: str, status: str = 'indexed') -> dict[str, Any]:
        with self._lock:
            docs = self.documents.setdefault(user_id, [])
            item = {'document_id': document_id, 'filename': filename, 'status': status}
            if not any(existing['document_id'] == document_id for existing in docs):
                docs.append(item)
            return deepcopy(item)

    def remove_document(self, user_id: str, document_id: str) -> bool:
        with self._lock:
            docs = self.documents.get(user_id, [])
            updated = [item for item in docs if item['document_id'] != document_id]
            if len(updated) == len(docs):
                return False
            self.documents[user_id] = updated
            return True


store = InMemoryStore()
