# cnLSP：FOLIO 架构分析与中国本土化路线图

> 版本：v1.1 · 2026-09-19
> 基线代码：`platform-complete`（已克隆至 `../platform-complete`，snapshot 分支）

---

## 1. 项目定位

cnLSP（China Library Services Platform）基于开源图书馆服务平台 **FOLIO**（Apache 2.0），
建设一套**完整的、架构灵活的、覆盖智慧图书馆几乎所有需求**的图书馆业务管理与服务平台。

### 1.1 目标馆型与规模基准（设计基准）

| 维度 | 基准 |
|---|---|
| 馆型 | 城市图书馆（公共馆）、学校图书馆（大学/学院/大中专/职业学校）、专业图书馆 |
| 纸本馆藏 | 100 万–500 万种（册）（书刊报） |
| 读者规模 | 日接待 3k–10k 人次 |
| 流通量 | 日流通 10k–30k 册 |
| 特藏 | 古籍、地方文献等（特藏管理、数字化与长期保存） |
| 电子资源 | 电子书、数据库（ERM、发现服务、远程访问） |
| 服务形态 | 流通、阅览、参考咨询、空间/座位、活动、自助设备、移动端等全类型服务 |

**容量含义**：500 万册馆藏对应 inventory 实例/馆藏记录千万级行、日 3 万笔流通交易
（峰值时段并发数百 TPS 量级），部署规划须按「Okapi + 关键模块多副本 +
PostgreSQL 独立高可用 + Kafka 集群 + OpenSearch 集群」的生产级拓扑设计，
单机部署仅用于开发测试。特藏与电子资源意味着除传统流通外，
数字化仓储、长期保存（OAIS 思路）与统一发现均为必备能力域。

### 1.2 核心策略

- **不重写内核**：保留 Okapi 网关 + 微模块架构，跟随上游版本演进；
- **以模块替换/新增实现本土化**：凡中国特有业务（CNMARC、中图法、CALIS 对接、
  微信/支付宝、等保合规）均以自有模块或配置层实现，避免 fork 核心模块。

## 2. FOLIO 架构速览

```
┌─────────────────────────────────────────────────────┐
│  UI 层      Stripes（React）· 78 个前端模块(ui-*/plugin-*)│
├─────────────────────────────────────────────────────┤
│  边缘层     edge-*（13 个）：SIP2 / NCIP / Z39.50 / OAI-PMH │
│             对外协议适配，API Key 认证                  │
├─────────────────────────────────────────────────────┤
│  网关层     Okapi（Vert.x）：路由、租户、权限、模块发现     │
├─────────────────────────────────────────────────────┤
│  应用层     mod-*（73 个后端微模块）：业务逻辑 + 存储       │
├.────────────────────────────────────────────────────┤
│  系统层     PostgreSQL · Kafka(pubsub) · OpenSearch(检索)  │
└─────────────────────────────────────────────────────┘
```

**关键机制**

- **多租户**：Okapi 原生支持 tenant 隔离，适合联盟/总分馆模式（与云瀚联盟路线一致）；
- **ModuleDescriptor / 接口契约**：模块通过 JSON 描述符声明 provides/requires，
  版本化接口允许单个模块独立替换——这是本土化替换策略的技术基础；
- **pub/sub 事件总线**（mod-pubsub + Kafka）：数据导入、流通事件均走事件驱动；
- **edge 模块**：把内部 API 包装成自助设备/外部系统可用的协议端点。

> **⚠ 平台换代：Okapi → Eureka（进行中）**
> 据云瀚 2026 调研报告（见 §3.5），FOLIO 正在从 Okapi 单中心架构迁移到
> **Eureka 平台**：Kong（API 网关）+ Keycloak（认证授权）+ Quarkus Sidecar
> （模块通信/授权过滤）+ 管理组件（应用注册/租户/授权），并以 **application**
> 作为模块组合与版本管理单位。**Sunflower 起已采用 Eureka 的
> capabilities / capability sets / roles 逐步替代 Okapi 的 permission sets**，
> 目前处于两套权限体系并存的迁移期。cnLSP 的基线选型、权限体系设计和
> 部署脚本都必须以 Eureka 为准来规划，避免在 Okapi 私有管理接口上投资。

