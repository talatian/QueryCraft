FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app


# Install uv
RUN pip install --upgrade pip setuptools wheel \
    && pip install uv

# Copy dependency files first (for caching)
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Copy the rest of the application code
COPY . /app/

# Make the entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]




# # Install system dependencies
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends \
#         postgresql-client \
#         build-essential \
#         libpq-dev \
#     && rm -rf /var/lib/apt/lists/*


