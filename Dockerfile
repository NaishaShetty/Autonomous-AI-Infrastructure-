# Autonomous AI Infrastructure -- Phase 6 Docker image
#
# CPU only, no GPU assumed. Installs the full project requirements.txt
# (torch/transformers included) so both `pytest tests/` and the benchmark
# runner work from the same image. If you only need the benchmark itself,
# its standalone release package
# (experiments/results/phase5_6_external_release/<ts>/release/benchmark/)
# has a much smaller requirements.txt (numpy/pandas/scikit-learn/scipy only)
# and can be built/run independently of this image.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install OS-level build deps needed by some pinned wheels on slim images.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY . .

# Default action: run the 16-task benchmark (fast, no GPU, no network).
# Override the command to run the test suite instead, e.g.:
#   docker run --rm autonomous-ai-infrastructure:latest pytest tests/unit/test_phase54_benchmark.py -q
CMD ["python", "scripts/run_phase5_4_benchmark.py"]
