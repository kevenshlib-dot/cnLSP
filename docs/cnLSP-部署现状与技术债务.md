# cnLSP 部署现状与技术债务（第一阶段收尾报告）

> 截至 2026-09-19。覆盖：Eureka 最小平台部署、全部本地改造、PoC-1（CNMARC 规则零代码配置）、
> 遗留问题与技术债务清单。下一阶段（编目链部署）前的基线快照。

---

## 1. 已部署的功能

### 1.1 平台基座（Eureka / Sunflower R1-2025 技术线）

| 层 | 组件 | 状态 |
|---|---|---|
| 网关 | Kong（folio-kong，expression 路由） | ✅ 运行，18000 代理 / 8001 管理 |
| 认证 | Keycloak 26.7.3（nginx LB + keycloak-s0 单节点） | ✅ 运行，18080 |
| 管理面 | mgr-tenants / mgr-applications / mgr-tenant-entitlements | ✅ 运行 |
| 基础设施 | PostgreSQL（55432）、Kafka、Vault、kafka-ui | ✅ 运行 |
| 租户 | `diku`，管理员 `folio/folio`（269 项 capabilities） | ✅ 已初始化 |

### 1.2 业务模块（13 个后端模块 + 13 个 sidecar，全部 ARM 原生镜像）

- 基础十二件：mod-configuration、mod-permissions、mod-tags、mod-users、mod-users-bl、
  mod-password-validator、mod-login-keycloak、mod-users-keycloak、mod-roles-keycloak、
  mod-notes、mod-scheduler、mod-settings
- **PoC-1 增部**：mod-record-specifications 2.0.3（Mr. Specs，Sunflower 版本）

应用描述符已从 `app-platform-minimal-0.0.17-SNAPSHOT...` 升级为自建
`app-platform-minimal-0.0.18`（含第 13 个模块），租户 diku 已完成 PUT 升级授权。

### 1.3 PoC-1 产出（CNMARC 零代码规则配置）

- CNMARC 本地字段已建 6 个：**200**（题名与责任说明，$a 必备 + ind1 检索意义代码表）、
  **205**、**215**、**606**（主题）、**690**（中图法分类号）、**701**（个人名称，
  含 ind2 直序/倒序代码表），各含完整子字段定义。
- 规格规则调整：`undefinedField` 已启用；`missingField` 已停用（原因见 §3.2-C）。
- 验证工装 `poc/validator-harness/`（Java + 官方 validator 库 2.0.3）实测：
  合规 CNMARC 记录全通过；缺 200$a 被 missingSubfield 规则精确捕获。
- 配置脚本 `poc/poc1-cnmarc-spec.py`（幂等，可重跑）。

---

## 2. 已做的本地改造（相对官方仓库的全部偏移）

### 2.1 环境工具链（仓库外 `tools/`，不入库）

- Temurin JDK21（**必须，JDK17 编译模块失败**）、Maven 3.9、自编译 bash 5.2.37
  （官方脚本与 macOS 自带 bash 3.2 不兼容）。
- 运行前必须 export JAVA_HOME/PATH/API_GATEWAY_URL（见运行指南 §1）。

### 2.2 端口重映射（本机 8000/8080/5432/90xx 被其他项目占用）

| 组件 | 官方 | 本机 | 改动位置 |
|---|---|---|---|
| Kong 代理 | 8000 | 18000 | docker-compose.kong.yml + misc/lib/docker-health.sh + misc/bootstrap-engine.sh |
| Keycloak | 8080 | 18080 | docker-compose.keycloak.yml + misc/lib/folio-api.sh（2 处） |
| Keycloak 管理 | 9000 | 19000 | docker-compose.keycloak.yml |
| PostgreSQL | 5432 | 55432 | docker-compose.core.yml |
| 模块直连 | 90xx | 290xx | docker-compose.minimal.module.yml（sed 批量） |

### 2.3 Keycloak 26 关键修复（本阶段最大坑）

- **问题**：KC26 用 hostname v2，v1 的 `KC_HOSTNAME_PORT`/`KC_HOSTNAME_STRICT` 被静默忽略，
  端口退化为"跟随请求来源"：外网令牌 iss=`localhost:18080`，内网（sidecar→nginx→KC）
  令牌 iss=`localhost:8080`，sidecar 做 UMA 权限评估时 iss 不匹配 → 401 invalid_token。
- **修复**：`KC_HOSTNAME` 直接写完整 URL `http://localhost:18080`（v2 语法），内外网 iss 一致。
- 此为**端口重映射场景的通用陷阱**，官方默认（内外同 8080）不会触发。

### 2.4 内存调优

- mod-roles-keycloak：384m → **768m**（默认限制 OOM/137）。
- mod-record-specifications：384m → **768m**（首启 OOM 导致租户种子数据只灌了一半，
  后由 sync 端点补齐——见 §3.2-E）。

### 2.5 应用与授权操作

- 描述符升版 0.0.18 并增部模块；**升级授权必须 PUT /entitlements**（POST 会因
  同 app 旧版本已授权被拒），且需同时带 `Authorization` 与 `x-okapi-token` 头。
- 新模块 discovery 需单独注册（批量 POST 遇已有条目 409 即整体跳过）。
- 未添加 /etc/hosts 别名（keycloak/kafka/kong），全程 localhost 无影响。

---

## 3. 遗留问题与技术债务

### 3.1 平台层

