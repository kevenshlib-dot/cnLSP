# cnLSP 第三阶段部署记录 —— 流通链（circulation chain）

日期：2026-09-20
基线：app-platform-minimal 0.0.19（19 个后端模块，第二阶段编目链完成态）
目标：部署 FOLIO 流通链全部核心模块，验证中文流通规则端到端（PoC-3）。

## 1. 阶段目标与范围

以官方 platform-complete R1-2025（Ramsons CSP）的 install.json 为版本基准，
通过接口依赖闭包分析（`poc/circ-deps.py`）确定流通链最小集 **15 个模块**，
闭包零缺口：

| 模块 | 版本 | 说明 |
|---|---|---|
| mod-circulation | 24.4.20 | 流通核心（借还、规则引擎、逾期计算） |
| mod-circulation-storage | 17.4.3 | 借期/通知/请求政策、流通规则、loan 存储 |
| mod-feesfines | 19.3.3 | 费用/罚款账户、逾期/赔偿政策（注意：overdue/lost-item 政策 API 在本模块，不在 circulation-storage） |
| mod-patron-blocks | 1.12.3 | 读者封禁（自动封禁条件） |
| mod-patron | 6.3.6 | 读者自助（我的账户） |
| mod-notify | 3.4.1 | 站内通知 |
| mod-sender | 1.14.2 | 通知投递 |
| mod-email | 1.19.1 | 邮件发送（SMTP） |
| mod-template-engine | 1.22.2 | 通知模板 |
| mod-calendar | 3.3.1 | 开馆日历（影响到期日计算，Spring Boot） |
| mod-pubsub | 2.16.3 | 发布订阅事件总线（Spring 校验 + RMB 混合） |
| mod-audit | 2.11.5 | 审计日志 |
| mod-inventory | 21.1.20 | inventory 业务层（检索聚合等） |
| mod-event-config | 2.9.1 | mod-event 接口兜底（mod-notify 依赖） |
| mod-batch-print | 1.3.0 | batch-print 接口兜底（mod-sender 依赖） |

应用描述符升至 **app-platform-minimal 0.0.20（34 个后端模块）**。

## 2. 执行过程与关键坑

### 2.1 镜像构建（全部无官方 ARM64，本地构建）

- 15 个模块全部为 RMB/Vert.x（仅 mod-calendar/mod-pubsub 内嵌 Spring 组件），
  均用 `misc/images-builder/build.sh` 构建。
- **build.sh 两处修补（已落盘）**：
  1. `git clone` 加 `--recurse-submodules --shallow-submodules`
     （13/15 模块带 raml-utilities 子模块，不拉子模块则 RAML 生成失败）；
  2. mvn 加 `-Dcheckstyle.skip=true -Ddocker.skip=true`
     （防 docker-maven-plugin 在无 Docker daemon 上下文中 gson NPE）。
- 并行 8 路构建时 GitHub 网络抖动导致 2 个模块 clone 失败，改 NUM_JOBS=2 补建。

### 2.2 端口规划修正（重要）

- 初次扩展给新模块分配 29020-29034，**与存量 mod-scheduler 的 29020 冲突**
  （二阶段 19 个模块实际用到 29020）。已将 15 个新模块整体移至：
  - 模块 HTTP **29035-29049**，调试 **10035-10049**；
  - sidecar HTTP **19035-19049**，调试 **11035-11049**。
- 教训：扩展前先 `grep -oE '"29[0-9]{3}:8081"' compose 文件 | sort -u` 核对占用。

### 2.3 私有端口（官方 private-port）

**mod-circulation 监听 9801、mod-inventory 监听 9403**（非默认 8081），
这是官方 eureka-cli `config.combined.yaml` 中标注的 `private-port`。
症状：模块日志正常、verticle 全部署，但 8081 无监听，健康检查永远失败。
解法（已落盘 compose）：
- 模块侧：ports 改为 `29036:9801` / `29047:9403`，healthcheck 端口同步改；
- sidecar 侧：`MODULE_URL` 改为 `http://mod-circulation:9801` / `http://mod-inventory:9403`。

### 2.4 mod-pubsub 系统用户配置

- 症状：mod-pubsub 启动即退出（exit 0），
  `SystemUserConfig validateCredentials: username is blank`。
