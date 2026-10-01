from django.urls import path
from .views import (
    MemoryListCreateAPIView,
    MemoryDetailAPIView,
    ScreenshotMemoryCreateAPIView,
    SearchAPIView,
    AskAPIView,
    RegisterAPIView,
    LoginAPIView,
    MeAPIView,
)

urlpatterns = [
    path("auth/register/", RegisterAPIView.as_view(), name="auth-register"),
    path("auth/login/", LoginAPIView.as_view(), name="auth-login"),
    path("auth/me/", MeAPIView.as_view(), name="auth-me"),
    # Phase 1: Core memories list & ingest
    path("memories/", MemoryListCreateAPIView.as_view(), name="memory-list-create"),
    path("memories/<uuid:pk>/", MemoryDetailAPIView.as_view(), name="memory-detail"),

    # Phase 7: Screenshot Capture & OCR Ingest
    path("memories/screenshot/", ScreenshotMemoryCreateAPIView.as_view(), name="memory-screenshot"),

    # Phase 2: Hybrid & Semantic Search
    path("search/", SearchAPIView.as_view(), name="memory-search"),

    # Phase 4: LLM Answer Synthesis Layer with Citations
    path("ask/", AskAPIView.as_view(), name="memory-ask"),
]
