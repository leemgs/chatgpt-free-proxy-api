FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y x11vnc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium

COPY . .

EXPOSE 8005

RUN chmod +x start.sh
CMD ["./start.sh"]
