FROM python:3.11-slim

WORKDIR /app

# Install Python requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source, migrations, ingestion, and transcripts
COPY backend/alembic.ini .
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY ingestion ./ingestion
COPY data ./data

ENV PYTHONPATH=/app

EXPOSE 8000

# Run Alembic migrations and then start Uvicorn
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
