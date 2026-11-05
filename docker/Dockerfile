# ==========================================================================
# Single image of the platform: web interface + REST API + LitGPT engine.
#
#   CPU (default):  docker compose build
#   GPU (NVIDIA):   docker compose -f docker-compose.yml -f docker-compose.gpu.yml build
#
# One process (FastAPI) serves the API and the built interface.
# Model weights, documents, datasets, checkpoints and conversations are NOT
# in the image: they come from volumes, so rebuilding never deletes them.
# ==========================================================================

# ---- Stage 1: build the web interface ----
FROM node:22-alpine AS frontend
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: Python runtime ----
FROM python:3.12-slim

# Where PyTorch is downloaded from: CPU build by default, CUDA build for GPU
ARG TORCH_INDEX_URL=https://download.pytorch.org/whl/cpu

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# torch and torchvision must come from the same index (CPU or CUDA build),
# then their versions are frozen so other packages cannot replace them.
RUN pip install --index-url "${TORCH_INDEX_URL}" torch torchvision \
    && pip freeze | grep -E "^(torch|torchvision)==" > /tmp/torch-constraints.txt

# Dependencies (cached layer: only rebuilt when pyproject.toml changes).
# An empty package lets pip read the project metadata; the real code is
# copied below and found through PYTHONPATH.
COPY pyproject.toml README.md LICENSE.md ./
RUN mkdir litgpt && touch litgpt/__init__.py \
    && pip install --extra-index-url "${TORCH_INDEX_URL}" -c /tmp/torch-constraints.txt ".[extra,platform]" \
    && pip uninstall -y litgpt \
    && rm -rf litgpt build *.egg-info

# Source code
COPY litgpt ./litgpt
COPY config ./config
COPY inference ./inference
COPY chat ./chat
COPY api ./api
COPY backend ./backend
COPY training ./training
COPY rag ./rag
COPY scripts ./scripts
# Built interface, served by FastAPI (FRONTEND_DIR default: frontend/dist)
COPY --from=frontend /build/dist ./frontend/dist

# Run as a normal user, not root
RUN useradd --create-home --uid 1000 app \
    && mkdir -p models checkpoints datasets documents tokenizer logs storage .cache/huggingface \
    && chown -R app:app /app
USER app

EXPOSE 4444

HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:4444/openapi.json')"

CMD ["python", "-m", "backend.main"]
