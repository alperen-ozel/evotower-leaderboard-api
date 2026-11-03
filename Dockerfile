FROM python:3.12-slim

WORKDIR /app

# Install dependencies first so Docker can cache this layer between code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py service.py repository.py ./

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
