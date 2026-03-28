FROM python:3.12.8-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 9105

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
