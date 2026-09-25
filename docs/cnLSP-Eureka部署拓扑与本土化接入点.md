# cnLSP：Eureka 部署拓扑与本土化数据格式接入点

> 版本：v1.0 · 2026-09-19
> 依据：FOLIO 官方 Wiki（Eureka Platform Overview / Developer Guide / TC-0010）、
> folio-org/platform-lsp、eureka-platform-bootstrap、Sunflower 发布说明、
> 刘炜等（2026）论文，以及云瀚 2026 调研报告。

---

## 1. 关键事实确认

1. **Sunflower（R1-2025）是 FOLIO 完成 Okapi → Eureka 架构转型的版本**
   （2026-03-17 官方发布说明确认）。
2. Sunflower 同时提供两种部署变体（platform-complete 分支实证）：
   - `R1-2025`：**Eureka 版**（cnLSP 基线应选这个）；
   - `R1-2025-okapi`：Okapi 版（仅供存量迁移过渡，**不应作为新部署基线**）。
3. **Eureka 时代的平台组合仓库是 `folio-org/platform-lsp`**
   （含 `install-applications.json`、`management-modules.json`，
   分支已有 R1-2025 / R1-2026）——地位等同 Okapi 时代的 platform-complete。
4. 应用（**Application**）成为模块组合与版本管理单位：
   `app-platform-minimal`（必备核心）+ `app-platform-complete`（完整业务）+
   各领域可选应用（ERM、采访、edge 等）。

## 2. Eureka 平台组件清单

### 2.1 平台管理组件（Eureka 特有）

| 组件 | 职责 | 部署形态 |
|---|---|---|
| folio-kong | API 网关、CORS、流量管理 | DaemonSet |
| folio-keycloak | 认证与授权（OAuth2/OIDC，每租户一个 Realm） | StatefulSet |
| mgr-applications | 应用/模块注册、发现信息 | ReplicaSet |
| mgr-tenants | 租户生命周期管理 | ReplicaSet |
| mgr-tenant-entitlements | 租户-应用授权（entitlement），驱动 Keycloak 资源配置与 Kong 路由生成 | ReplicaSet |
| folio-module-sidecar | 每个业务模块的边车：服务发现、模块间路由、授权过滤 | 随模块成对部署 |
| mod-roles-keycloak | 角色/策略/capability 管理 | 应用模块 |
| mod-users-keycloak | FOLIO 用户与 Keycloak 用户桥接 | 应用模块 |
| mod-login-keycloak | login 接口的 Keycloak 实现 | 应用模块 |
| mod-consortia-keycloak | 联盟（consortia）接口的 Eureka 实现 | 应用模块 |
| mod-scheduler | 定时任务 | 应用模块 |
| mod-okapi-facade | okapi 接口的部分兼容实现（迁移期用） | 应用模块 |

### 2.2 基础设施

PostgreSQL（多库）、Kafka（事件流 + entitlement 变更通知）、
OpenSearch（检索）、Vault（密钥）、MinIO/S3（对象存储，数据导出等）、
Postfix（邮件）。

### 2.3 被替换/将废弃的 Okapi 时代组件（cnLSP 一律不投入）

| 废弃 | 替代 |
|---|---|
| Okapi | Kong + Keycloak + sidecar + mgr-* |
| mod-authtoken | Keycloak / sidecar |
| mod-login | mod-login-keycloak |
| mod-login-saml | **Keycloak 原生 SAML/OIDC IdP 联邦** |
| mod-permissions | mod-roles-keycloak（capabilities/roles） |
| mod-consortia | mod-consortia-keycloak |

> **对 cnLSP 的直接利好**：mod-login-saml 被 Keycloak 取代后，
> CARSI / 校园统一认证 / 城市公共身份平台对接变成 Keycloak 的
> Identity Provider 配置工作，基本无需自研适配模块。

## 3. cnLSP 目标部署拓扑

### 3.1 开发/测试环境（单机容器）

- 入口：`folio-org/eureka-platform-bootstrap`（docker-compose 最小平台）
  或 `eureka-cli`（folio-org/eureka-setup，Go 编写的本地部署 CLI）；
- 内容：Kong + Keycloak + mgr-* + PostgreSQL + Kafka + OpenSearch +
  Vault + MinIO + app-platform-minimal；
- 用途：模块开发、汉化验证、CNMARC 规则试验。

### 3.2 生产拓扑（按规模基准：500 万册 / 日 3 万流通）

