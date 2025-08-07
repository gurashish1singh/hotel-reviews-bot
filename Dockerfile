FROM python:3.11-slim

# Install Chrome dependencies and Chromium while removing unnecessary libs
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    chromium-driver chromium \
    fonts-liberation libasound2 libatk-bridge2.0-0 libnspr4 libnss3 libxss1 libx11-xcb1 xdg-utils curl unzip bash \
 && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Create workdir folder
WORKDIR /usr/app

# Copy and install requirements
COPY requirements.txt /usr/app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY main.py /usr/app/
COPY hotel_reviews_bot/ /usr/app/hotel_reviews_bot
COPY logger.py /usr/app/
COPY logging.yaml /usr/app/