## 3. 模块清单分类（platform-complete snapshot）

### 3.1 后端 mod-*（73 个）

| 类别 | 模块 | 本土化相关性 |
|---|---|---|
| 平台核心 | mod-authtoken, mod-login, mod-login-saml, mod-permissions, mod-users, mod-users-bl, mod-password-validator, mod-configuration, mod-settings, mod-audit | 认证需对接国内统一身份认证（CARSI/校园 SSO） |
| 消息通知 | mod-event-config, mod-template-engine, mod-email, mod-sender, mod-notify | 需扩展短信/微信模板与通道 |
| 事件总线 | mod-pubsub, mod-graphql, mod-tags, mod-notes, mod-calendar | 直接复用 |
| 资源管理/编目 | mod-inventory(-storage/-update), mod-source-record-storage(-manager), mod-data-import, mod-di-converter-storage, mod-quick-marc, mod-entities-links, mod-search, mod-copycat, mod-z3950, mod-oai-pmh, mod-record-specifications | **改造重点**：CNMARC、中图法、中文分词检索 |
| 流通服务 | mod-circulation(-storage/-item), mod-patron, mod-patron-blocks, mod-feesfines, mod-ncip, mod-rtac, mod-reading-room, mod-remote-storage, mod-batch-print | 规则适配国内借阅习惯；费款对接移动支付 |
| 采访/财务 | mod-orders(-storage), mod-invoice(-storage), mod-finance(-storage), mod-organizations(-storage), mod-gobi, mod-ebsconet | GOBI/EBSCO 为海外书商，需替换为国内书商（人天、湖北三新等）采访接口 |
| 电子资源管理(ERM) | mod-agreements, mod-licenses, mod-erm-usage(-harvester), mod-eusage-reports, mod-kb-ebsco-java, mod-serials-management, mod-service-interaction | 知识库需接中文数据库（CNKI/万方/维普）元数据 |
| 数据导出/报表 | mod-data-export(-spring/-worker), mod-reporting, mod-lists, mod-fqm-manager, mod-bulk-operations | 需增加教育部高校馆统计报表模板 |
| 其他 | mod-courses（教参）, mod-user-import, mod-dcb（馆际互借）, mod-copycat | DCB 可演化为 CALIS 馆际互借对接 |

### 3.2 前端 folio_*（78 个）

- 65 个 `folio_*` 业务 UI（checkin/checkout/circulation/inventory/orders/users…）
  —— **汉化主战场**，Stripes 采用 react-intl，各模块自带 `translations/*/en.json`，
  提供 `zh_CN.json` 即可，无需改代码；
- 13 个 `edge-*` 对外协议端点（见下）。

### 3.3 edge-* 边缘模块与本土化映射

| edge 模块 | 用途 | 国内对应 |
|---|---|---|
| edge-sip2 | 自助借还机 SIP2 协议 | 国内自助设备普遍支持 SIP2，**直接复用** |
| edge-rtac | 实时馆藏查询（OPAC） | 复用，接自建 OPAC/发现系统 |
| edge-oai-pmh | 元数据收割 | 复用，供 CALIS/国家联合目录收割 |
| edge-ncip / mod-ncip | 馆际互借 NCIP | 改造对接 CALIS 馆际互借协议 |
| edge-connexion | OCLC 联机编目 | **替换**：CALIS 联机编目 / 国图 Z39.50 |
| edge-orders | 书商 EDI 订单 | 改造为国内书商接口 |
| edge-patron | 读者自助服务 API | 复用，可接微信服务号/小程序 |
| edge-caiasoft / edge-dematic | 自动化书库(ASRS) | 国内密集书库集成时按需启用 |
| edge-courses / edge-erm / edge-fqm / edge-dcb | 教参/ERM/查询/馆互 | 视业务范围启用 |

### 3.4 OLF 生态项目考察范围

FOLIO 自身不含统一发现、知识库、馆际互借协调、数据分析等外围服务——
这些能力在 OLF（Open Library Foundation）生态中由姊妹开源项目承担。
以下项目一并纳入 cnLSP 考察范围（项目总入口：https://openlibraryfoundation.org/projects/）：

