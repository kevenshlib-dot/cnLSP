# cnLSP — 基于 FOLIO 的中国本土化图书馆服务平台（实验项目）

**cnLSP**（China Library Services Platform）是一个实验性的长期开发项目：以开源图书馆服务平台
[FOLIO](https://www.folio.org/)（Apache 2.0）为基线，在**不改内核**的前提下，
以模块替换 / 新增与配置层完成中国本土化（CNMARC、中图法、中文流通规则、本土系统对接等）。

> ⚠️ 实验阶段。目前仅在单台 macOS Apple Silicon 开发机上验证，不适合生产使用。

## 技术基线

- FOLIO **Sunflower（R1-2025）Eureka 架构**：Kong 网关 + Keycloak 认证 + mgr-applications /
  mgr-tenants / mgr-tenant-entitlements 管理面 + 每模块一个 sidecar
- 部署编排：官方 [eureka-platform-bootstrap](https://github.com/folio-org/eureka-platform-bootstrap)
  的本地改造版，见 fork：
  [kevenshlib-dot/eureka-platform-bootstrap `cnlsp` 分支](https://github.com/kevenshlib-dot/eureka-platform-bootstrap/tree/cnlsp)
- 全部模块镜像为本地构建的 ARM64 原生镜像（官方未提供）

## 进展

| 阶段 | 内容 | 状态 |
|---|---|---|
| 一 | Eureka 最小平台（13 模块）+ **PoC-1**：CNMARC 字段规则零代码配置（200/205/215/606/690/701） | ✅ |
| 二 | 编目链 6 模块（SRS / SRM / inventory-storage / quick-marc 等）+ **PoC-2**：中图法索书号 + CNMARC 端到端 | ✅ |
| 三 | 流通链 15 模块 + **PoC-3**：中文流通规则端到端（借还、逾期罚款） | ✅（34 模块） |
| 四 | 采购 / 期刊链 11 模块（orders / invoice / finance / organizations / courses / oai-pmh / serials） | 🟡 描述符已至 0.0.21，受限于内存尚未完成授权与验证 |

主要本土化发现与技术债务见 `docs/` 下各阶段部署记录，例如：流通规则 DSL 的 `NAME` 词法仅支持 ASCII，
需改造 mod-circulation 文法才能直接使用中文名。

## 仓库结构

```
cnLSP/
├── docs/                    架构分析、部署拓扑、各阶段部署记录、运行 / 迁移指南（中文）
└── poc/
    ├── poc1-cnmarc-spec.py        PoC-1 CNMARC 规格配置（幂等）
    ├── poc2-clc-e2e.py            PoC-2 中图法 + CNMARC 编目链端到端
    ├── poc3-circulation-e2e.py    PoC-3 中文流通规则端到端
    ├── circ-deps.py / acq-deps.py 模块接口依赖闭包分析
    ├── extend-stage3/4.py         向描述符与 compose 追加模块（幂等）
    ├── load-permissions.py        向 mod-permissions 灌入模块 permissionSets
    ├── descriptors/               所用模块的 ModuleDescriptor 快照
    ├── validator-harness/         CNMARC 规则验证工装（Java + 官方 validator 库）
    └── migrate-*.sh               整机迁移导出 / 恢复
```

## 快速开始

### 1. 硬件与环境

- macOS Apple Silicon，Docker Desktop（Compose ≥ 2.24）
- **Docker 内存：34 模块约需 20GB；45 模块（阶段四）建议分配 ≥ 32GB**（实测 23.4GB 不足）
- JDK 21（及 JDK 17）、Maven 3.9、bash 5、Python ≥ 3.10、jq、curl
  （开发机使用 OpenJDK 21.0.12 / 17.0.20、Maven 3.9.9、GNU bash 5.2.37）

### 2. 获取代码

```bash
git clone https://github.com/kevenshlib-dot/cnLSP.git
cd cnLSP
git clone -b cnlsp https://github.com/kevenshlib-dot/eureka-platform-bootstrap.git
```

`poc/` 下的脚本按相对路径查找 `eureka-platform-bootstrap/`，两者需放在同一目录下。
`docs/cnLSP-本地运行指南.md` 中假定工具链位于 `tools/`（jdk21、maven、bin/bash），
可自行放置，或改用系统已安装的工具。

### 3. 启动与验证

```bash
cd eureka-platform-bootstrap
export API_GATEWAY_URL="http://localhost:18000"
./start.sh --yes          # 幂等；末尾出现 "Smoke check: passed" 即成功
```

- 网关 `http://localhost:18000`，Keycloak `http://localhost:18080`（端口已重映射，非官方默认值）
- 租户 `diku`，管理员 `folio / folio`（仅限本地开发环境的默认凭据）
- 常见问题：网关 502 但模块直连正常 → `docker restart api-gateway`

详见 [docs/cnLSP-本地运行指南.md](docs/cnLSP-本地运行指南.md)。

## 文档索引

- [架构分析与本土化路线图](docs/cnLSP-架构分析与本土化路线图.md)
- [Eureka 部署拓扑与本土化接入点](docs/cnLSP-Eureka部署拓扑与本土化接入点.md)
- [第一阶段：部署现状与技术债务](docs/cnLSP-部署现状与技术债务.md)
- [第二阶段：编目链](docs/cnLSP-第二阶段部署记录-编目链.md)
- [第三阶段：流通链](docs/cnLSP-第三阶段部署记录-流通链.md)
- [本地运行指南](docs/cnLSP-本地运行指南.md) · [迁移指南](docs/cnLSP-迁移指南.md)

## 参考资料

- 刘炜、周纲、张磊.《图书馆服务平台架构演进与智慧化——以 FOLIO 的 Eureka 架构转型为例》.
  《图书馆杂志》, 2026, 45(9).
- 《开源图书馆系统生态及其 AI 时代演进——面向云瀚社区的全面调研报告》（2026 发布版）.

以上资料受版权保护，本仓库不分发原文。

## 许可

本仓库原创内容以 [Apache License 2.0](LICENSE) 发布。FOLIO 及其各模块版权归
Open Library Foundation 及相应贡献者所有，同样以 Apache 2.0 授权。
