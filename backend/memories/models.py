import uuid
import os
from django.db import models
from django.conf import settings


def get_vector_field():
    """Returns pgvector VectorField if using PostgreSQL, else JSONField."""
    db_engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
    if "postgresql" in db_engine:
        try:
            from pgvector.django import VectorField
            return VectorField(dimensions=384, null=True, blank=True)
        except Exception:
            pass
    return models.JSONField(null=True, blank=True, help_text="384-dimensional vector embedding")


class MemoryItem(models.Model):
    """Core memory item representation for text, web, and screenshots."""
    SOURCE_CHOICES = [
        ("text", "Text Note"),
        ("webpage", "Webpage"),
        ("screenshot", "Screenshot"),
        ("pdf", "PDF Document"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="memories",
        null=True,
        blank=True,
    )
    source_type = models.CharField(max_length=20, choices=SOURCE_CHOICES, default="text")
    title = models.CharField(max_length=500, blank=True, default="Untitled Memory")
    raw_content = models.TextField(help_text="Extracted or input plain text content")
    source_url = models.URLField(max_length=2048, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # 384-dimensional vector embedding
    embedding = get_vector_field()
    
    chunk_index = models.PositiveIntegerField(default=0)
    parent_id = models.UUIDField(null=True, blank=True, db_index=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "memory_items"
        ordering = ["-created_at"]
        verbose_name = "Memory Item"
        verbose_name_plural = "Memory Items"

    def __str__(self):
        prefix = f"[{self.source_type.upper()}]"
        suffix = f" (Part {self.chunk_index + 1})" if self.chunk_index > 0 else ""
        return f"{prefix} {self.title or self.raw_content[:40]}{suffix}"