| 项目 | 定位 | 技术/许可 | 与 FOLIO 的集成 | cnLSP 考察重点 |
|---|---|---|---|---|
| **VuFind** | 统一发现层 / 新一代 OPAC | PHP + Apache Solr，GPL；最新 11.x（2026-07 发布 11.1） | 官方 FOLIO 驱动；Texas A&M、芝加哥大学等通过 mod-oai-pmh 小时级增量同步 + 实时可用性 API 对接 | **统一发现的首选候选**：中文界面、CNMARC 索引映射、中文分词（Solr IK）、与微信小程序/门户集成；注意 GPL 与 FOLIO Apache-2.0 的许可差异（VuFind 独立部署、API 交互，不构成衍生作品） |
| **GOKb** | 全球开放知识库（电子资源包/题名级元数据） | Web 应用 + 开放 API，数据 CC0 | 可为 ERM/发现提供知识库数据 | 评估作为中文数据库（CNKI/万方/维普）知识库的参照模型或共建数据源 |
| **Project ReShare / OpenRS** | 馆际互借与资源共享（ILS/发现无关的异构共享） | 微服务，与 FOLIO 同源的 Okapi 系架构 | 与 FOLIO mod-dcb 等衔接 | 二期馆际互借/文献传递的重要候选，或作为对接 CALIS 馆互的参照实现 |
| **LDP**（Library Data Platform） | 图书馆数据分析平台（Metadb 内核，跨域 SQL 分析、历史数据存储） | 开源，社区所有 | 从 FOLIO 抽取数据做报表分析 | 教育部统计报表、馆情分析的数据底座候选（替代/补充 mod-reporting） |
| **BitCurator** | 数字文献策展与保存（born-digital curation） | 工具集 + 社区 | 无直接集成 | 二期特藏数字化与长期保存能力的技术参照 |
| **ORC**（Open Rules for Cataloging） | 开放编目规则项目 | 文档型项目 | — | 关注即可，国内以《中国文献编目规则》/CNMARC 为准 |

**考察结论（初步）**：VuFind + GOKb + ReShare + LDP 与 cnLSP 的业务定位
（统一发现、电子资源、馆际互借、统计报表）高度互补，且与 FOLIO 有成熟集成先例。
一期复刻 FOLIO 时应同步验证 **VuFind ↔ FOLIO** 集成链路（OAI-PMH 收割 + 实时
可用性 + 读者账户 SSO），因为发现层是读者侧门面，中文化体验成败在此。

### 3.5 调研报告借鉴要点（云瀚 2026 报告）

参考资料：《开源图书馆系统生态及其 AI 时代演进——面向云瀚社区的全面调研报告
（2026 发布版）》（已存于 `docs/` 目录）。该报告调研 24 个代表性开源项目，
以下要点直接纳入 cnLSP 设计基准：

1. **Okapi → Eureka 平台换代（最重要修正）**：见 §2 警示框。Sunflower 起权限体系
   已开始从 Okapi permission sets 迁移到 Eureka capabilities/roles，基线与权限
   设计必须面向 Eureka。
2. **FOLIO 中国实践基础**：2018 年起 CALIS 与北大、上交、人大、深大、上图等合作
   探索；北大曾以「FOLIO + 既有 Symphony 叠加」试运行二维码借阅——
   「叠加而非替代」在国内有现实可行性，也印证了 cnLSP 的模块替换策略。
3. **从试点到生产需补五类能力**：中文元数据、国内资源与供应链（出版社/馆配商/
   中文数据库/发票财务适配器）、校园与现场系统（统一身份/门禁/RFID/微信）、
   实施服务体系、数据与模型合规。cnLSP 路线图阶段 2–5 已覆盖前三类，
   **「实施服务产品化」（迁移工具、测试数据、配置模板、中文手册、升级验证）
   需作为一期交付物的显性组成部分**。
