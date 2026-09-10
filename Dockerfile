# Use the official lightweight Python image
FROM python:3.14-slim
# Create a non‑root user (good practice)
RUN adduser --disabled-password appuser
WORKDIR /app
# Copy source code
COPY . /app
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Expose the port FastAPI will listen on
EXPOSE 8000
# Run the server (Render supplies , we fall back to 8000 for local runs)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