| # | 问题 | 级别 | 说明与对策 |
|---|---|---|---|
| A | ~~Docker 内存见顶~~ **已解决（2026-09-20）** | ✅ | Docker 已扩至 23.4 GiB，编目链 6 模块顺利部署（仅 mod-entities-links 需单独提到 640m，见第二阶段记录 §3.4）。 |
| B | Kong 占用 2.1GiB 且日志 debug 级 | 🟡 中 | 生产应调 KONG_LOG_LEVEL=info；2.1GiB 偏高疑似与 debug 日志相关，待观察。 |
| C | mgr-tenant-entitlements 查询偶发 Keycloak 缓存异常 | 🟡 中 | GET /entitlements/{t}/applications 曾报 `Null key ... getAccessToken('#userToken')` 缓存错误（不影响授权主流程），疑为 KC26 hostname 修复前的残留会话，未复现验证。 |
| D | 旧版应用描述符残留 | 🟢 低 | app-platform-minimal 0.0.17 与 0.0.18 并存于 mgr-applications；无害，清理需 revoke 旧版（风险操作，暂留）。 |
| E | create-user.sh 官方 bug | 🟢 低 | line 61 `is_debug: command not found`，不影响主流程，未修。 |
| F | start.sh 摘要硬编码 `Keycloak: http://localhost:8080` | 🟢 低 | 仅显示文案错误（实际 18080），本土化时顺手修。 |
| G | 端口改动散落 4+ 文件 | 🟡 中 | 本土化基线应收敛为单一 env 变量驱动，否则升级官方脚本时易漂移。 |

### 3.2 数据/规范层（PoC-1 实测边界）

| # | 问题 | 级别 | 说明与对策 |
|---|---|---|---|
| A | 规格族不可新建 | 🔴 高（架构约束） | Mr. Specs 只有种子化 MARC bib/authority 两套，无创建 API。中文馆策略=直接定制现有 bib 规格；**西文 MARC21 与 CNMARC 混编时的规则取舍需产品层决策**。 |
| B | 010 标签语义冲突无解 | 🔴 高 | standard 字段禁改 label：MARC21 010=LCCN，CNMARC 010=ISBN。对策候选：① 数据入藏时 CNMARC 010→020 映射（FOLIO inventory 认 020）；② 接受冲突、规范层面约定；③ 长期自研规格族支持。**建议走 ①，入藏映射规则属 mod-inventory 的 data-import 配置域**。 |
| C | system 字段完全锁定 | 🟡 中 | 245/008（MARC21 必备）required 不可改，纯 CNMARC 记录会被 missingField 拦。**当前已整体关闭 missingField**（记录验证通过），代价：丧失所有字段级"必备"检查（子字段级必备不受影响）。长期解法：patch 种子规格数据（把 245/008 降 scope）或等上游开放。 |
| D | CNMARC 字段集不完整 | 🟡 中 | poc1 脚本仅覆盖 9 个核心字段（010/210/856 因标签冲突未建）；CNMARC 全字段集（1xx-8xx 约 60+ 常用字段）需扩充为正式「CNMARC 规格配置包」交付物。 |
| E | 测试残留 | 🟢 低 | 856$9「本地附注(cnLSP测试)」为连通性测试残留，正式配置包定稿时清除。 |
| F | 验证无平台内 API | 🟡 中 | /records-editor/validate 在 mod-quick-marc，依赖 SRS 链——**正是下一阶段部署要解决的**。当前用 Java 工装绕开，工装读 /tmp 路径、手工导出规格，较脆弱。 |

### 3.3 工程层

| # | 问题 | 级别 | 说明 |
|---|---|---|---|
| A | 全部改造未纳入版本控制 | 🟡 中 | eureka-platform-bootstrap 是官方 git clone，本地改动（compose/脚本/描述符）未 commit；建议 fork 或以 patch 集管理，否则官方更新难跟进。 |
| B | ARM 镜像本地构建、无缓存复用 | 🟢 低 | 17 个模块镜像本地构建成功但重建依赖 .m2 缓存；镜像未打私有 tag 归档，Docker 重置即重来（首轮约 1-2 小时）。 |
| C | 令牌 10 分钟过期 | 🟢 低 | 脚本从 /tmp/user-token.txt 读令牌，过期需手动重登（运行指南 §4.1）。 |

---

## 4. 第一阶段结论

- **Eureka 平台本地全链路跑通**，增部模块的通用流程（描述符→构建→注册→PUT 升级）已验证，
  为后续任意模块扩展打下基础。
- **CNMARC 零代码配置核心假设成立**，但 §3.2-A/B/C 三条边界需要产品决策；
  其中 010→020 入藏映射与 missingField 关闭是推荐基线。
- ~~下一阶段最大风险是内存~~（已解决：Docker 扩至 23.4 GiB，编目链部署完成，见《第二阶段部署记录-编目链》）。

## 5. 下一阶段计划（编目链部署）

目标：打通「MARC 记录存储 → 实例映射 → 在线编辑/校验」链路，并完成 PoC-2。

模块（Sunflower R1-2025 锁定版本）：
mod-source-record-storage 5.10.15、mod-source-record-manager 3.10.14、
mod-inventory-storage 29.0.23、mod-inventory 21.1.22、mod-entities-links 4.0.3、
mod-quick-marc 7.0.0

验证点：PoC-2（中图法 call-number-type + 690 映射）、/records-editor/validate 端到端验证、
实例化（MARC→Instance 映射规则的中文适配摸底）。