4. **元数据转换是第一道硬门槛**：CNMARC ↔ MARC21 不是字段号逐项替换，存在
   一对多拆分、不同年代不同规则的历史数据。cnLSP 应建设**独立的元数据映射与
   验证服务**：每次转换保存源记录、目标记录、映射版本、警告与人工修订，
   支持回放和批量重做（对应路线图阶段 2，需加重投入）。
5. **本地系统对接三路径**（适配器设计原则）：优先 OpenAPI/REST + 事件；
   其次 SIP2、NCIP、Z39.50/SRU、OAI-PMH、OpenURL、KBART、COUNTER/SUSHI 等行业
   协议；最后对无开放接口的存量系统用经授权的批量文件/只读视图/中间交换库，
   **禁止直接写生产库**。
6. **合规边界补充**：除等保与个保法外，面向公众的生成式 AI 服务还涉及
   《生成式人工智能服务管理暂行办法》、2025 年生成合成内容标识制度、
   2026-07-15 施行的《人工智能拟人化互动服务管理暂行办法》（数字馆员/
   角色陪伴类 E 类服务直接相关）。一期若不涉及生成式服务，此项列入二期合规清单。
7. **落地形态参考**：报告提出「存量叠加型 / 开源组合型 / 联盟平台型」三种形态。
   cnLSP 一期对应「开源组合型」（FOLIO + VuFind + 本土适配），
   但产品化时应兼容「存量叠加型」交付（保留汇文/Interlib 等存量系统，
   先接发现与服务层），以匹配国内图书馆的投资周期与风险偏好。
8. **M/I/E 模块分类法**（云瀚 A-LSP）：M 类=现有事务系统的纳入与适配、
   I 类=传统 ILS 未覆盖的增长型业务（智能采集、可信研究服务、阅读运营分析等）、
   E 类=无界体验（数字人/沉浸服务，以可信内容为前提、慎重生长）。
   cnLSP 二期扩展可借用此分类组织自有模块规划。
9. **报告推荐适配优先级**：第一批 FOLIO、Koha、通用协议、DSpace；
   第二批 Evergreen、dp2、VuFind、Omeka S、ArchivesSpace；
   第三批 RERO ILS、InvenioRDM、SLiMS、Aspen、Archivematica。
   其中 **dp2（国产开源 ILS）与 DSpace（机构知识库）值得补充考察**：
   dp2 的国内业务适配经验可直接借鉴，DSpace 是二期特藏/机构库能力的首选基线。

### 3.6 刘炜等（2026）Eureka 架构转型研究的借鉴

参考资料：刘炜、周纲、张磊《图书馆服务平台架构演进与智慧化——以 FOLIO 的
Eureka 架构转型为例》（《图书馆杂志》2026 年第 45 卷第 9 期；原文受版权保护，不随本仓库分发）。
该文以「基础设施能力—服务治理机制—智能化适配能力」三维框架系统对比
Okapi 与 Eureka，对 cnLSP 的借鉴：

1. **Okapi 的结构性局限（复刻时须认清的边界）**
   - 集中式单一网关在高并发/复杂调用下形成性能瓶颈，**限制国家级与城市级
     图书馆的规模化部署**——正好命中 cnLSP 的规模基准（日 3 万流通、高峰并发）；
   - 云原生调度支持有限（传统虚拟机/静态容器，缺自动扩缩容与动态调配）；
   - 自定义令牌机制与 OAuth2/OIDC 企业级身份标准存在兼容性差距，
     对接高校统一认证/城市公共身份平台需额外适配层；
   - 无标准化 M2M（机器对机器）认证，智能体类服务无独立、可审计的系统身份；
   - 面向同步 REST，高频异步与复杂任务编排支持有限；无语义化数据模型原生支持。
