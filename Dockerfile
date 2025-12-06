FROM python:3.11-slim

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /main
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .

CMD ["dagster-webserver", "-h", "0.0.0.0", "-f", "extract_transform_load.py"]