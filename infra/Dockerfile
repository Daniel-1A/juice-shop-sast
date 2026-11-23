FROM node:24-bookworm@sha256:9d266751ca3d7fdbe651c878ffd5ad0a42fed49a18c283509267c97f025b7496 AS installer
WORKDIR /juice-shop
ENV CYPRESS_INSTALL_BINARY=0
COPY . .
RUN npm install --include=dev --no-audit --no-fund \
    && npm run build:server \
    && npm run sbom \
    && npm prune --omit=dev --ignore-scripts \
    && npm dedupe --omit=dev --ignore-scripts \
    && rm -rf frontend/node_modules frontend/.angular frontend/src/assets \
    && mkdir -p logs \
    && rm -f ftp/legal.md i18n/*.json \
    && chown -R 65532:65532 logs data ftp uploads i18n frontend/dist

FROM gcr.io/distroless/nodejs24-debian13:nonroot@sha256:39b0407357c9fadf1a9708d22088f02de21f0e1e8a688474eea2d8701e7d5693
ARG BUILD_DATE
ARG VCS_REF
LABEL org.opencontainers.image.title="OWASP Juice Shop - laboratorio SSDLC" \
    org.opencontainers.image.version="20.3.0" \
    org.opencontainers.image.licenses="MIT" \
    org.opencontainers.image.revision=$VCS_REF \
    org.opencontainers.image.created=$BUILD_DATE
WORKDIR /juice-shop
COPY --from=installer --chown=65532:65532 /juice-shop .
USER 65532:65532
EXPOSE 3000
HEALTHCHECK --interval=15s --timeout=5s --start-period=120s --retries=5 \
    CMD ["/nodejs/bin/node", "-e", "require('node:http').get('http://127.0.0.1:3000/', r => { r.resume(); process.exit(r.statusCode === 200 ? 0 : 1) }).on('error', () => process.exit(1))"]
CMD ["/juice-shop/build/app.js"]
