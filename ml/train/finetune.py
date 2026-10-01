"""
Fine-tuning Pipeline for Recall Embedding Model.
Base Model: all-MiniLM-L6-v2 (dim: 384)
Loss: MultipleNegativesRankingLoss
Features:
- Configurable epochs, batch size, learning rate
- Early stopping based on validation loss
- CSV logging of train and val loss per epoch
- Checkpoint saving to ml/checkpoints/recall-finetuned-v1/
"""

import os
import sys
import csv
import json
import argparse
import logging
import torch
from torch.utils.data import Dataset, DataLoader
from sentence_transformers import SentenceTransformer, InputExample, losses

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ML_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_DIR = os.path.dirname(ML_DIR)


class TripletDataset(Dataset):
    """PyTorch Dataset loading (anchor, positive, negative) records."""
    def __init__(self, json_path: str):
        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        return InputExample(texts=[item["anchor"], item["positive"], item["negative"]])


def collate_fn(batch):
    return batch


def evaluate_val_loss(model, loss_func, val_loader, device):
    """Computes mean loss over validation triplets."""
    model.eval()
    total_loss = 0.0
    steps = 0
    with torch.no_grad():
        for batch in val_loader:
            # Tokenize texts for the loss function
            sentence_features = [
                model.tokenize([example.texts[i] for example in batch])
                for i in range(3)
            ]
            sentence_features = [{k: (v.to(device) if hasattr(v, "to") else v) for k, v in sf.items()} for sf in sentence_features]
            labels = torch.zeros(len(batch), dtype=torch.long, device=device)
            loss_val = loss_func(sentence_features, labels)
            total_loss += loss_val.item()
            steps += 1
    return total_loss / max(steps, 1)


def train_model(
    base_model_name: str = "all-MiniLM-L6-v2",
    batch_size: int = 16,
    epochs: int = 4,
    learning_rate: float = 2e-5,
    patience: int = 3,
    output_checkpoint_name: str = "recall-finetuned-v1",
):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"Using compute device: {device.upper()}")
    if device == "cpu":
        logger.info("Running on CPU. For large datasets, running in Google Colab with GPU is recommended.")

    train_path = os.path.join(ML_DIR, "data", "train_triplets.json")
    val_path = os.path.join(ML_DIR, "data", "val_triplets.json")

    if not os.path.exists(train_path):
        logger.info("Triplets not found. Running generate_triplets.py first...")
        sys.path.insert(0, os.path.join(ML_DIR, "data"))
        from generate_triplets import build_triplets
        build_triplets(target_count=250, train_split=0.8)

    train_dataset = TripletDataset(train_path)
    val_dataset = TripletDataset(val_path)

    logger.info(f"Loaded {len(train_dataset)} training examples, {len(val_dataset)} validation examples.")

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        drop_last=True if len(train_dataset) > batch_size else False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=collate_fn,
    )

    # 1. Initialize Base SentenceTransformer
    logger.info(f"Initializing base model: '{base_model_name}'...")
    model = SentenceTransformer(base_model_name, device=device)

    # 2. Objective Loss Function
    # MultipleNegativesRankingLoss optimizes:
    # anchor matches positive, while being repelled by the negative (and in-batch negatives)
    train_loss = losses.MultipleNegativesRankingLoss(model)

    # 3. Optimizer and Scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=0.01)
    total_steps = len(train_loader) * epochs
    warmup_steps = int(total_steps * 0.1)

    checkpoint_dir = os.path.join(ML_DIR, "checkpoints", output_checkpoint_name)
    results_dir = os.path.join(ML_DIR, "results")
    os.makedirs(checkpoint_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)
    csv_log_path = os.path.join(results_dir, "loss_history.csv")

    loss_history = []
    best_val_loss = float("inf")
    patience_counter = 0

    logger.info(f"Starting training: {epochs} epochs, batch_size={batch_size}, lr={learning_rate}")

    for epoch in range(1, epochs + 1):
        model.train()
        epoch_train_loss = 0.0
        train_steps = 0

        for step, batch in enumerate(train_loader):
            optimizer.zero_grad()
            sentence_features = [
                model.tokenize([example.texts[i] for example in batch])
                for i in range(3)
            ]
            sentence_features = [{k: (v.to(device) if hasattr(v, "to") else v) for k, v in sf.items()} for sf in sentence_features]
            labels = torch.zeros(len(batch), dtype=torch.long, device=device)

            loss_val = train_loss(sentence_features, labels)
            loss_val.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            epoch_train_loss += loss_val.item()
            train_steps += 1

        avg_train_loss = epoch_train_loss / max(train_steps, 1)

        # Validation step
        avg_val_loss = evaluate_val_loss(model, train_loss, val_loader, device)

        logger.info(
            f"Epoch {epoch:02d}/{epochs:02d} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}"
        )

        loss_history.append({
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 4),
            "val_loss": round(avg_val_loss, 4),
        })

        # Save Best Checkpoint
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            logger.info(f"New best val loss ({best_val_loss:.4f})! Saving checkpoint to {checkpoint_dir}")
            model.save(checkpoint_dir)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping triggered at epoch {epoch} (no val improvement in {patience} epochs).")
                break

    # Write loss history to CSV
    with open(csv_log_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["epoch", "train_loss", "val_loss"])
        writer.writeheader()
        writer.writerows(loss_history)

    logger.info(f"Loss history logged to: {csv_log_path}")
    logger.info(f"Fine-tuned model checkpoint saved to: {checkpoint_dir}")
    return checkpoint_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune all-MiniLM-L6-v2 on Recall memory triplets.")
    parser.add_argument("--epochs", type=int, default=4, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=16, help="Training batch size")
    parser.add_argument("--lr", type=float, default=2e-5, help="Learning rate")
    args = parser.parse_args()

    train_model(epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr)
