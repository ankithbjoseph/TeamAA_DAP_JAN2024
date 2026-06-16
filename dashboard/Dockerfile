FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY dashboard.py dashboard.py
COPY filtered_locations.csv filtered_locations.csv
COPY TeamAA.pdf TeamAA.pdf

RUN useradd -m appuser && chown -R appuser /app /opt/venv
USER appuser

EXPOSE 5006

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5006')" || exit 1

CMD ["panel", "serve", "dashboard.py", \
     "--address", "0.0.0.0", \
     "--port", "5006", \
     "--allow-websocket-origin=*"]
