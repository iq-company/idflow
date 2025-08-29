#
# conductor:server - Build Conductor Server
# ===========================================================================================================
ARG IMAGE_CONDUCTOR_SRC=conductor-src:latest
FROM ${IMAGE_CONDUCTOR_SRC} AS conductor-src

LABEL maintainer="service@get-iq.com"

# Build the server on run
RUN ./gradlew build -x test
WORKDIR /server/build/libs
RUN ls -ltr

