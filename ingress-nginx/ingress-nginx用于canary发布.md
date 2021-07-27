# ingress-nginx用于canary发布

> 如果想启用Canary功能，要先设置`nginx.ingress.kubernetes.io/canary: "true"`，然后可以启用以下注释来配置Canary

- `nginx.ingress.kubernetes.io/canary-weight` 请求到Canary ingress中指定的服务的请求百分比，值为0-100的整数，根据设置的值来决定大概有百分之多少的流量会分配Canary Ingress中指定的后端s服务
- `nginx.ingress.kubernetes.io/canary-by-header` 基于request header 的流量切分，适用于灰度发布或者A/B测试，当设定的hearder值为always是，请求流量会被一直分配到Canary入口，当hearder值被设置为never时，请求流量不会分配到Canary入口，对于其他hearder值，将忽略，并通过优先级将请求流量分配到其他规则
- `nginx.ingress.kubernetes.io/canary-by-header-value` 这个配置要和`nginx.ingress.kubernetes.io/canary-by-header` 一起使用，当请求中的hearder key和value 和`nginx.ingress.kubernetes.io/canary-by-header` `nginx.ingress.kubernetes.io/canary-by-header-value`匹配时，请求流量会被分配到Canary Ingress入口，对于其他任何hearder值，将忽略，并通过优先级将请求流量分配到其他规则
- `nginx.ingress.kubernetes.io/canary-by-cookie` 这个配置是基于cookie的流量切分，也适用于灰度发布或者A/B测试，当cookie值设置为always时，请求流量将被路由到Canary Ingress入口，当cookie值设置为never时，请求流量将不会路由到Canary入口，对于其他值，将忽略，并通过优先级将请求流量分配到其他规则

> 金丝雀规则按优先顺序进行如下排序：canary-by-header - > canary-by-cookie - > canary-weight

### 安装`flask`

```shell
pip install flask -i https://pypi.douban.com/simple
```

### 自建`python`项目用于展示

```python
from flask import Flask,request
import socket
from os import environ

'''
Use environ variable version to change version
'''

app=Flask(__name__)

@app.route("/")
def index():
    try:
        version = environ['version']
    except KeyError:
        version = 'v1'
    hostname = 'hostname: ' + socket.gethostname() + ', version: ' + version
    return hostname

if __name__ == '__main__':
    # must be 0.0.0.0, because default 127.0.0.1, can't access out of docker
    app.run(host="0.0.0.0")
```

### `Dockerfile`构建镜像

- 构建镜像

  ```dockerfile
  python:3.8-alpine
  
  WORKDIR /app
  
  EXPOSE 5000
  
  COPY app.py /app/app.py
  
  CMD ["python", "app.py"]
  ```

