FROM python:3.11-slim-bookworm as build

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get -y install gcc python3-dev libldap2-dev libsasl2-dev libmariadb-dev mariadb-client gettext-base pkg-config curl && \
    apt-get clean
RUN pip install --upgrade pip
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

COPY . .
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
