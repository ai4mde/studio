FROM oven/bun:1
WORKDIR /usr/src/app

COPY . /usr/src/app
RUN bun install --frozen-lockfile
ENTRYPOINT ["bun", "dev", "--host", "0.0.0.0"]