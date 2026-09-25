# cnLSP 第二阶段部署记录：编目链（Cataloging Chain）

> 2026-09-20 完成。覆盖：编目链 6 模块部署、升级授权三次失败的完整根因链与解法、
> PoC-2（中图法索书号 + CNMARC 端到端验证）结果、新增技术债务。
> 前置文档：《cnLSP-部署现状与技术债务.md》（第一阶段基线）。

---

## 1. 本阶段目标与结果

目标：在 Eureka minimal 平台上部署 FOLIO 编目链核心模块，复刻 FOLIO 的
"MARC 源记录存储 → 数据导入 → 馆藏存储 → MARC 编辑"链路，并验证本土化基线
（CNMARC 规则 + 中图法索书号）。

结果：**全部完成**。应用描述符升至 `app-platform-minimal-0.0.19`（19 个模块），
租户 diku 升级授权成功，PoC-2 全部通过。

## 2. 新增模块清单

| 模块 | 版本 | 直连端口 | 角色 |
|---|---|---|---|
| mod-source-record-storage (SRS) | 5.10.15 | 29014 | MARC 源记录存储 |
| mod-source-record-manager (SRM) | 3.10.14 | 29015 | 数据导入编排 |
| mod-di-converter-storage | 2.4.3 | 29016 | 数据导入 profile/映射存储 |
| mod-inventory-storage | 29.0.23 | 29017 | 馆藏存储（instance/holdings/item） |
| mod-entities-links | 4.0.3 | 29018 | 书目-规范连接 |
| mod-quick-marc | 7.0.0 | 29019 | MARC 编辑与规范验证 |

各配 sidecar（190xx）。镜像均为本地构建的 ARM 原生镜像；其中 SRS 与
inventory-storage 因官方构建缺陷手工修复（见第一阶段文档 §3 与本文 §4.6）。

## 3. 升级授权三次失败的根因链与解法（本阶段核心经验）

PUT 升级授权到 0.0.19 共失败两次、第三次成功。三个根因相互独立、逐层暴露：

### 3.1 第一次失败：mod-permissions 权限表为空

- **现象**：mod-entities-links 租户初始化报错 `Attempting to add non-existent
  permissions inventory-storage.instances.item.get,...`；查 mod-permissions
  `/perms/permissions` 为 0 条。
- **根因**：Eureka minimal 平台没有 Okapi 时代的 `/_/tenantPermissions` 注册
  环节，19 个模块描述符里的 permissionSets 从未被灌进 mod-permissions。
  folio-spring-base 模块（如 entities-links）在系统用户创建时会向
  mod-permissions 校验权限存在性，于是炸掉。
- **解法**：`poc/load-permissions.py`——从各模块描述符提取 permissionSets，
  POST 到 mod-permissions 直连端点 `http://localhost:29003/_/tenantpermissions`
  （注意：**直连端口 29003**，`/_/` 系统端点无 Kong 路由；描述符带缓存与重试）。
  共灌入 642 条权限（19 个模块），幂等可重跑。

### 3.2 第二次失败：升级流程回滚不完整导致授权表不一致

- **现象**：第一次失败回滚后，平台原有功能（/users 等）也全部 503：
  `ModUsersKeycloakTargetNotResolvedException: mod-users-keycloak address is
  not resolved for the tenant yet. No entitled module found for name:
  moduleName = mod-users-keycloak, tenant = diku`。
- **根因链**：
  1. 该异常实际由 **sidecar**（folio-module-sidecar 的
     `TenantModuleResolver`/`UserService`）抛出：sidecar 为校验请求令牌，需解析
     "租户 diku 授权了哪个 mod-users-keycloak 版本"，数据源是
     mgr-tenant-entitlements 的 `GET /entitlements?tenant=X&includeModules=true`。
  2. 该查询按 `entitlement` 表的 application_id 连接 `entitlement_module` 表。
  3. 升级流程开始后会把 entitlement_module 行改写成 0.0.19 的模块，而
     entitlement 主表行仍指 0.0.18 → 连接结果为空 → 全平台解析失败。
     **即：升级流程执行期间存在一个"解析中断窗口"，任何需要认证的
     模块间调用都会失败。**
  4. 更糟的是失败后回滚只恢复了 entitlement 主表（回到 0.0.18），
     **没有恢复 entitlement_module 行**（仍留 17 行 0.0.19）→ 窗口永久化。
