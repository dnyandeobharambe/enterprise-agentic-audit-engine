# Use a slim Python image for a smaller footprint
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 1. Copy requirements first to leverage Docker cache
COPY requirements.txt .

# 2. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy the rest of your application code
COPY . .

# 4. Permissions Hardening
# Ensure the SQLite database is writable within the container environment
RUN chmod 666 inventory.db

# 5. Expose ports
# 8000 for FastAPI Gateway
# 8501 for Streamlit UI
EXPOSE 8000
EXPOSE 8501

# 6. Healthcheck (Best practice for Cloud/HF deployments)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 7. Entrypoint
# We use a shell form to run both the API and UI simultaneously.
# In a true production environment, we might use a process manager like supervisord,
# but for this architectural demo, the & operator is efficient.
CMD uvicorn main:api --host 0.0.0.0 --port 8000 & streamlit run ui.py --server.port 8501 --server.address 0.0.0.0
