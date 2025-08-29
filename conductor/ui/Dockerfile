#
# conductor:server - Build Conductor UI
# ===========================================================================================================
ARG IMAGE_CONDUCTOR_SRC=conductor-src:latest
FROM ${IMAGE_CONDUCTOR_SRC} AS conductor-src

FROM alpine:3.20 AS ui-builder
ARG YARN_OPTS

LABEL maintainer="service@get-iq.com"

# Install dependencies
RUN apk add --update nodejs npm yarn

COPY --from=conductor-src /src/conductor /conductor
WORKDIR /conductor/ui

# Include monaco sources into bundle (instead of using CDN)
ENV REACT_APP_MONACO_EDITOR_USING_CDN=false
ENV REACT_APP_ENABLE_ERRORS_INSPECTOR=true
RUN yarn ${YARN_OPTS} install && cp -r node_modules/monaco-editor public/ && yarn ${YARN_OPTS} build
RUN ls -ltr
RUN echo "Done building UI"

