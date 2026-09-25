# cnLSP 迁移指南：搬到 36GB MacBook Pro

> 2026-09-19。从当前机器（48GB，多项目混跑）迁移到专用机器（36GB）。
> 迁移包已生成在 `migration/` 目录（共约 2.8GB）。

## 迁移原理

平台状态 **95% 可脚本化重建**：租户、用户、权限、CNMARC 规则都由
start.sh 和 poc 脚本幂等重建。真正需要搬运的只有：

| 内容 | 文件 | 大小 |
|---|---|---|
| 工作区（文档+PoC 脚本+本地改造后的 bootstrap+工具链 JDK21/Maven/bash5） | cnlsp-workspace.tar | 724MB |
| Docker 镜像批 1（JRE 基座/sidecar/Kong/Keycloak/mgr×3/vault） | cnlsp-images-1.tar | 994MB |
| Docker 镜像批 2（13 个业务模块，全部 arm64 原生） | cnlsp-images-2.tar | 1.1GB |

不需要搬 Docker 数据卷——`./start.sh --yes` + `poc/poc1-cnmarc-spec.py` 会在新机器上
重建全部状态（租户 diku、folio/folio 管理员、CNMARC 字段规则）。

## 新机操作步骤

### 1. 准备工作（约 10 分钟）

1. 安装 **Docker Desktop for Mac（Apple Silicon 版）** 并启动。
2. Docker Desktop → Settings → Resources：
   - **Memory: 20-24 GB**（36GB 物理内存，建议 24576 MiB）
   - 确认 "Use Rosetta for x86_64/amd64 emulation" 保持默认即可（我们用不上模拟）
3. 无需安装 Java/Maven/ Homebrew——工具链已含在工作区 `tools/` 内。

### 2. 传输迁移包

整个 `migration/` 目录（2.8GB）用任意方式传到新机，如：
- AirDrop / 局域网共享 / 移动硬盘
- 或命令行（两台机器同网段）：`scp -r migration/ 新机用户@新机IP:~/`

### 3. 恢复（一条命令）

```bash
cd <迁移包所在目录>/migration
bash migrate-restore.sh        # 默认恢复到 ~/Documents/Kimi/Workspaces/cnLSP
```

脚本会：校验 Docker 运行中 + arm64 → 解包工作区 → 导入 22 个镜像 →
拉取 3 个公共基础设施镜像（postgres/kafka/nginx）。

### 4. 启动并验证

```bash
cd ~/Documents/Kimi/Workspaces/cnLSP/eureka-platform-bootstrap
export JAVA_HOME="$PWD/../tools/jdk21/Contents/Home"
export PATH="$PWD/../tools/bin:$PWD/../tools/jdk21/Contents/Home/bin:$PWD/../tools/maven/bin:$PATH"
export API_GATEWAY_URL="http://localhost:18000"
./start.sh --yes
```

首次启动约 3-5 分钟（重建租户/用户），看到 `Smoke check: passed` 即成功。

### 5. 恢复 CNMARC 规则（可选，2 分钟）

按 `docs/cnLSP-本地运行指南.md` §4 跑一遍 `poc/poc1-cnmarc-spec.py` 即可。

## 注意事项

- **两台机器可同时跑**：端口映射（18000/18080/55432/290xx）与机器无关，不冲突。
- 新机器若 8000/8080 空闲，也可逐步回归官方默认端口，但不建议现在动——
  所有脚本已按重映射后的端口适配。
- 迁移完成后，旧机器的 FOLIO 容器可用 `eureka-platform-bootstrap/stop.sh` 停掉，
  数据卷保留无妨；确认新机稳定后再清理。
- 迁移完成后下一步：在新机上继续**编目链部署**（描述符 0.0.19 已含 6 个新模块定义，
  start.sh 会自动构建这 6 个镜像——36GB 机器内存充裕，一次到位）。

## 故障排查

| 症状 | 处理 |
|---|---|
| `docker info` 报错 | Docker Desktop 没启动 |
| 提示镜像缺失（postgres/kafka/nginx） | 按报错 tag 手动 `docker pull` |
| start.sh 报内存/OOM | 确认 Docker 内存 ≥20GB |
| 脚本兼容性报错 | 确认已 export 工具链 PATH（第 4 步前两行） |
