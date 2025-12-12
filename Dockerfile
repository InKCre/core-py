# Multi-stage build for InKCre Core-Py
FROM python:3.12-slim as builder

# Install PDM
RUN pip install --no-cache-dir pdm

# Set workdir
WORKDIR /app

# Copy all for dependency installation
COPY . .

# Install core dependencies
RUN pdm install --prod --no-editable

# Install extensions dependencies
RUN for dir in extensions/*/; do \
        if [ -f "$dir/pyproject.toml" ]; then \
            cd "$dir" && pdm install --prod --no-editable && cd /app; \
        fi; \
    done

# Final stage
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code (excluding extensions)
COPY app/ app/
COPY run.py .
COPY pyproject.toml .
COPY pdm.lock .
COPY alembic.ini .
COPY migrations/ migrations/
COPY utils/ utils/
COPY requirements.txt .

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "run:api_app", "--host", "0.0.0.0", "--port", "8000"]