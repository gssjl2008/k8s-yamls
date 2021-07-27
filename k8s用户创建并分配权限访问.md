# 创建`k8s Account`

- 创建私钥

  > 要求权限是600

  ```shell
  umask 077; openssl genrsa -out tom.key 2048
  ```

- 创建证书签署请求

  > /O 组织
  >
  > /CN 账户

  ```bash
  openssl req -new -key tom.key -out tom.csr -subj "/O=nb/CN=tom"
  ```

- 签署证书

  > 需要使用`k8s`的`ca.crt, ca.key`用来签署

  ```shell
  openssl x509 -req -in tom.csr -CA /etc/kubernetes/pki/ca.crt -CAkey /etc/kubernetes/pki/ca.key -CAcreateserial -out tom.crt -days 3650
  ```

- 创建集群配置

  > --embed-certs=true.  作用是不在配置文件中显示证书信息。
  >
  > --kubeconfig=tom.json	生成指定配置文件，如不指定，则默认 ~/.kube/config， 会覆盖原有的配置文件

  ```shell
  kubectl config set-cluster tom-cluster --server=https://192.168.50.180:16443 --certificate-authority=/etc/kubernetes/pki/ca.crt --embed-certs=true --kubeconfig=tom.conf
  
  # 可通过命令查看
  kubectl config view --kubeconfig=tom.conf
  ```

- 创建用户配置

  > 添加`tom`到配置中

  ```shell
  kubectl config set-credentials tom --client-certificate=tom.crt --client-key=tom.key --embed-certs=true --kubeconfig=/root/user-for-k8s/tom.conf
  ```

- 创建上下文

  ```shell
  kubectl config set-context tom@tom-cluster --cluster=tom-cluster --user=tom --kubeconfig=/root/user-for-k8s/tom.conf
  ```

- 切换上下文

  > 必须

  ```shell
  kubectl config use-context tom@tom-cluster --kubeconfig=/root/user-for-k8s/tom.conf
  ```

  

- 创建系统用户`tom`

  ```shell
  useradd tom
  mkdir /home/tom/.kube
  cp tom.conf /home/tom/.kube/config
  chown -R tom.tom /home/tom/
  ```

- 切换到用户`tom`

  ```shell
  su - tom
  kubectl get pod  # 提示没有没有权限
  ```

- 创建角色`pod-reader`

  ```yaml
  # kubectl create role pod-reader --verb=get,list,watch --resource=pods  -o yaml --dry-run=client
  apiVersion: rbac.authorization.k8s.io/v1
  kind: Role
  metadata:
    creationTimestamp: null
    name: pod-reader
  rules:
  - apiGroups:
    - ""
    resources:
    - pods
    verbs:
    - get
    - list
    - watch
  ```

- 创建用户绑定

  ```yaml
  # kubectl create rolebinding tom-pod-reader --role=pod-reader --user=tom --dry-run=client -o yaml
  apiVersion: rbac.authorization.k8s.io/v1
  kind: RoleBinding
  metadata:
    creationTimestamp: null
    name: tom-pod-reader
  roleRef:
    apiGroup: rbac.authorization.k8s.io
    kind: Role
    name: pod-reader
  subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: tom
  ```

- 再次使用`tom`进行访问，可正常访问默认`default`到命名空间了

  ```bash
  [tom@node01 ~]$ kubectl get pod
  NAME                                      READY   STATUS    RESTARTS   AGE
  box                                       1/1     Running   150        3d3h
  nexus-75cdd74585-2pxzk                    1/1     Running   0          3h48m
  nfs-client-provisioner-7458cf8f97-nvkzj   1/1     Running   2          3d3h
  
  [tom@node01 ~]$ kubectl get pod -A
  Error from server (Forbidden): pods is forbidden: User "tom" cannot list resource "pods" in API group "" at the cluster scope
  ```

- 创建集群角色

  ```yaml
  # kubectl create clusterrole cluster-pod-reader --verb=get,list,watch --resource=pods --dry-run=client -o yaml
  apiVersion: rbac.authorization.k8s.io/v1
  kind: ClusterRole
  metadata:
    creationTimestamp: null
    name: cluster-pod-reader
  rules:
  - apiGroups:
    - ""
    resources:
    - pods
    verbs:
    - get
    - list
    - watch
  ```

- 绑定集群角色

  ```yaml
  kubectl create clusterrolebinding tom-cluster-pod-reader --clusterrole=cluster-pod-reader --user=tom --dry-run=client -o yaml
  apiVersion: rbac.authorization.k8s.io/v1
  kind: ClusterRoleBinding
  metadata:
    creationTimestamp: null
    name: tom-cluster-pod-reader
  roleRef:
    apiGroup: rbac.authorization.k8s.io
    kind: ClusterRole
    name: cluster-pod-reader
  subjects:
  - apiGroup: rbac.authorization.k8s.io
    kind: User
    name: tom
  ```

- 再次测试即可

  ```shell
  [tom@node01 ~]$ kubectl get pod -A
  NAMESPACE     NAME                                      READY   STATUS    RESTARTS   AGE
  default       box                                       1/1     Running   150        3d3h
  default       nexus-75cdd74585-2pxzk                    1/1     Running   0          3h57m
  default       nfs-client-provisioner-7458cf8f97-nvkzj   1/1     Running   2          3d3h
  kube-system   calico-kube-controllers-7d569d95-7vqmn    1/1     Running   0          4d3h
  kube-system   calico-node-9dw82                         1/1     Running   0          4d3h
  kube-system   calico-node-pxcqn                         1/1     Running   0          4d3h
  kube-system   calico-node-qwhrs                         1/1     Running   0          4d3h
  ...
  ```

  

