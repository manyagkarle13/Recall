import json
from django.contrib.auth import authenticate, get_user_model
from rest_framework.authtoken.models import Token
from rest_framework import serializers
from .models import MemoryItem

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("That username is already taken.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        token, _ = Token.objects.get_or_create(user=user)
        return user, token


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        token, _ = Token.objects.get_or_create(user=user)
        return {"user": user, "token": token.key}


class MemoryItemSerializer(serializers.ModelSerializer):
    """List serializer for MemoryItem records."""
    has_embedding = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = MemoryItem
        fields = [
            "id",
            "source_type",
            "title",
            "raw_content",
            "source_url",
            "created_at",
            "chunk_index",
            "parent_id",
            "metadata",
            "has_embedding",
            "media_url",
        ]
        read_only_fields = ["id", "created_at", "chunk_index", "parent_id"]

    def get_has_embedding(self, obj) -> bool:
        return bool(obj.embedding is not None and len(obj.embedding) > 0)

    def get_media_url(self, obj) -> str:
        if obj.metadata and isinstance(obj.metadata, dict):
            return obj.metadata.get("media_url", "")
        return ""


class MemoryItemDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer returning full representation including embedding vector."""
    embedding = serializers.SerializerMethodField()
    media_url = serializers.SerializerMethodField()

    class Meta:
        model = MemoryItem
        fields = [
            "id",
            "source_type",
            "title",
            "raw_content",
            "source_url",
            "created_at",
            "chunk_index",
            "parent_id",
            "metadata",
            "embedding",
            "media_url",
        ]

    def get_embedding(self, obj):
        if obj.embedding is not None:
            return list(obj.embedding)
        return None

    def get_media_url(self, obj) -> str:
        if obj.metadata and isinstance(obj.metadata, dict):
            return obj.metadata.get("media_url", "")
        return ""


class MemoryCreateRequestSerializer(serializers.Serializer):
    """Serializer validating incoming memory creation via raw text or file upload."""
    title = serializers.CharField(max_length=500, required=False, allow_blank=True)
    raw_content = serializers.CharField(required=False, allow_blank=True)
    source_type = serializers.ChoiceField(
        choices=MemoryItem.SOURCE_CHOICES,
        default="text",
        required=False,
    )
    source_url = serializers.URLField(max_length=2048, required=False, allow_blank=True, allow_null=True)
    file = serializers.FileField(required=False, allow_null=True)

    def validate(self, data):
        raw_content = data.get("raw_content", "").strip()
        uploaded_file = data.get("file", None)

        if not raw_content and not uploaded_file:
            raise serializers.ValidationError(
                "Either 'raw_content' or a 'file' upload must be provided."
            )
        return data


class SearchRequestSerializer(serializers.Serializer):
    """Validates natural language search queries with hybrid scoring options."""
    query = serializers.CharField(required=True, min_length=1, max_length=2000)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=50, required=False)
    alpha = serializers.FloatField(default=0.6, min_value=0.0, max_value=1.0, required=False)
    mode = serializers.ChoiceField(
        choices=["hybrid", "vector", "keyword"],
        default="hybrid",
        required=False,
    )
    source_type = serializers.ChoiceField(
        choices=["text", "webpage", "screenshot", "pdf"],
        required=False,
        allow_blank=True,
    )
    threshold = serializers.FloatField(default=0.45, min_value=0.0, max_value=1.0, required=False)


class AskRequestSerializer(serializers.Serializer):
    """Validates question-answering requests with Groq synthesis."""
    question = serializers.CharField(required=True, min_length=1, max_length=2000)
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20, required=False)
    threshold = serializers.FloatField(default=0.45, min_value=0.0, max_value=1.0, required=False)
    alpha = serializers.FloatField(default=0.6, min_value=0.0, max_value=1.0, required=False)
    mode = serializers.ChoiceField(
        choices=["hybrid", "vector", "keyword"],
        default="hybrid",
        required=False,
    )
    model = serializers.CharField(required=False, allow_blank=True, default=None)


class ScreenshotCreateSerializer(serializers.Serializer):
    image_base64 = serializers.CharField(required=True)
    title = serializers.CharField(max_length=500, required=False, allow_blank=True)
    source_url = serializers.URLField(max_length=2048, required=False, allow_blank=True)
