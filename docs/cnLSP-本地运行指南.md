# cnLSP 本地运行指南

> 更新于 2026-09-19。适用环境：macOS Apple Silicon + Docker Desktop（≥12GB 内存）。

## 1. 启动 FOLIO Eureka 平台

```bash
cd <cnLSP 根目录>/eureka-platform-bootstrap

# 每次开新终端都要先执行这两行环境设置（指向仓库自带工具链）
export JAVA_HOME="$PWD/../tools/jdk21/Contents/Home"
export PATH="$PWD/../tools/bin:$PWD/../tools/jdk21/Contents/Home/bin:$PWD/../tools/maven/bin:$PATH"
export API_GATEWAY_URL="http://localhost:18000"

./start.sh --yes
```

- 全程幂等，已部署时约 20 秒跑完；末尾出现 `Smoke check: passed` 即成功。
- 停止平台：`./stop.sh`（数据保留在 Docker volume 中，下次启动原样恢复）。

## 2. 访问入口

| 入口 | 地址 | 说明 |
|---|---|---|
| API 网关 | http://localhost:18000 | 所有模块 API 统一入口 |
| Keycloak 管理台 | http://localhost:18080/admin | admin / admin |
| 租户 | `diku` | 默认租户 |
| 平台管理员 | `folio` / `folio` | 已分配全部 269 项权限 |

注意：本机端口做过重映射（官方默认 8000/8080 被其他项目占用），
网关是 **18000**、Keycloak 是 **18080**，不是官方文档里的 8000/8080。

## 3. 快速验证 API 可用

```bash
# 登录拿用户令牌（10 分钟有效，过期重跑这行即可）
TOKEN=$(curl -s -X POST "http://localhost:18000/authn/login" \
  -H "x-okapi-tenant: diku" -H "Content-Type: application/json" \
  -d '{"username":"folio","password":"folio"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['okapiToken'])")

# 例：查询 MARC 规格列表
curl -s "http://localhost:18000/specification-storage/specifications" \
  -H "x-okapi-tenant: diku" -H "x-okapi-token: $TOKEN" | python3 -m json.tool | head
```

## 4. 运行 PoC-1（CNMARC 规则配置 + 验证）

```bash
cd <cnLSP 根目录>

# 4.1 刷新令牌（脚本从 /tmp/user-token.txt 读令牌）
curl -s -X POST "http://localhost:18000/authn/login" \
  -H "x-okapi-tenant: diku" -H "Content-Type: application/json" \
  -d '{"username":"folio","password":"folio"}' \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['okapiToken'])" > /tmp/user-token.txt

# 4.2 配置 CNMARC 核心字段（幂等，已配置的字段会跳过）
python3 poc/poc1-cnmarc-spec.py

# 4.3 导出当前规格（含全部字段/子字段/指示符/规则）
SPEC=6eefa4c6-bbf7-4845-ad82-de7fc4abd0e3
curl -s "http://localhost:18000/specification-storage/specifications/$SPEC?include=all" \
  -H "x-okapi-tenant: diku" -H "x-okapi-token: $(cat /tmp/user-token.txt)" > /tmp/spec-full.json

# 4.4 运行验证实验（用官方验证器库验证两条 CNMARC 测试记录）
cd poc/validator-harness
export JAVA_HOME="<cnLSP 根目录>/tools/jdk21/Contents/Home"
export PATH="<cnLSP 根目录>/tools/maven/bin:$JAVA_HOME/bin:$PATH"
mvn -q compile exec:java -Dexec.args="/tmp/spec-full.json"
```

预期输出：记录 A（合规 CNMARC）`✓ 验证通过`；记录 B 报 `missingSubfield 200[0]$a[0]`。

## 5. 常见问题

- **401 Unauthorized**：令牌 10 分钟过期，重新执行 4.1 的登录命令。
- **脚本报 `command not found: bash` 版本错误**：确认已执行第 1 节的 PATH 导出
  （官方脚本需要 bash 5，macOS 自带 bash 3.2 不兼容）。
- **端口被占**：本指南的端口映射表见部署文档 §7.1；若再有冲突需同步改
  compose 文件与脚本中的四处端口。
- **模块容器反复重启（exit 137）**：内存不足 OOM。在
  `docker/docker-compose.minimal.module.yml` 中给对应模块加 768m 限制
  （mod-roles-keycloak、mod-record-specifications 已调过）。
