FROM python:3.9-slim

WORKDIR /app

# Update pip
RUN pip install --upgrade pip

# Copy requirements.txt first for better caching
COPY requirements.txt .

# Install dependencies from requirements.txt
RUN pip install -r requirements.txt

# Copy application code
COPY . .

EXPOSE 5003

CMD ["python", "app.py"]