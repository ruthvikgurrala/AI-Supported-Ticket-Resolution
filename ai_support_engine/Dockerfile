
# ---------------------------------------------------
# Backend Dockerfile for Owntrail (FastAPI)
# ---------------------------------------------------

# 1. Base Image: Use an official lightweight Python image
FROM python:3.10-slim

# 2. Work Directory: Set the internal folder where code lives
WORKDIR /app

# 3. Dependencies: Copy requirements first (for caching speed)
#    We assume the Dockerfile is inside 'ai_support_engine' folder context
COPY requirements.txt .

# 4. Install Libraries
#    --no-cache-dir keeps the image smaller
RUN pip install --no-cache-dir -r requirements.txt

# 5. Fix Imports: content is in /app/src, so let Python find it
ENV PYTHONPATH="${PYTHONPATH}:/app/src"

# 6. Copy Code: Move your source code into the container
COPY . .

# 6. Expose Port: Tell Docker this app speaks on port 8000
EXPOSE 8000

# 7. Command: What to run when the container starts
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
