from __future__ import annotations

import hashlib
import math
import os
from typing import Any


class EmbeddingService:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', fallback_dim: int = 384) -> None:
        self.model_name = model_name
        self.model: Any | None = None
        self.fallback_dim = fallback_dim
        self.allow_download = os.getenv('ALLOW_EMBEDDING_DOWNLOAD', '').strip().lower() in {'1', 'true', 'yes', 'on'}

    def name(self) -> str:
        return self.model_name

    def get_model(self):
        if self.model is not None:
            return self.model
        if not self.allow_download:
            return None
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
        except Exception:
            self.model = None
        return self.model

    def _fallback_embed(self, text: str) -> list[float]:
        if not text or not text.strip():
            return [0.0] * self.fallback_dim

        tokens = [token.lower() for token in text.split() if token.strip()]
        if not tokens:
            return [0.0] * self.fallback_dim

        vector = [0.0] * self.fallback_dim
        for index, token in enumerate(sorted(set(tokens))):
            digest = hashlib.sha256(token.encode('utf-8')).digest()
            for dim in range(self.fallback_dim):
                byte_value = digest[dim % len(digest)]
                vector[dim] += ((byte_value / 255.0) - 0.5) * (1.0 / (index + 1))

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed(self, text: str):
        model = self.get_model()
        if model is not None:
            try:
                return model.encode(text).tolist()
            except Exception:
                pass
        return self._fallback_embed(text)

    def __call__(self, input: str | list[str]) -> list[list[float]]:
        values = [input] if isinstance(input, str) else list(input)
        return [self.embed(value) for value in values]
