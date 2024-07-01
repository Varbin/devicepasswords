FROM python:3.12-slim-bookworm@sha256:da2d7af143dab7cd5b0d5a5c9545fe14e67fc24c394fcf1cf15e8ea16cbd8637

WORKDIR /opt

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY devicepasswords/ devicepasswords
COPY wordlist.txt .
COPY wordlist-de.txt .

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:5000", "-k", "uvicorn.workers.UvicornWorker", "devicepasswords:create_asgi()"]