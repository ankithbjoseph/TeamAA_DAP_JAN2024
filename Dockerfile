FROM python:3.11-slim as base

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /main
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

FROM base as dagster
CMD ["dagster-webserver", "-h", "0.0.0.0", "-f", "extract_transform_load.py"]

FROM base as dagster_daemon
CMD ["dagster-daemon", "run"]