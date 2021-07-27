FROM gssjl2008/py3-alpine:latest

# 标签说明
# docker rmi django-py3-nginx-alpine:latest || echo "not"  && docker build -t django-py3-nginx-alpine:latest -f ./Dockerfile .
# docker tag django-py3-nginx-alpine:latest gssjl2008/django-py3-nginx-alpine:latest
# docker push gssjl2008/django-py3-nginx-alpine:latest
LABEL author="wx" email="gssjl2004@126.com" desc="python3.8+nginx+uwsgi+Django3镜像，用于pages项目"

ADD requirements.txt /requirements.txt

# 更新软件
RUN apk add --update --upgrade && \
    apk add --no-cache nginx jpeg-dev zlib-dev linux-headers musl-dev gcc python3-dev mysql-dev && \
    pip3 install --no-cache-dir --upgrade pip && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    rm /etc/nginx/conf.d/default.conf && \
    pip install --no-cache-dir -r /requirements.txt && \
    rm -rf /requirements.txt
