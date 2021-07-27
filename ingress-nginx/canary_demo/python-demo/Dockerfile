ARG ARCH=""
ARG ALPINE_VERSION="3.8"

FROM ${ARCH}python:${ALPINE_VERSION}-alpine as builder

ARG PYINSTALLER_TAG
ENV PYINSTALLER_TAG ${PYINSTALLER_TAG:-"v3.6"}

# Official Python base image is needed or some applications will segfault.
# PyInstaller needs zlib-dev, gcc, libc-dev, and musl-dev
RUN apk --update --no-cache add \
    zlib-dev \
    musl-dev \
    libc-dev \
    libffi-dev \
    gcc \
    g++ \
    git \
    pwgen \
    && pip install --upgrade pip

# Install pycrypto so --key can be used with PyInstaller
RUN pip install \
    pycrypto \
    flask -i https://pypi.douban.com/simple

# Build bootloader for alpine
RUN git clone --depth 1 --single-branch --branch ${PYINSTALLER_TAG} https://github.com/pyinstaller/pyinstaller.git /tmp/pyinstaller \
    && cd /tmp/pyinstaller/bootloader \
    && CFLAGS="-Wno-stringop-overflow -Wno-stringop-truncation" python ./waf configure --no-lsb all \
    && pip install .. \
    && rm -Rf /tmp/pyinstaller

COPY app.py /app/app.py

WORKDIR /app

RUN pyinstaller -F app.py

# FROM gssjl2008/py3-alpine

FROM alpine

WORKDIR /app

EXPOSE 5000

COPY --from=builder /app/dist/app .

CMD [ "./app" ]