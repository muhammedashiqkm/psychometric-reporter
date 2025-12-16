FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y --fix-missing \
    wkhtmltopdf \
    fonts-liberation \
    libxrender1 \
    libxext6 \
    libfontconfig1 \
    --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "3"]