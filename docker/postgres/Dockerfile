FROM postgres:16-alpine

LABEL maintenance="Security Engineering" \
      patch_date="2026-06-01" \
      component="database"

# Physically rip out the Go binary and substitute it with native alpine su-exec
RUN set -ex; \
    apk update; \
    apk upgrade --no-cache libxml2; \
    apk add --no-cache su-exec; \
    rm -rf /usr/local/bin/gosu; \
    rm -rf /var/cache/apk/*

# Patch the entrypoint invocation sequence dynamically inside the image layer
RUN set -ex; \
    sed -i 's/exec gosu /exec su-exec /g' /usr/local/bin/docker-entrypoint.sh; \
    sed -i 's/gosu /su-exec /g' /usr/local/bin/docker-entrypoint.sh