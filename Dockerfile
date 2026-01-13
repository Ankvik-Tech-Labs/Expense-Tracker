FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# - git: needed for pip git+ dependencies
# - build-essential: C compiler for native extensions (safe-pysha3, etc.)
# - python3-dev: Python headers for C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml .
COPY uv.lock .

# Workaround: cchecksum's setup.py has a bug that expects requirements.txt
RUN touch requirements.txt

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY src/ src/
COPY app/ app/
COPY data/ data/

# Copy ape configuration for crypto-portfolio-tracker
COPY ape-config.yaml .

# Install Ape plugins (infura, etherscan, base, etc.)
# Use || true since plugins may already be installed via crypto-portfolio-tracker
RUN uv run ape plugins install . || true

# Expose Streamlit port
EXPOSE 8501

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit app (--no-sync to avoid re-resolving dependencies at runtime)
CMD ["uv", "run", "--no-sync", "streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
