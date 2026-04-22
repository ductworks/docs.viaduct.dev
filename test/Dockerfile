# syntax=docker/dockerfile:1

# ── Stage 1: Build ────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jdk-noble AS builder

ARG SITE_URL=http://localhost:8080
ARG SOURCE_REF=main

ENV SITE_URL=${SITE_URL}
# Cap heap for container builds
ENV GRADLE_OPTS="-Xmx3g -XX:MaxMetaspaceSize=512m -Dfile.encoding=UTF-8 -Dkotlin.compiler.execution.strategy=in-process"

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Supports branches, tags, and full commit SHAs
RUN git init && \
    git remote add origin https://github.com/airbnb/viaduct && \
    git fetch --depth=1 origin ${SOURCE_REF} && \
    git checkout FETCH_HEAD

RUN --mount=type=cache,target=/root/.cache/pip \
    pip3 install -r docs/requirements.txt --break-system-packages

COPY overlays/ /workspace/

# Flatten docs/docs/docs/{developers,service_engineers,contributors} up one level
# so they build at /developers/, /service_engineers/, /contributors/ instead of /docs/*/
RUN cp -rn docs/docs/docs/developers docs/docs/docs/service_engineers docs/docs/docs/contributors docs/docs/

# Remove non-docs content so it is never built or indexed by search
RUN rm -rf docs/docs/about docs/docs/roadmap docs/docs/community docs/docs/blog

# MkDocs must run before Dokka — it cleans site/ before writing
RUN cd docs && mkdocs build

RUN --mount=type=cache,target=/root/.gradle \
    ./gradlew :core:tenant:tenant-api:dokkaGenerate :core:service:dokkaGenerate --no-daemon --max-workers=2 --quiet

# ── Stage 2: Static file server ───────────────────────────────────────────────
FROM golang:1.23-alpine AS server-builder
WORKDIR /build
COPY test/server.go .
RUN go mod init server && \
    CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o server .

# ── Stage 3: Serve (distroless) ───────────────────────────────────────────────
FROM gcr.io/distroless/static-debian12
COPY --from=server-builder /build/server /server
COPY --from=builder /workspace/docs/site /srv

HEALTHCHECK --interval=5s --timeout=3s --retries=3 CMD ["/server", "--health"]
EXPOSE 8080
ENTRYPOINT ["/server"]
