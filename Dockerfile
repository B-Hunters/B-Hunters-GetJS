# The getJS tool cannot be installed with `go install`:
#
#   * the module path contains upper case letters, which the Go module
#     proxy rejects, and the `!` escape that the proxy protocol uses is
#     not accepted by `go install`;
#   * the v1.0.0 tag predates Go modules, so the repository has no
#     go.mod and the dependencies have to be resolved at build time.
#
# The tool is therefore built from a pinned source revision, with the
# module initialised in the build.
FROM golang:1.26-bookworm AS build
ARG GETJS_TAG=v1.0.0
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
RUN git clone --depth 1 --branch ${GETJS_TAG} https://github.com/003random/getJS.git . \
 && rm -rf .git \
 && (test -f go.mod || go mod init github.com/003random/getJS) \
 && go mod tidy \
 && CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/getJS .

FROM python:3.12-slim
COPY --from=build /out/getJS /usr/local/bin/getJS
RUN apt update && apt install -y git && apt clean && rm -rf /var/lib/apt/lists/*
# The shared class is built from this repository, not from the published
# release: a worker that calls auth_headers(task) against a release that
# does not have it fails inside the scan.  scripts/build_workers.sh passes
# the local wheel; the default is the published release.
ARG B_HUNTERS_WHEEL=b-hunters==1.2.0
RUN pip install --no-cache-dir ${B_HUNTERS_WHEEL}
ENV PATH="$PATH:/usr/local/go/bin:/root/go/bin:/usr/local/bin"
WORKDIR /app/service
COPY getjs /app/service/getjs
CMD ["python3", "-m", "getjs"]