2. **Eureka 重构要点 = cnLSP 基线部署的技术清单**
   - Kong 网关 + Kubernetes：动态扩缩容、负载均衡、容灾——对应高校学期初高峰、
     公共馆集中服务时段的弹性需求；
   - **Keycloak 标准化身份（OAuth2/OpenID Connect）**：可直接顺畅对接高校统一
     身份认证、城市公共服务身份平台与跨机构联盟认证——意味着 cnLSP 的
     CARSI/统一认证对接（阶段 3）在 Eureka 下可省去大量自研适配层；
   - Sidecar 边车：通信/认证/流量控制从业务模块剥离，集中异常重试与故障隔离；
   - 标准化 M2M 认证 + capability 细粒度授权：为二期智能体类模块
     （自动编目辅助、智能咨询代理、跨系统数据处理）提供独立身份、权限分级与
     操作可追溯——**cnLSP 二期「沿用相同扩展架构」的技术基础正是这套机制**；
   - 流程编排能力：跨模块任务串联（批量元数据清洗、自动化馆藏同步、
     跨系统资源整合分析），与阶段 2 的元数据映射验证服务设计相契合。
3. **对中国实践的实施路径启示**
   - 建设重心从「功能配置」转向「能力沉淀」：云原生兼容架构、开放接口标准、
     服务治理机制、系统扩展能力应作为平台的长期公共技术资产统筹规划；
   - **分层协同布局**：国家/省级建统一认证 + 元数据规范 + 跨馆接口的区域级
     基础设施；市级馆与高校馆做业务系统模块化改造与云原生适配；基层馆接入
     区域平台共享能力——对 cnLSP 面向城市馆/联盟的产品化交付模式有直接参考
     价值（与 §3.5 的「联盟平台型」落地形态呼应）；
   - **数据治理与平台升级同步**：元数据规范调整、数据质量控制、语义结构优化
     纳入平台工程，避免「表层智能化」；
   - 组织能力：平台化转型需要信息管理 + 数据分析 + 系统工程的复合型团队，
     实施服务体系建设（§3.5 第 3 点）应包含人才与培训机制。

## 4. 版本基线建议

- 当前 snapshot 分支对应 **Trillium (R1-2026)**，属开发中版本，不宜作基线；
- 官方仅维护两个最新稳定版：**Sunflower (R1-2025)** 与 **Ramsons (R2-2024)**；
- **建议基线：Sunflower 的 Eureka 变体**（2026-09-19 修正）：
  - Sunflower 是官方确认完成 Okapi→Eureka 转型的版本，同时提供两种部署变体：
    platform-complete 的 **`R1-2025` 分支 = Eureka 版**（选这个），
    `R1-2025-okapi` 分支 = Okapi 过渡版（不选）；
  - Eureka 时代的平台组合仓库为 **`folio-org/platform-lsp`**（R1-2025 分支），
    以 application（app-platform-minimal / app-platform-complete）为版本管理单位；
  - 详细组件清单、目标部署拓扑与本土化接入点见
    《[cnLSP-Eureka部署拓扑与本土化接入点](./cnLSP-Eureka部署拓扑与本土化接入点.md)》；
- 每年跟随上游升级一次命名版本，升级窗口选在上游发布 CSP（bugfix 累积版）之后。

```bash
git clone --depth 1 -b R1-2025 https://github.com/folio-org/platform-lsp.git
git clone --depth 1 https://github.com/folio-org/eureka-platform-bootstrap.git
```

## 5. 分期战略与路线图

> **分期原则（2026-09-19 确认）**：FOLIO 的空白领域（特藏、空间预约、活动管理、
> 统一发现等）虽然很多，但**第一期只做一件事——完整复刻 FOLIO 并使其本土化**；
> 功能扩展放第二期，且必须沿用同一套扩展架构（Okapi 网关 + ModuleDescriptor
> 接口契约 + 自有 mod-*/ui-* 模块）进行，保证与上游兼容、可持续升级。

### 第一期：本土化复刻 FOLIO（阶段 0–5）

### 阶段 0 · 开发环境就绪（2–4 周）
- 基于 folio-install / 官方单机容器部署指南搭建 Sunflower 基线环境；
- 建立 CI：模块构建、镜像仓库、测试租户初始化脚本；
- 选定首个试点业务域（建议：流通 + 馆藏，避开 ERM 复杂度）。

### 阶段 1 · 中文化（4–8 周）
- 为 65 个前端模块补齐 `zh_CN.json`（react-intl 机制，可机器翻译+人工校订）；
- 后端通知模板（mod-template-engine）中文化；
- 日期/货币/姓名格式（中文姓名顺序、身份证号校验）本地化。

