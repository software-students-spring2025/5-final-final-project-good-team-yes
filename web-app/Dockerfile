FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

# Install pipenv
RUN pip install --upgrade pip && pip install pipenv

RUN pip install --trusted-host pypi.python.org -r requirements.txt

EXPOSE 5003

CMD ["python", "app.py"]