FROM python:3.12-slim-bookworm@sha256:541d45d3d675fb8197f534525a671e2f8d66c882b89491f9dda271f4f94dcd06

WORKDIR /opt

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY devicepasswords/ devicepasswords
COPY wordlist.txt .
COPY wordlist-de.txt .

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "-k", "uvicorn.workers.UvicornWorker", "devicepasswords:create_asgi()"]