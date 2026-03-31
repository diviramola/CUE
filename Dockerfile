FROM python:3.11-slim

# Install ffmpeg for video frame extraction
RUN apt-get update && apt-get install -y ffmpeg --no-install-recommends && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# App root — data (library, docs, output) lives here
ENV CUE_DATA_DIR=/app

EXPOSE 8080

CMD ["python", "src/webapp.py"]
