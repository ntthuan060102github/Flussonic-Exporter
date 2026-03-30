FROM python:3.12.8-slim

WORKDIR /app

RUN useradd --create-home --no-log-init --uid 1000 --shell /usr/sbin/nologin exporter

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flussonic_exporter ./flussonic_exporter
COPY main.py .
RUN chown -R exporter:exporter /app

USER exporter

EXPOSE 9105

ENV PYTHONUNBUFFERED=1

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:9105/healthz', timeout=4)"

CMD ["python", "-m", "flussonic_exporter"]
