FROM python:3.14.7-slim-trixie AS build
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


FROM node:alpine AS nodejs
WORKDIR /nodejs
COPY package.json .
COPY ./updatengine/templates ./updatengine/templates
COPY ./static_modern/src ./static_modern/src
RUN npm install
RUN npm run build


FROM python:3.14.7-slim-trixie AS final
WORKDIR /app
RUN apt-get update && \
    apt-get -y install --no-install-recommends gettext-base mariadb-client curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY --from=build /opt/venv /opt/venv
COPY . .
COPY --from=nodejs /nodejs/updatengine/files/modern-ui ./updatengine/files/modern-ui
ENV PATH="/opt/venv/bin:$PATH"
RUN chmod +x ./entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