- 【可选】使用多阶段构建，打出的包比较小

  > 打包参考 [https://github.com/six8/pyinstaller-alpine](https://github.com/six8/pyinstaller-alpine)

  ```dockerfile
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
  ```

- 构建镜像

  ```shell
  docker build -t myapp .
  ```

  > ps.... 第一种快捷，第二种很慢。

### 使用`k8s`部署服务

#### 	基于权重的版本测试

- 部署`myapp1`

  ```yaml
  ---
  apiVersion: v1
  kind: Service
  metadata:
    name: myapp1
  spec:
    selector:
      app: myapp1
    ports:
    - port: 5000
      targetPort: 5000
  
  ---
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: myapp1
  spec:
    selector:
      matchLabels:
        app: myapp1
    template:
      metadata:
        labels:
          app: myapp1
      spec:
        containers:
        - name: myapp1
          image: gssjl2008/myapp
          imagePullPolicy: Always
          resources:
            limits:
              memory: "128Mi"
              cpu: "500m"
          env:
          - name: version
            value: v1
          ports:
          - containerPort: 5000
  
  ---
  apiVersion: extensions/v1beta1
  kind: Ingress
  metadata:
    name: myapp1-ingress
    annotations:
      kubernetes.io/ingress.class: "nginx"
  spec:
    rules:
    - host: myapp.cortex.com
      http:
        paths:
        - pathType: Prefix
          path: "/"
          backend:
            serviceName: myapp1
            servicePort: 5000
  ```

- 部署`myapp2`

  ```yaml
  ---
  apiVersion: v1
  kind: Service
  metadata:
    name: myapp2
  spec:
    selector:
      app: myapp2
    ports:
    - port: 5000
      targetPort: 5000
  
  ---
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: myapp2
  spec:
    selector:
      matchLabels:
        app: myapp2
    template:
      metadata:
        labels:
          app: myapp2
      spec:
        containers:
        - name: myapp2
          image: gssjl2008/myapp
          imagePullPolicy: Always
          resources:
            limits:
              memory: "128Mi"
              cpu: "500m"
          env:
          - name: version
            value: v2
          ports:
          - containerPort: 5000
  
  ---
  apiVersion: extensions/v1beta1
  kind: Ingress
  metadata:
    name: myapp2-ingress
    annotations:
      kubernetes.io/ingress.class: "nginx"
      nginx.ingress.kubernetes.io/canary: "true"					# 新增
      nginx.ingress.kubernetes.io/canary-weight: "50"			# 新增 ，要不然无法创建ingres
  spec:
    rules:
    - host: myapp.cortex.com
      http:
        paths:
        - pathType: Prefix
          path: "/"
          backend:
            serviceName: myapp2
            servicePort: 5000
  ```

- 配置本地`hosts`文件

  ```shell
  192.168.50.181	myapp.cortex.com
  ```

- 测试访问

  ```shell
  while 1
  do
      curl myapp.cortex.com:30000						# ingress配置30000端口
      sleep 1
  done
  ```

  可观察结果，

  ```shell
  hostname: myapp2-69f5cb7657-dk4gj, version: v2
  hostname: myapp1-6754dcdc76-qr4bb, version: v1
  ...
  ```

  权重设置为50，服务出现比例无限接近50%。

#### 基于`header`的A/B测试

- 修改`myapp2`文件中`ingress`部分

  > 增加 nginx.ingress.kubernetes.io/canary-by-header: "cortex"   # 引号内名称随意

- 修改生效

  ```shell
  kubectl apply -f myapp2.yaml
  ```

- 验证，请求时，添加`cortex`到`header`中

  - `always`

    > 此时流量全部接入到v2中

    ```shell
    while 1                          
    do
    curl -H "cortex:always" myapp.cortex.com:30000;sleep 1
    done
    hostname: myapp2-69f5cb7657-dk4gj, version: v2
    hostname: myapp2-69f5cb7657-dk4gj, version: v2
    hostname: myapp2-69f5cb7657-dk4gj, version: v2
    ...
    ```

  - `never`

    > 此时流量全部接入到v1中

    ```shell
    while 1                          
    do
    curl -H "cortex:never" myapp.cortex.com:30000;sleep 1
    done
    hostname: myapp1-6754dcdc76-qr4bb, version: v1
    hostname: myapp1-6754dcdc76-qr4bb, version: v1
    hostname: myapp1-6754dcdc76-qr4bb, version: v1
    ...
    ```

  - 其他任意值，

    > 则会按照默认策略走，即按照权重50来分配流量。

  - 最后，如果要设置自定义值进行流量分配，可以添加

    ```yaml
    nginx.ingress.kubernetes.io/canary-by-header-value: "all"
    ```

  - 再次测试

    > 测试, `always`和`never`只会按照默认策略走，只有设置为`all`到时候，流量全部给`v2`，

    ```shell
    while 1                          
    do
    curl -H "cortex:all" myapp.cortex.com:30000;sleep 1
    done
    ~/Documents/k8s系列/ingress-nginx
    hostname: myapp2-69f5cb7657-dk4gj, version: v2
    hostname: myapp2-69f5cb7657-dk4gj, version: v2
    hostname: myapp2-69f5cb7657-dk4gj, version: v2
    ```

    

    

  

  

  

  

  

  

  

  