- **解法**（手工 SQL，`docker exec -i` 必须有 `-i`，否则 stdin 不进容器）：
  删除 17 行 0.0.19，插回 13 行 0.0.18（见本文附录 A 的 SQL）。
  sidecar 的 bindings 缓存不缓存失败结果，DB 修复后无需重启即恢复。
- **上游缺陷记录**：mgr-tenant-entitlements 的 UPGRADE 流程存在
  (a) 执行期解析中断窗口、(b) 回滚不完整两个设计缺陷。官方 minimal 平台
  不触发是因为其模块租户初始化均不做认证 egress 调用（见 3.3）。

### 3.3 第三次成功的关键：禁用 entities-links 的旧式系统用户创建

- **现象**：第二次 PUT 仍失败于 entities-links 租户初始化，但错误从
  "权限不存在"变为 POST /perms/users 时 sidecar 解析失败（命中 §3.2 的窗口）。
- **根因**：mod-entities-links 的 `application.yaml` 默认
  `folio.system-user.enabled: ${SYSTEM_USER_ENABLED:true}`——走 Okapi 时代的
  旧式系统用户创建（POST /users + /authn/credentials + /perms/users），
  这些认证调用在升级窗口内必败。
- **解法**：compose 中为 mod-entities-links 设置
  `SYSTEM_USER_ENABLED: "false"` + `FOLIO_SYSTEM_USER_ENABLED: "false"`。
  这是官方 Eureka 部署的标准做法（folio-org/eureka-setup 的
  `eureka-cli/moduleenv/module_env.go` 对所有模块默认设置）。
  Eureka 模式下系统用户改由 mgr-tenant-entitlements 的
  `systemUserModuleEventPublisher` 阶段发 Kafka 事件、mod-users-keycloak
  消费后创建（Keycloak 服务账号，密码入 Vault）。
- **对照**：mod-quick-marc、mod-notes 等没有该默认开启的配置，不受影响。

### 3.4 附带修复：mod-entities-links OOM

- 授权成功后 entities-links 因 Kafka 消费组激增（authority 主题 50 分区等）
  超出默认 384m 内存限制被 OOMKill（exit 137）。compose 中单独提到 640m 后稳定。

### 3.5 灌权限后的副作用观察

- 灌入 642 条权限后原有 12 模块无异常（它们走 capabilities 不查 perms 表）。
- PoC-2 期间 SRS 的 `/source-storage/records?limit=0` 出现
  `RecordDaoImpl.asRow NPE`（上游缺陷，limit=0 触发；`/source-records` 正常）。

### 3.6 构建期遗留（记录备查）

- SRS / inventory-storage 官方 maven 构建在 Apple Silicon + 新 Docker API 下失败
  （docker-maven-plugin 0.43 gson NPE），已用手工方式构建（参数见第一阶段文档）。
  后续升级版本时需复用该手工流程或升级插件。

## 4. 配置变更清单（本阶段新增偏移）

| 位置 | 变更 |
|---|---|
| descriptors/app-platform-minimal/descriptor.json | 0.0.18 → 0.0.19（13→19 模块） |
| docker-compose.minimal.module.yml | 新增 6 模块服务（29014-29019/10014-10019）；mod-entities-links 加 `SYSTEM_USER_ENABLED=false`/`FOLIO_SYSTEM_USER_ENABLED=false` + 内存 640m |
| docker-compose.minimal.sidecar.yml | 新增 6 个 sidecar（19014-19019） |
| poc/load-permissions.py | 新增：权限集灌入脚本（幂等） |
| poc/poc2-clc-e2e.py | 新增：PoC-2 验证脚本（幂等） |

## 5. 验证结果

### 5.1 平台状态

- 授权状态：diku → app-platform-minimal-0.0.19，entitlement_module 19 行一致。
- folio 用户 capabilities：604 → **647**，登录验证 672 权限可用
  （重跑 `misc/create-user.sh`，幂等）。
- 端点矩阵（网关 18000，folio 令牌）：

| 端点 | 状态 |
|---|---|
| /users | ✅ 200 |
| /source-storage/source-records | ✅ 200 |
| /instance-storage/instances | ✅ 200 |
| /holdings-storage/holdings | ✅ 200 |
| /data-import-profiles/jobProfiles（SRM） | ✅ 200 |
| /specification-storage/specifications | ✅ 200 |
| /records-editor/records（quick-marc） | ✅ 可达（400=参数校验，路由正常） |
| /links/instances/{id}（entities-links） | ✅ 200 |

### 5.2 PoC-2：中图法 + CNMARC 端到端（全部通过）

脚本 `poc/poc2-clc-e2e.py`，两部分：

