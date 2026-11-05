# ==========================================================================
# Backend image: FastAPI + LitGPT engine
#
# CPU (default):   docker compose build backend
# GPU (NVIDIA):    docker compose -f docker-compose.yml -f docker-compose.gpu.yml build backend
#
# Model weights, documents, datasets and checkpoints are NOT in the image:
# they come from volumes (see docker-compose.yml), so rebuilding the image
# never deletes them.
# ==========================================================================
FROM python:3.12-slim

# Where PyTorch is downloaded from: CPU build by default, CUDA build for GPU
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# ---- 1. Dependencies (cached layer: only rebuilt when pyproject.toml changes) ----
# torch and torchvision must come from the same index (CPU or CUDA build),
# then their versions are frozen so other packages cannot replace them.
RUN pip install --index-url "${TORCH_INDEX_URL}" torch torchvision \
    && pip freeze | grep -E "^(torch|torchvision)==" > /tmp/torch-constraints.txt

COPY pyproject.toml README.md LICENSE.md ./
# Empty package so pip can read the project metadata and install its dependencies.
# The real code is copied in step 2 and found through PYTHONPATH.
RUN mkdir litgpt && touch litgpt/__init__.py \
    && pip install --extra-index-url "${TORCH_INDEX_URL}" -c /tmp/torch-constraints.txt ".[extra,platform]" \
    && pip uninstall -y litgpt \
    && rm -rf litgpt build *.egg-info

# ---- 2. Source code ----
COPY litgpt ./litgpt
COPY config ./config
COPY inference ./inference
COPY api ./api
COPY backend ./backend
COPY training ./training
COPY rag ./rag
COPY scripts ./scripts

# Run as a normal user, not root
RUN useradd --create-home --uid 1000 app \
    && mkdir -p models checkpoints datasets documents tokenizer logs .cache/huggingface \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["python", "-m", "backend.main"]