### 阶段 2 · 编目与检索适配（8–12 周）
- **CNMARC 支持**：mod-quick-marc / mod-source-record-storage 的 MARC 校验规则、
  字段映射表扩展（FOLIO 的 MARC 映射本身可配置，工作量集中在映射表与校验）；
- **中图法（CLC）分类**：call-number 类型扩展；
- **中文检索**：mod-search 底层 OpenSearch 增加 IK/jieba 分词与拼音检索；
- Z39.50 套录源配置为 CALIS/国图（mod-copycat、mod-z3950 配置层）。

### 阶段 3 · 业务流对接（8–12 周）
- 身份认证：CARSI / 校园统一认证（mod-login-saml 配置 + 自有 login 模块）；
- 通知通道：新增 mod-notify-sms / mod-notify-wechat（短信、微信服务号模板消息）；
- 费款支付：mod-feesfines 扩展微信/支付宝扫码支付；
- 读者门户：基于 edge-patron / edge-rtac 开发微信小程序与中文 OPAC。

### 阶段 4 · 联盟与采访（8–12 周）
- CALIS 联合目录上载/下载、馆际互借（改造 mod-dcb / edge-ncip）；
- 国内书商采访 EDI（替换 edge-orders 对接层）；
- 中文数据库 ERM 知识库（CNKI/万方/维普 元数据导入）。

### 阶段 5 · 合规与交付（持续）
- 等保二级/三级：审计日志（mod-audit）、数据加密、备份与渗透测试；
- 个保法：读者数据最小化、留存策略、脱敏导出；
- 教育部高校图书馆统计报表（基于 mod-reporting / LDP 构建）。

**第一期完成标志**：在目标规模基准（500 万册 / 日 3 万流通）的压测环境下，
FOLIO 全部现有业务域（编目、流通、采访、ERM、期刊、读者服务、报表）
以中文界面、中国标准、国内对接通道完整可用。

### 第二期：功能扩展（一期验收后启动，本文件不展开）

- 沿用同一扩展架构补齐 FOLIO 空白：特藏与数字化保存、空间/座位预约、
  活动管理、参考咨询、统一发现服务等；
- 扩展模块一律以自有 `mod-cn-*` / `ui-cn-*` 命名并遵守 ModuleDescriptor 契约，
  与上游模块平级部署、独立演进；
- 一期落地过程中应同步沉淀「cnLSP 自有模块开发脚手架与规范」，
  作为二期扩展的工程基础。

## 6. 风险与注意事项

1. **升级策略**：fork 核心模块是最大长期风险，一切本土化优先走
   「配置 > 插件点 > 新增模块 > 最后才 patch 上游」的顺序；
2. **性能基线**：官方单机部署参考配置为最低 8C16G + PostgreSQL 独立部署，
   高校馆生产建议按 Okapi + 每模块 2 副本起步规划；
3. **中文编目深度**：CNMARC 与 MARC21 的字段差异（如 200@ vs 245）需要
   编目专家参与映射表评审，这是纯技术无法闭门完成的部分；
4. **社区借力**：云瀚联盟（calsp.cn）已有中文资料与实施经验，建议尽早建立联系，
   避免重复造轮子。

## 7. 下一步行动清单

- [ ] 切换仓库到 Sunflower（R1-2025-okapi）基线分支
- [ ] 按官方 Single Server 指南完成首次本地部署冒烟
- [ ] 盘点 65 个前端模块的翻译文件现状，估算汉化工作量
- [ ] 调研云瀚联盟已有中文本地化成果，确定可复用范围
- [ ] 部署 VuFind 并验证与 FOLIO 的集成链路（OAI-PMH 收割 + 实时可用性 + 读者 SSO）
- [ ] 评估 Eureka 平台部署拓扑（Kong + Keycloak + Sidecar），确定基线部署形态
- [ ] 补充考察 dp2（国产开源 ILS 的本土业务适配经验）与 DSpace（二期特藏/机构库基线）
- [ ] 精读云瀚 2026 调研报告全文，提炼 M/I/E 模块分类对二期规划的映射