```
                 ┌──────────── 读者/馆员入口 ────────────┐
                 │  Stripes UI (Nginx)  │  微信/OPAC/自助机 │
                 └─────────┬────────────────────┬───────┘
                           │                    │
                    ┌──────▼───────┐     ┌──────▼──────┐
                    │  Kong 网关    │     │ edge-* 端点  │
                    │ (DaemonSet,  │     │ (SIP2/NCIP/  │
                    │  多副本)      │     │  OAI-PMH…)   │
                    └──────┬───────┘     └──────┬──────┘
                           │                    │
        ┌──────────────────┼────────────────────┤
        │                  │                    │
 ┌──────▼──────┐   ┌───────▼────────┐   ┌───────▼────────┐
 │  Keycloak    │   │ 业务模块集群     │   │ 管理组件        │
 │ (StatefulSet, │   │ mod-* + sidecar │   │ mgr-applications│
 │  每租户Realm) │   │ (每模块≥2副本,   │   │ mgr-tenants     │
 │              │   │  K8s HPA 弹性)  │   │ mgr-tenant-     │
 │  ← CARSI/SSO │   │                │   │  entitlements   │
 │    IdP 联邦   │   └───────┬────────┘   └────────────────┘
 └──────────────┘           │
        ┌───────────────────┼───────────────────┐
 ┌──────▼──────┐  ┌─────────▼────┐  ┌───────────▼───┐  ┌────────┐
 │ PostgreSQL   │  │ Kafka 集群   │  │ OpenSearch 集群│  │ MinIO/ │
 │ (主备/HA,    │  │ (3 节点)     │  │ (3 节点,      │  │ S3 +   │
 │  多租户分库)  │  │              │  │  中文分词插件) │  │ Vault  │
 └─────────────┘  └──────────────┘  └───────────────┘  └────────┘
```

容量要点：
- 流通高峰弹性：mod-circulation、mod-inventory、edge-sip2 等按 HPA 配置
  自动扩缩容（刘炜论文指出的 Eureka 核心收益）；
- Keycloak 为状态ful 关键组件，需独立 HA 与备份策略；
- entitlement 变更经 Kafka 通知 sidecar，扩缩容时路由一致性由平台保证。

## 4. 本土化数据格式与标准规范接入点（重点）

> 原则：**能用配置/参考数据解决的，绝不改代码；必须扩展的，以自有模块实现。**

### 4.1 CNMARC 支持

| 接入点 | 机制 | cnLSP 做法 |
|---|---|---|
| **MARC 校验规则** | mod-record-specifications（社区昵称 "Mr. Specs"）提供 **API 驱动的校验规则配置**：字段/指示符/子字段的可重复性、必填性均可按租户定义；Eureka 下为 app-platform-complete 的 `Specification-Storage` capability set | 将 **CNMARC 字段规则库**（200 题名/690 中图法分类/701 责任者/905 馆藏等）制作为租户级规则配置包，随实施交付，**零代码改动** |
| MARC 编辑 | mod-quick-marc（Spring Boot 后端）+ ui-quick-marc | 验证 CNMARC 字段在编辑器中的可用性；如有硬编码 MARC21 假设，以最小 patch 或配置解决 |
| MARC 存储 | mod-source-record-storage（SRS）以 MARC-JSON 存储，本身格式中立 | 直接复用；CNMARC↔MARC21 转换走独立映射验证服务（见路线图 §3.5-4） |
| 数据导入 | mod-data-import + mod-di-converter-storage 的字段映射 profile | 建立 CNMARC→Inventory 实例/馆藏/条目的映射 profile 库 |
| 规范控制 | mod-marc-authorities / mod-entities-links | 接入中文名称规范与主题词表（中文主题词表、人名规范库） |

### 4.2 分类法（中图法 CLC）

- FOLIO 的索书号类型（call-number-types）是 mod-inventory-storage 的
  **参考数据（reference data）**，可通过 API 扩展——**新增「中图法」类型无需改代码**；
- CNMARC 中中图法分类号著录于 **690 字段**（与美国 050/082 对应），
  需在 data-import 映射与 quickMARC 规则中对应配置；
- 需要验证：索书号排序（shelving order）算法对 CLC 字母-数字混排的适配，
  如有问题以自有排序服务/补丁解决；
- 科图法（LCCAS）等小众分类法按馆需求以同样机制追加。

### 4.3 中文检索

- mod-search 底层为 OpenSearch：需部署 **IK 或 jieba 分词插件**，
  并配置拼音字段（题名/责任者拼音检索是国内 OPAC 标配）；
