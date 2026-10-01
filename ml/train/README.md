# Training Guide: Local CPU vs Google Colab GPU

This directory contains the training pipeline to fine-tune `all-MiniLM-L6-v2` using `MultipleNegativesRankingLoss`.

## 1. Running Locally (CPU / GPU)
If running locally:
```bash
python ml/train/finetune.py --epochs 4 --batch_size 16
```
The script automatically detects if a CUDA GPU is present; otherwise, it executes on CPU. On modern CPUs, 250 triplets for 4 epochs completes in ~1-2 minutes.

---

## 2. Running on Google Colab (Free T4 GPU)
For larger datasets or rapid iteration, open Google Colab:
1. Set runtime to **GPU**: `Runtime` -> `Change runtime type` -> `T4 GPU`.
2. Install dependencies:
```bash
!pip install sentence-transformers torch
```
3. Upload `ml/data/train_triplets.json` and `ml/data/val_triplets.json`.
4. Run:
```python
from finetune import train_model
train_model(epochs=10, batch_size=32, learning_rate=2e-5)
```
5. Download the output checkpoint folder `recall-finetuned-v1` and place it in `ml/checkpoints/`.
