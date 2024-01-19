FROM python:3.12-slim-bookworm

WORKDIR /opt

ENV CLASS="gevent"
ENV WORKERS="4"

COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY devicepasswords/ devicepasswords
COPY wordlist.txt .
COPY wordlist-de.txt .

ENTRYPOINT ["gunicorn", "-b", "0.0.0.0:8000", "-k", "${CLASS}", "-w", "${WORKERS}", "devicepasswords:create_app()"]