- 多语种混排（中/英/日/俄）分词策略需在索引模板中显式定义；
- 该部分是唯一必须动基础设施镜像的本土化项，应封装为
  「cnLSP OpenSearch 镜像 + 索引模板包」统一交付。

### 4.4 其他本土化标准

| 领域 | 标准/规范 | 接入方式 |
|---|---|---|
| 界面语言 | zh_CN | Stripes react-intl：各 ui-* 模块提供 `zh_CN.json`（不改代码） |
| 读者证件 | 身份证号/读者证规则 | mod-users 的 patron group + 校验配置；必要时自有校验模块 |
| 古籍/特藏著录 | 古籍著录规则、地方文献规范 | 一期以 CNMARC 扩展字段 + inventory 本地字段承载；二期自研特藏模块 |
| 联合目录 | CALIS Z39.50 / OAI-PMH | mod-z3950、mod-copycat、edge-oai-pmh 配置层对接 |
| 统计报表 | 教育部高校图书馆统计指标 | LDP / mod-reporting 的 SQL 报表模板包 |
| 流通规则 | 国内借阅册数/期限/罚款习惯 | mod-circulation 规则引擎（规则文本配置，不改代码） |

## 5. 与一期路线图的衔接

- **阶段 0（环境就绪）改为基于 Eureka**：
  1. 用 eureka-platform-bootstrap 起最小平台（app-platform-minimal）；
  2. 切换 platform-lsp `R1-2025` 分支组合，部署 app-platform-complete；
  3. 验证 Keycloak 租户 Realm、Kong 路由、sidecar 通信、capabilities 授权链。
- **阶段 2（编目检索）的前置试验提前**：
  CNMARC 规则包（Mr. Specs API）与中图法 call-number-type 扩展是
  「零代码可行性」的关键验证点，建议在阶段 0 完成后立即做 PoC，
  以尽早暴露需要 patch 的硬编码点。
- **阶段 3（认证）简化为 Keycloak IdP 联邦配置 + 少量属性映射**。

## 6. 下一步行动

- [x] 克隆 platform-lsp（R1-2025 分支）与 eureka-platform-bootstrap 到工作区
- [x] 本地启动 Eureka 最小平台冒烟（Docker）——2026-09-19 通过，见 §7
- [x] PoC-1：通过 Mr. Specs API 配置 CNMARC 核心字段校验规则——2026-09-19 完成，见 §8
- [ ] PoC-2：新增「中图法」call-number-type 并验证 690 字段映射
- [ ] PoC-3：OpenSearch 中文分词（IK/jieba + 拼音）索引模板验证

## 8. PoC-1 实测结论：CNMARC 规则零代码配置（2026-09-19）

在最小平台上增部 mod-record-specifications 2.0.3（Sunflower 版本）后完成实测，
脚本与工装存于 `poc/`（poc1-cnmarc-spec.py、validator-harness/）。

### 8.1 验证通过的假设

1. **任意 3 位数字标签可定义**：字段 tag 约束仅为 `\d{3}`，非 9XX 的 CNMARC
   字段（200/205/215/606/690/701）均成功创建为 local scope，含全部子字段、
   指示符及代码表（如 200 ind1 题名检索意义 0/1、856 ind1 访问方法 0-4/7）。
2. **验证引擎确实由规格数据驱动**：用平台 API 导出的规格 JSON 驱动官方
   validator 库（mod-record-specifications-validator 2.0.3），合规 CNMARC
   记录通过；缺 200$a 的记录被 missingSubfield 规则准确捕获（位置 200[0]$a[0]）。
3. **规格级 15 条规则可独立开关**（PATCH …/rules/{id}），standard 字段可
   追加 local 子字段（如 856$9）。
4. **增部模块路径打通**：描述符加模块 → run.py 同步 → ARM 镜像构建 →
   compose 加服务对 → 单独注册 discovery → **PUT /entitlements 升级**
   （POST 会因同 app 旧版本已授权被拒；升级必须 PUT 且带 x-okapi-token）。

### 8.2 发现的硬边界（零代码做不到，需决策）