- 查证：官方 eureka-cli 对 mod-pubsub 标 `disable-system-user: true`，
  对应 env（`moduleenv/module_env.go DisabledSystemUserEnv`）：
  ```
  FOLIO_SYSTEM_USER_ENABLED=false
  SYSTEM_USER_CREATE=false
  SYSTEM_USER_ENABLED=false
  SYSTEM_USER_NAME=mod-pubsub
  SYSTEM_USER_USERNAME=mod-pubsub
  ```
  已加入 compose，模块随即 healthy。

### 2.5 Kafka fenced / 分区无 leader（本阶段最大坑）

- 背景：前一天重启 Docker 后，单节点 KRaft Kafka 的 broker 一直停在
  `Waiting for the broker to be unfenced`——容器健康检查通过但**不接受任何新
  topic 创建**（`INVALID_REPLICATION_FACTOR: All brokers are currently fenced`）。
- 这导致 PUT 授权连续失败（各模块租户初始化要建 topic/发事件）：
  - 第 1 次：mod-patron-blocks PubSub 注册 408 + mod-inventory createTopics 超时；
  - 后续：mgr-tenant-entitlements 向
    `folio.diku.mgr-tenant-entitlements.scheduled-job` / `.capability`
    发事件报 `NotLeaderOrFollowerException`（分区无 leader）。
- **同时 keycloak-s0 被 OOMKill（exit 137，原内存上限 1200m）**，令牌端点 502，
  nginx 代理还缓存了旧上游 IP，需 `docker restart keycloak`（nginx）刷新。
- 解法：
  1. `docker restart kafka` 触发重新注册与分区选主（恢复有延迟，需等 2-3 分钟）；
  2. keycloak-s0 compose 内存上限 **1200m → 2048m**（已落盘）；
  3. 停掉本机其他项目容器（scholarguard、ai-literacy，经用户同意）降低负载；
  4. 重试 PUT → **200 成功**。
- 排查工具：kafka-native 镜像无 CLI，用一次性工具容器：
  `docker run --rm --network folio-platform-minimal apache/kafka:4.3.1
   /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic ...`

### 2.6 mod-calendar OOM

PoC-3 借出时 mod-circulation 调 `/calendar/dates/{sp}/surrounding-openings`，
mod-calendar 在处理请求时被 OOMKill（384m 不够）。compose 提至 **640m** 后稳定。

### 2.7 Kong 上游 IP 陈旧

sidecar 重启后 IP 变化，Kong（api-gateway）仍按旧 IP 转发 →
`/groups`、`/users` 全部 502（`invalid response received from upstream`），
直连模块（29001）正常。`docker restart api-gateway` 即恢复。
（与二阶段 keycloak nginx 的问题同类。）

## 3. 授权升级结果

- 描述符 0.0.20 注册：201；15 条新 discovery 注册：201
  （注意：discovery 批量 POST 遇已有条目 409 整体跳过，必须只提交新增部分）。
- PUT /entitlements → app-platform-minimal-0.0.20：**200**。
  升级后 `entitlement_module` 表 34 行一致（升级前已备份
  `eureka-platform-bootstrap/backups/backup-pre-0.0.20.sql`）。
- `poc/load-permissions.py`：15 个新模块 permissionSets 全部灌入（34/34 成功）。
- `misc/create-user.sh folio folio`：capabilities **647 → 1113**，
  capability sets 90，登录验证 1178 权限。

## 4. PoC-3：中文流通规则端到端（poc/poc3-circulation-e2e.py）✅ 全部通过

1. 读者类型：`本科生`（中文名，存储/展示）+ `undergrad`（ASCII 代码，规则引用）
2. 中文流通政策五个：借期[中文图书30天]、通知[中文默认]、请求[允许预约与递送]、
   逾期[中文图书逾期每天0.1元]、赔偿[中文图书赔偿按原价+10元加工费]
3. 费款主体[总馆流通台]（绑定服务点）+ 费款类型[Overdue fine]
4. 流通规则：`m cn-book + g undergrad → 中文政策组`（含 fallback-policy）
5. 读者：张三（barcode R20260001，读者类型 undergrad）
6. 册：CN20260001，挂 PoC-2 的 CLC holdings（索书号 G250.76），
   material type cn-book，借阅类型 普通外借
7. check-out-by-barcode：成功，到期日 = 30 天后 23:59:59（规则命中）
8. 到期日改 3 天前 → check-in：loan Closed/action=checkedin
9. 逾期费账单生成：**Overdue fine 4.0 Open**（feesfines 结算正常）