**第一部分 CNMARC 规范验证**（quick-marc `/records-editor/validate`）：
- 含 010（ISBN）/200（题名）/690（中图法分类号 G250.76）的 CNMARC 记录
  **全部通过** PoC-1 注册的 CNMARC 规则；
- 对照组：规范外字段 133 被精确标记 `Field is undefined`（warn 级）——
  证明规格的严格校验真正在端到端链路上生效。

**第二部分 CLC 索书号存储**（mod-inventory-storage）：
- 创建索书号类型"中国图书馆分类法（中图法/CLC）"（source=local，
  中文名正常持久化）；
- 补齐 0.0.19 升级未加载的参考数据（实例类型 text、标识符类型 ISBN、
  馆/ campus/图书馆/位置四级 + 流通服务点 + holdings 来源"本地"）；
- 创建实例《智慧图书馆概论》+ holdings（索书号 G250.76，中图法类型），
  回读验证一致。

**发现的 upstream 缺陷（validate 端点）**：字段 `content` 必须传字符串
（`"$a xxx $b yyy"`）；传 Map（`{"$a":"xxx"}`）时——
- 字段 010 触发 `Tag010FieldItemPopulationService` 对 Map.toString 结果做
  `substring(2)` 导致 500（该填充器为 MARC21 LCCN 规范化设计，从未考虑 Map 输入）；
- 其他字段报 400 `Invalid converter: `。
PoC 脚本已用字符串格式规避；此坑需写入开发者文档，后续给上游提 issue。

## 6. 新增技术债务 / 遗留问题

1. **mgr-tenant-entitlements 升级窗口缺陷**（§3.2）：每次 PUT 升级授权期间
   全平台认证调用短暂不可用，且失败回滚不完整需手工修表。
   → 后续每次升级前备份 `entitlement`/`entitlement_module` 两表；
   升级窗口避开服务时段；向 FOLIO 社区确认是否已知问题。
2. **权限表无自动注册环节**：新增含 permissionSets 的模块后必须重跑
   `poc/load-permissions.py`，否则 Spring 模块租户初始化失败。
   → 已脚本化、幂等；升级 SOP 中固化为步骤。
3. **参考数据未随升级加载**：PUT 升级不带 `tenantParameters=loadReference=true`，
   新模块的参考数据（实例类型、位置等）为空，PoC-2 已按需手工补齐。
   → 生产部署时应使用带 loadReference 的初始化策略；或编写中文参考数据集
   （本土化工作：中国图书馆适用的事先编目的实例类型/载体/语种代码表）。
4. **SRS limit=0 NPE**（§3.5）：上游缺陷，查询用 limit≥1 规避。
5. **mod-entities-links 内存**：640m 是经验值，正式部署需按数据量复测。
6. 第一阶段遗留问题仍有效（见《部署现状与技术债务》§3），其中 §3.1-A
   Docker 内存已扩至 23.4 GiB，本条可关闭。

## 7. 升级授权 SOP（沉淀给后续每次应用描述符升级）

1. 备份：`docker exec db pg_dump -U $POSTGRES_USER mgr_tenant_entitlements > backup.sql`
2. 构建/更新镜像 → 更新描述符 → 注册描述符与 discovery → 重启新模块 sidecar。
3. 重跑 `python3 poc/load-permissions.py`（灌权限）。
4. 检查新增 Spring 模块是否默认开启旧式 system-user（查其 application.yaml 的
   `folio.system-user.enabled`），是则在 compose 加 `SYSTEM_USER_ENABLED=false`。
5. PUT /entitlements 升级；若失败且报 `ModUsersKeycloakTargetNotResolvedException`，
   按附录 A 修复授权表后重试。
6. 重跑 `misc/create-user.sh folio folio` 分配新 capabilities。
7. 跑端点矩阵 + PoC 脚本验证。

## 附录 A：授权表修复 SQL（回滚不完整时使用）

```sql
-- docker exec -i db sh -c 'psql -U $POSTGRES_USER -d mgr_tenant_entitlements'
BEGIN;
DELETE FROM entitlement_module
 WHERE tenant_id='<tenant_uuid>' AND application_id='app-platform-minimal-0.0.19';
INSERT INTO entitlement_module (module_id, tenant_id, application_id) VALUES
 -- …0.0.18 的 13 个模块，逐条 ('<module-id>', '<tenant_uuid>', 'app-platform-minimal-0.0.18')
COMMIT;
-- 验证：select application_id, count(*) from entitlement_module group by 1;
-- 应只剩 0.0.18 × 13；然后重试 PUT
```