| 边界 | 实测 | 影响与对策 |
|---|---|---|
| 不能新建规格族 | 规格仅种子化 MARC bib/authority 两套，无 POST /specifications | 一个租户一套书目规格：中文馆直接把它定制为 CNMARC 取向 |
| standard 字段不可改 label/deprecated | 010 在 MARC21=LCCN、CNMARC=ISBN，语义冲突无法改标签 | CNMARC 010→仍按 ISBN 用系需数据层约定；或入藏时映射到 020（FOLIO inventory 本来就认 020） |
| system 字段完全锁定 | 245/008 为 system scope，required 都不可改；纯 CNMARC 记录会被 missingField 拦 | 只能整体关闭 missingField 规则（实测可行，记录 A 随即全通过），代价是放弃字段级必备检查；子字段级必备（200$a）不受影响 |
| 验证无独立 API | validate 端点在 mod-quick-marc，且其 requires SRS/entities-links 接口 | 端到端验证需部署编目链（SRS+entities-links+quick-marc），归入编目阶段任务 |

### 8.3 对一期方案的影响

- CNMARC 著录校验**可行且大部分零代码**：CNMARC 独有字段全部 API 可配；
  推荐配置基线 = 关闭 missingField + 保留子字段级必备 + 本地字段全集。
- 需要编写一份「CNMARC 规格配置包」脚本（poc1-cnmarc-spec.py 的完整版），
  覆盖 CNMARC 全部常用字段，作为本土化交付物。
- 混合馆藏（中西文混编）场景需在数据层决策：西文 MARC21 记录与 CNMARC
  记录共用一套规格时的取舍（本 PoC 的 mixed 状态即为默认形态）。

## 7. 本地开发环境实测（2026-09-19，macOS Apple Silicon）

Eureka 最小平台（app-platform-minimal）本地冒烟已通过：网关可达、系统令牌、
租户 diku、248 项 capabilities、管理员 folio/folio 登录验证（256 权限）全部成功，
幂等重跑 `start.sh --yes` 全程约 17s。

### 7.1 本地端口映射（因本机 8000/8080/5432/90xx 被其他项目占用）

| 组件 | 官方端口 | 本机映射 | 涉及文件 |
|---|---|---|---|
| Kong API 网关 | 8000 | **18000** | docker-compose.kong.yml；脚本 misc/lib/docker-health.sh、misc/bootstrap-engine.sh |
| Keycloak（nginx 前端） | 8080 | **18080** | docker-compose.keycloak.yml；misc/lib/folio-api.sh |
| Keycloak 管理端口 | 9000 | **19000** | docker-compose.keycloak.yml |
| PostgreSQL | 5432 | **55432** | docker-compose.core.yml |
| 模块直连端口 | 90xx | **290xx** | docker-compose.minimal.module.yml |

### 7.2 本地工具链（系统无 brew/Java，置于仓库外 ../tools/）

- JDK：Temurin 21（**必须 JDK21，JDK17 编译模块会失败**）
- Maven 3.9、自编译 bash 5.2.37（官方脚本与 macOS 自带 bash 3.2 不兼容）
- 运行 start.sh 前需 export JAVA_HOME/PATH 指向 tools，并设
  `API_GATEWAY_URL="http://localhost:18000"`

### 7.3 实测踩坑与修正（提交本土化基线时需固化）

1. **mod-roles-keycloak OOM**：模块模板默认 384m 内存限制导致容器反复 137 退出，
   已在 compose 中为该模块单独调至 768m 后稳定 healthy。
2. **Keycloak 26 hostname v2 导致的 401（本次主要故障）**：
   官方默认内外网端口同为 8080，令牌 issuer 天然一致；端口重映射后，
   外网令牌 iss 为 `localhost:18080`、内网（sidecar 经 nginx 访问 keycloak:8080）
   令牌 iss 为 `localhost:8080`，sidecar 用外网 iss 的令牌做 UMA 权限评估时
   被 Keycloak 判定 `invalid_token`（PERMISSION_TOKEN_ERROR, grant_type=uma-ticket）。
   KC26 已移除 v1 的 KC_HOSTNAME_STRICT/KC_HOSTNAME_PORT（静默忽略），
   **修复方式：KC_HOSTNAME 直接写完整 URL `http://localhost:18080`**，
   内外网签发令牌的 iss 即一致。这是端口重映射场景的通用陷阱，需写入部署手册。
3. **create-user.sh line 61 官方小 bug**：`is_debug: command not found`（不影响主流程）。
4. start.sh 尾部摘要仍硬编码显示 `Keycloak: http://localhost:8080`（仅显示文案，
   实际为 18080），本土化时可顺手修正。
5. 未添加 /etc/hosts 的 keycloak/kafka/kong 别名，全程走 localhost 无影响；
   官方文档要求的别名在端口重映射方案下并非必需。
