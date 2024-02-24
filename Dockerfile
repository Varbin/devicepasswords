FROM python:3.12-slim-bookworm@sha256:5c73034c2bc151596ee0f1335610735162ee2b148816710706afec4757ad5b1e

WORKDIR /opt

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY devicepasswords/ devicepasswords
COPY wordlist.txt .
COPY wordlist-de.txt .

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "-k", "uvicorn.workers.UvicornWorker", "devicepasswords:create_asgi()"]