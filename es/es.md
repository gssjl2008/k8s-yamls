---
tags:
  - es
  - elasticsearch
  - k8s
---

/

# Yaml 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: es-deployment
  labels:
    app: elasticsearch
spec:
  replicas: 1  # 单节点模式
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
      - name: elasticsearch
        image: docker.elastic.co/elasticsearch/elasticsearch:7.16.3
        env:
        - name: ES_JAVA_OPTS
          value: "-Xms1g -Xmx4g -Des.ingest.geoip.downloader.enabled=false"
        - name: discovery.type
          value: "single-node"
```