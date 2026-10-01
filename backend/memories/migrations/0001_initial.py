import uuid
from django.db import migrations, models
from django.conf import settings


def get_operations():
    db_engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
    ops = []

    if "postgresql" in db_engine:
        try:
            import pgvector.django
            ops.append(pgvector.django.VectorExtension())
            emb_field = pgvector.django.VectorField(blank=True, dimensions=384, null=True)
        except Exception:
            emb_field = models.JSONField(blank=True, null=True)
    else:
        emb_field = models.JSONField(blank=True, null=True)

    ops.append(
        migrations.CreateModel(
            name="MemoryItem",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("source_type", models.CharField(choices=[("text", "Text Note"), ("webpage", "Webpage"), ("screenshot", "Screenshot"), ("pdf", "PDF Document")], default="text", max_length=20)),
                ("title", models.CharField(blank=True, default="Untitled Memory", max_length=500)),
                ("raw_content", models.TextField()),
                ("source_url", models.URLField(blank=True, max_length=2048, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("embedding", emb_field),
                ("chunk_index", models.PositiveIntegerField(default=0)),
                ("parent_id", models.UUIDField(blank=True, db_index=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "verbose_name": "Memory Item",
                "verbose_name_plural": "Memory Items",
                "db_table": "memory_items",
                "ordering": ["-created_at"],
            },
        )
    )
    return ops


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = get_operations()
