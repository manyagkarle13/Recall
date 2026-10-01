"""
Embedding utility for Recall.
Dimension: 384 (all-MiniLM-L6-v2 architecture).
Supports auto-detecting and loading the Phase 3 fine-tuned checkpoint
('ml/checkpoints/recall-finetuned-v1') with runtime toggle support for
live demo comparisons between base and fine-tuned models.
"""

import os
import logging
from typing import List, Union
import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)


def resolve_model_path() -> str:
    """
    Resolves active model path.
    1. Checks Django settings or environment variable EMBEDDING_MODEL_NAME_OR_PATH
    2. Auto-detects local fine-tuned checkpoint 'ml/checkpoints/recall-finetuned-v1'
    3. Falls back to base 'all-MiniLM-L6-v2'
    """
    configured = None
    try:
        from django.conf import settings
        if settings.configured:
            configured = getattr(settings, "EMBEDDING_MODEL_NAME_OR_PATH", None)
    except Exception:
        pass

    if not configured:
        configured = os.getenv("EMBEDDING_MODEL_NAME_OR_PATH")

    if configured and os.path.exists(configured):
        return configured

    # Check for fine-tuned checkpoint in project ml/checkpoints/
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(curr_dir, "..", "..", ".."))
    ft_path = os.path.join(project_root, "ml", "checkpoints", "recall-finetuned-v1")
    if os.path.exists(ft_path):
        return ft_path

    # Fallback to base pretrained
    return "all-MiniLM-L6-v2"


class EmbeddingEngine:
    _instance = None

    def __init__(self, model_name_or_path: str = None, device: str = None):
        self.model_name_or_path = model_name_or_path or resolve_model_path()
        if device is None:
            try:
                from django.conf import settings
                if settings.configured:
                    device = getattr(settings, "EMBEDDING_DEVICE", "cpu")
            except Exception:
                pass
        self.device = device or os.getenv("EMBEDDING_DEVICE", "cpu")
        self._model = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def model(self):
        """Lazy loader for SentenceTransformer model."""
        if self._model is None:
            logger.info(f"Loading embedding model: '{self.model_name_or_path}' on {self.device}...")
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name_or_path, device=self.device)
            logger.info(f"Active model: {self.model_name_or_path} (dim: {self._model.get_sentence_embedding_dimension()})")
        return self._model

    def switch_model(self, model_name_or_path: str):
        """
        Hot-swap active model at runtime (e.g. for live comparison between
        base 'all-MiniLM-L6-v2' and fine-tuned 'recall-finetuned-v1').
        """
        logger.info(f"Switching active embedding model to: '{model_name_or_path}'")
        from sentence_transformers import SentenceTransformer
        self._model = SentenceTransformer(model_name_or_path, device=self.device)
        self.model_name_or_path = model_name_or_path

    def get_active_model_name(self) -> str:
        return self.model_name_or_path

    def encode(self, texts: Union[str, List[str]], normalize: bool = True) -> np.ndarray:
        if isinstance(texts, str):
            single = True
            texts = [texts]
        else:
            single = False

        cleaned_texts = [t.strip() if t and t.strip() else " " for t in texts]
        embeddings = self.model.encode(
            cleaned_texts,
            show_progress_bar=False,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
        )
        return embeddings[0] if single else embeddings


def get_embedding(text: str) -> List[float]:
    return EmbeddingEngine.get_instance().encode(text).tolist()


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    return [e.tolist() for e in EmbeddingEngine.get_instance().encode(texts)]


def set_active_embedding_model(model_path: str):
    EmbeddingEngine.get_instance().switch_model(model_path)


def get_active_model_info() -> dict:
    engine = EmbeddingEngine.get_instance()
    return {
        "model_path": engine.model_name_or_path,
        "is_finetuned": "finetuned" in engine.model_name_or_path.lower(),
        "device": engine.device,
    }
