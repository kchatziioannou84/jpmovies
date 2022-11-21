FROM python:3.10.8-slim@sha256:14f47505ae036cc75cdefbfd4c734682c0411b4109bc0419db0f17f8a8624f66

WORKDIR /app

RUN groupadd -g 999 app && useradd -r -u 999 -g app app

RUN python3 -m venv /app/venv

COPY requirements/base.txt requirements.txt

RUN /app/venv/bin/pip install -r requirements.txt

COPY jpmovies ./jpmovies

USER 999

ENTRYPOINT [ "/app/venv/bin/gunicorn",  "--bind", "0.0.0.0:8080", "jpmovies.api:app" ]
