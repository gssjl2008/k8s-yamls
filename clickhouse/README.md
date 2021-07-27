# prometheus持久化存储到clickhouse

### 安装clickhouse
> 
```shell
kubectl apply -f clickhouse.yaml
```
需要将配置文件`config.xml`中添加内容
为了方便修改，先`docker`运行`clickhouse`，然后`/etc/clickhouse-server/`下面的内容拷贝到pvc中
```xml
    <graphite_rollup>
                <path_column_name>tags</path_column_name>
                <time_column_name>ts</time_column_name>
                <value_column_name>val</value_column_name>
                <version_column_name>updated</version_column_name>
                <default>
                        <function>avg</function>
                        <retention>
                                <age>0</age>
                                <precision>10</precision>
                        </retention>
                        <retention>
                                <age>86400</age>
                                <precision>30</precision>
                        </retention>
                        <retention>
                                <age>172800</age>
                                <precision>300</precision>
                        </retention>
                </default>
        </graphite_rollup>
```

### 安装prom2click
> 本文已经编译好。
https://github.com/iyacontrol/prom2click.git
```shell
kubectl apply -f prom2click.yaml
```

### 使用clickhouse-client来添加数据表
```sql
CREATE DATABASE IF NOT EXISTS metrics;
create table if not exists metrics.samples(date Date DEFAULT toDate(0),name String, tags Array(String),val Float64,ts DateTime,updated DateTime DEFAULT now())ENGINE=GraphiteMergeTree(date, (name, tags, ts), 8192, 'graphite_rollup');
```