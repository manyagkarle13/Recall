from django.test import SimpleTestCase
from memories.utils.chunking import chunk_text, count_tokens


class ChunkingUtilityTests(SimpleTestCase):
    def test_short_text_single_chunk(self):
        text = "This is a brief note about machine learning embeddings."
        chunks = chunk_text(text, max_tokens=500)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0][0], 0)
        self.assertEqual(chunks[0][1], text)

    def test_long_text_chunking(self):
        # Generate text with ~600 words (>500 tokens)
        long_paragraph = " ".join(["sentence about metric learning representations and triplets."] * 80)
        chunks = chunk_text(long_paragraph, max_tokens=100, overlap_tokens=20)
        self.assertGreater(len(chunks), 1)
        for idx, content, tok_count in chunks:
            self.assertTrue(len(content) > 0)
            self.assertLessEqual(tok_count, 110)
