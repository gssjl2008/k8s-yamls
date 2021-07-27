#### 什么是StorageClass

> 动态的根据服务需求创建存储大小，而不用提前创建，省时省力

#### 为什么需要StorageClass

> 因为懒...

#### 前置条件

1. 已创建`NFS Server`；
2. 已搭建完`K8s`集群；
3. 所有`k8s`节点上安装`nfs-utils`包；

#### 背景

> k8s本身不支持`nfs`作为`StorageClass`，所以需要外部插件([插件](https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner/))来支持，

####  大致步骤如下：

1. 创建`ServiceAccount`用于管控`NFS provisioner`在集群中的权限；
2. 创建`Deployment`，有两个功能,一个是在NFS共享目录下创建挂载点(volume),另一个则是建了PV并将PV与NFS的挂载点建立关联
3. 创建`StorageClass`用于建立`PVC`，并调用`provisioner`进行工作，使`PV`和`PVC`建立管理；

> Ps...看着一大堆英文，其实简单使用的话，就只需要修改下`Deployment`中的`NFS_SERVER`和`NFS_PATH`即可。

 #### 具体操作

- ##### 克隆仓库

  ```shell
  git clone https://github.com/kubernetes-sigs/nfs-subdir-external-provisioner.git
  ```

  > Ps...其实只需要这个仓库下面`deploy/rbac.yaml,deployment.yaml,class.yaml`这3个文件

- 创建`rbac`

  ```
  kubectl apply -f rbac.yaml
  ```

- 修改`deploy/deployment.yaml`文件

  > 这是我修改之后的文件

  ```yaml
  apiVersion: apps/v1
  kind: Deployment
  metadata:
    name: nfs-client-provisioner
    labels:
      app: nfs-client-provisioner
    # replace with namespace where provisioner is deployed
    namespace: default							# 根据实际情况修改
  spec:
    replicas: 1
    strategy:
      type: Recreate
    selector:
      matchLabels:
        app: nfs-client-provisioner
    template:
      metadata:
        labels:
          app: nfs-client-provisioner
      spec:
        nodeName: node01
        serviceAccountName: nfs-client-provisioner
        containers:
          - name: nfs-client-provisioner
            image: quay.io/external_storage/nfs-client-provisioner:latest
            volumeMounts:
              - name: nfs-client-root
                mountPath: /persistentvolumes									# 此处不建议修改
            env:
              - name: PROVISIONER_NAME
                value: fuseim.pri/ifs													# 此处必须与class一致，可修改
              - name: NFS_SERVER
                value: 192.168.50.101													# 必须修改
              - name: NFS_PATH
                value: /data/k8s															# 必须修改
        volumes:
          - name: nfs-client-root
            nfs:
              server: 192.168.50.101													# 必须修改
              path: /data/k8s																	# 必须修改
  ```

  修改完即可创建

  ```shell
  kubectl apply -f deployment.yaml
  ```

- 创建`StorageClass`

  > 如果有一些非必须项目修改了， 下面这个文件也需要修改与之对应

  ```shell
  kubectl apply -f class.yaml
  ```

  