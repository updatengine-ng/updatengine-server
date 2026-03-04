FROM python:3.12-slim-bookworm AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get -y install --no-install-recommends \
        gcc python3-dev libldap2-dev libsasl2-dev libmariadb-dev pkg-config && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt .
RUN pip install pip --upgrade && \
    pip install --no-cache-dir -r requirements.txt


FROM python:3.12-slim-bookworm AS final
WORKDIR /app

RUN apt-get update && \
    apt-get -y install --no-install-recommends gettext-base mariadb-client curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY . .
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
