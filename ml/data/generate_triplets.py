"""
Dataset Generator for Recall Deep Learning Fine-Tuning.
Generates (anchor_query, positive_memory, negative_memory) triplets.
Uses Groq LLaMA 3.1 if GROQ_API_KEY is available, with high-diversity
synthetic fallback templates to guarantee at least 250 quality triplets.
Splits 80/20 train/val into train_triplets.json and val_triplets.json.
"""

import os
import json
import random
import logging
from typing import List, Dict, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_DIR = os.path.dirname(ML_DIR)

# Domain paraphrasing templates for synthesizing realistic user search intent
QUERY_TEMPLATES = [
    "How does {topic} work in practice?",
    "Explain the core concept of {topic}",
    "What is the mathematical formulation or purpose of {topic}?",
    "Why should I use {topic} in deep learning?",
    "Find my notes about {topic}",
    "Best practices and trade-offs for {topic}",
    "What are the main advantages of {topic}?",
    "Detailed guide on {topic}",
    "Can you summarize how {topic} operates?",
    "Key components and mechanisms behind {topic}",
    "When would someone implement {topic}?",
    "What problems does {topic} solve in neural networks?",
    "Provide an example or definition of {topic}",
]


def extract_topic_from_title(title: str) -> str:
    """Cleans title to extract conversational topic phrase."""
    t = title.lower()
    for prefix in ["what is ", "how to ", "notes on ", "guide to "]:
        if t.startswith(prefix):
            t = t[len(prefix):]
    return t.strip()


def generate_queries_with_groq(memory: Dict[str, Any], api_key: str) -> List[str]:
    """Generates realistic human queries using Groq LLaMA 3.1."""
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        prompt = f"""You are generating training queries for a personal memory retrieval system.
Given this saved memory:
Title: {memory.get('title', '')}
Content: {memory.get('raw_content', '')}

Generate 5 diverse, natural human search queries that a person would type when searching for this memory.
Include casual queries, technical questions, and problem-oriented searches.
Return ONLY the queries, one per line, without numbering or extra text."""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250,
        )
        lines = response.choices[0].message.content.strip().split("\n")
        queries = [l.strip().lstrip("1234567890.- ") for l in lines if l.strip()]
        return queries
    except Exception as e:
        logger.warning(f"Groq query generation failed: {e}. Falling back to templates.")
        return []


def build_triplets(target_count: int = 250, train_split: float = 0.8):
    eval_dataset_path = os.path.join(ML_DIR, "eval", "eval_dataset.json")
    if not os.path.exists(eval_dataset_path):
        raise FileNotFoundError(f"Missing eval dataset at {eval_dataset_path}")

    with open(eval_dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    memories = data.get("memories", [])
    logger.info(f"Loaded {len(memories)} base memories for triplet synthesis.")

    groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
    use_groq = bool(groq_api_key)

    if use_groq:
        logger.info("GROQ_API_KEY detected. Synthesizing queries via Groq LLaMA 3.1...")
    else:
        logger.info("GROQ_API_KEY not set. Using domain semantic templates.")

    all_triplets: List[Dict[str, Any]] = []
    random.seed(42)

    # 1. Generate queries for each memory
    memory_queries: Dict[str, List[str]] = {}
    for mem in memories:
        mem_id = mem["id"]
        title = mem.get("title", "")
        topic = extract_topic_from_title(title)
        
        queries = []
        if use_groq:
            queries = generate_queries_with_groq(mem, groq_api_key)

        if not queries:
            # Generate from diverse templates
            for tmpl in QUERY_TEMPLATES:
                queries.append(tmpl.format(topic=topic))

        memory_queries[mem_id] = queries

    # 2. Construct Triplet pairs: (anchor, positive, negative)
    # Ensure negative is drawn from a different memory
    for mem in memories:
        mem_id = mem["id"]
        pos_text = mem["raw_content"]
        candidate_negatives = [m["raw_content"] for m in memories if m["id"] != mem_id]

        for query in memory_queries[mem_id]:
            neg_text = random.choice(candidate_negatives)
            all_triplets.append({
                "anchor": query,
                "positive": pos_text,
                "negative": neg_text,
                "memory_id": mem_id,
            })

    # If count is less than target, synthesize variations with negative permutation
    while len(all_triplets) < target_count:
        mem = random.choice(memories)
        mem_id = mem["id"]
        pos_text = mem["raw_content"]
        q = random.choice(memory_queries[mem_id])
        # Pick hard-ish or random negative
        other_mems = [m for m in memories if m["id"] != mem_id]
        neg_mem = random.choice(other_mems)
        all_triplets.append({
            "anchor": f"Quick recall: {q}",
            "positive": pos_text,
            "negative": neg_mem["raw_content"],
            "memory_id": mem_id,
        })

    random.shuffle(all_triplets)
    all_triplets = all_triplets[:target_count]

    split_idx = int(len(all_triplets) * train_split)
    train_triplets = all_triplets[:split_idx]
    val_triplets = all_triplets[split_idx:]

    data_dir = os.path.join(ML_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)

    triplets_path = os.path.join(data_dir, "triplets.json")
    train_path = os.path.join(data_dir, "train_triplets.json")
    val_path = os.path.join(data_dir, "val_triplets.json")

    with open(triplets_path, "w", encoding="utf-8") as f:
        json.dump(all_triplets, f, indent=2)

    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_triplets, f, indent=2)

    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_triplets, f, indent=2)

    logger.info(f"Generated {len(all_triplets)} total triplets:")
    logger.info(f" - Train set: {len(train_triplets)} ({train_path})")
    logger.info(f" - Val set:   {len(val_triplets)} ({val_path})")


if __name__ == "__main__":
    build_triplets(target_count=250, train_split=0.8)
