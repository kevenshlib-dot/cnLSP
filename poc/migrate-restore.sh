#!/usr/bin/env bash
# cnLSP 迁移恢复脚本（在新 MacBook Pro 上运行）
# 前置：已安装 Docker Desktop（Apple Silicon 版）并启动；内存建议调至 20-24GB
# 用法：cd <迁移包目录> && bash migrate-restore.sh [目标工作区父目录]
set -euo pipefail

TARGET_PARENT="${1:-$HOME/Documents/Kimi/Workspaces}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 0. 前置检查
if ! docker info >/dev/null 2>&1; then
  echo "错误: Docker 未运行。请先启动 Docker Desktop。" >&2
  exit 1
fi
if [ "$(uname -m)" != "arm64" ]; then
  echo "错误: 本镜像包为 Apple Silicon (arm64) 构建，当前机器是 $(uname -m)。" >&2
  exit 1
fi
MEM_GB=$(($(docker info --format '{{.MemTotal}}') / 1073741824))
if [ "$MEM_GB" -lt 16 ]; then
  echo "警告: Docker 内存仅 ${MEM_GB}GB，建议调到 20-24GB（Docker Desktop → Settings → Resources）。" >&2
fi

echo "== 1/3 恢复工作区到 ${TARGET_PARENT}/cnLSP =="
mkdir -p "$TARGET_PARENT"
if [ -d "$TARGET_PARENT/cnLSP" ]; then
  echo "  目标已存在，备份为 cnLSP.bak.$(date +%s)"
  mv "$TARGET_PARENT/cnLSP" "$TARGET_PARENT/cnLSP.bak.$(date +%s)"
fi
mkdir -p "$TARGET_PARENT/cnLSP"
tar -xf "$HERE/cnlsp-workspace.tar" -C "$TARGET_PARENT/cnLSP"

echo "== 2/3 导入 Docker 镜像（约 5-10 分钟）=="
docker load -i "$HERE/cnlsp-images-1.tar"
docker load -i "$HERE/cnlsp-images-2.tar"

echo "== 3/3 拉取公共基础设施镜像（多架构官方镜像，无需打包）=="
docker pull postgres:16-alpine &
docker pull apache/kafka-native:4.3.1 &
docker pull nginx:latest &
wait

cat <<EOF

恢复完成！启动平台：

  cd "${TARGET_PARENT}/cnLSP/eureka-platform-bootstrap"
  export JAVA_HOME="\$PWD/../tools/jdk21/Contents/Home"
  export PATH="\$PWD/../tools/bin:\$PWD/../tools/jdk21/Contents/Home/bin:\$PWD/../tools/maven/bin:\$PATH"
  export API_GATEWAY_URL="http://localhost:18000"
  ./start.sh --yes

首次启动会重建租户与用户（约 3-5 分钟）。之后如需恢复 CNMARC 规则配置：
  见 docs/cnLSP-本地运行指南.md §4（跑 poc/poc1-cnmarc-spec.py 即可，幂等）。

注意：如果基础设施镜像的 tag 与 compose 文件要求的不一致，start.sh 会报
镜像缺失，按报错提示 docker pull 对应版本即可（均为公开多架构镜像）。
EOF
