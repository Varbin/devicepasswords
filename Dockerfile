FROM python:3.12-slim-bookworm@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63

WORKDIR /opt

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY devicepasswords/ devicepasswords
COPY wordlist.txt .
COPY wordlist-de.txt .

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "-k", "uvicorn.workers.UvicornWorker", "devicepasswords:create_asgi()"]