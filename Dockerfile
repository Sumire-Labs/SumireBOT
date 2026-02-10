# SumireBot v2 - Discord Bot Container
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY bot.py .
COPY cogs/ ./cogs/
COPY utils/ ./utils/
COPY views/ ./views/

# Create directories for mounted volumes
RUN mkdir -p /app/database /app/logs

# Run the bot
CMD ["python", "bot.py"]