### 4.1 PoC-3 暴露的本土化要点

- **【重大】流通规则 DSL 不支持中文名**：mod-circulation 的 ANTLR 文法
  `CirculationRules.g4` 中 `NAME: [0-9a-zA-Z-]+` —— 规则条件（读者类型/资料类型/
  馆藏地点等）只能用 ASCII 字母数字连字符。中文名写入报 `Name missing`。
  → 本土馆配置惯例：规则引用的参考数据用 ASCII 代码名（pinyin/编码），
  中文显示名放 desc；政策名可为中文（规则内按 UUID 引用）。
  → **本土化改造项**：cnLSP 后续应将 NAME 词法扩展到 Unicode
  （如 `[\p{L}\p{N}\-_]+`）并重构建 mod-circulation。
- 逾期政策 `overdueFine.intervalId` 枚举是小写 `day/hour/minute/week/month/year`
  （与通用 interval.json 的 `Days` 等**不同**，且 GitHub 该版本 ramls 目录缺失
  overdue schema，以 jar 内类为准）。
- 逾期费结算前置参考数据：费款主体（/owners，需绑定服务点）+ 费款类型
  （/feefines，`Overdue fine`）。无主体时 mod-circulation 日志
  `createAccount:: params are incomplete`，静默不生成账单。
- loan policy 必填 `renewable`；gracePeriod duration 不允许 0（≥1 或省略）。
- 逾期费按逾期天数 × overdueFine.quantity 计（验证值 4.0 = 1.0/天 × 4 天，
  起算日含当天取整，语义待精确核对）。

## 5. 新增技术债务 / 遗留问题

1. **流通规则文法 ASCII 限制**（§4.1）：本土化核心改造项，需 patch
   mod-circulation 的 CirculationRules.g4 并重建镜像。
2. **Kafka 单节点 fenced 风险**：Docker 重启后 broker 可能停在 fenced 状态，
   健康检查不反映。→ 建议：kafka 健康检查换用真实 produce/consume 探测；
   或在启动脚本加 `kafka metadata quorum` 校验；长期考虑 3 节点或迁移 Kraft 重建流程。
3. **keycloak-s0 内存**：已提 2048m；高负载授权期间仍是 OOM 观察对象。
4. **mod-calendar 内存 640m**（经验值，同 entities-links）。
5. **Kong 上游 IP 陈旧**：sidecar/模块容器重启后可能需重启 api-gateway；
   → 长期方案：Kong 配置 DNS resolver 或用 dnsmasq，避免静态 upstream 缓存。
6. mgr-tenant-entitlements 升级窗口缺陷（二阶段遗留）仍在，本次升级前已备份；
   本次前两次失败的部分回滚已由后续成功 PUT 自动收敛（验证 34 行一致）。
7. 通知链（mod-notify/sender/email/template-engine）已部署但未做端到端邮件
   验证（SMTP 未配置）；通知模板中文化待做。
8. 中文参考数据集（读者类型/资料类型/借阅类型代码表）应沉淀为初始化数据集。

## 6. 升级 SOP 增补（在二阶段 SOP 基础上）

- 扩展端口前先核对存量占用（grep compose）。
- 新模块先查官方 eureka-cli config.*.yaml 的 `disable-system-user` /
  `use-vault` / `private-port` 标注，再写 compose。
- 升级前检查 Kafka 是否 fenced（describe 任一 topic 看 Leader 是否为 -1），
  keycloak-s0 是否存活。
- PUT 失败报 Kafka `NotLeaderOrFollowerException` → restart kafka 等 2-3 分钟重试；
  报令牌 502 → 检查 keycloak-s0 是否 OOM、重启 nginx 代理。
- sidecar/模块重启后若网关 502 而直连正常 → `docker restart api-gateway`。

## 7. 当前平台状态（2026-09-20 晚）

- 34 个后端模块 + 34 个 sidecar + 核心组件，FOLIO 相关容器全部 healthy。
- 应用版本 app-platform-minimal-0.0.20；capabilities 1113；用户 folio 登录正常。
- 本机其他项目 scholarguard（5 容器）、ai-literacy（3 容器）处于停止状态
  （经用户同意，可随时 `docker start` 恢复）。
- PoC-1（CNMARC 校验）、PoC-2（中图法编目链）、PoC-3（中文流通链）全部通过。
