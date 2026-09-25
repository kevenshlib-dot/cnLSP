#!/usr/bin/env bash
# cnLSP 迁移导出脚本（在旧机器上运行）
# 产物：migration/ 目录，含工作区归档 + Docker 镜像归档 + 恢复脚本
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$WS/migration"
mkdir -p "$OUT"

echo "== 1/3 打包工作区（docs/poc/tools/bootstrap/platform-lsp）=="
cd "$WS"
tar -cf "$OUT/cnlsp-workspace.tar" docs poc tools eureka-platform-bootstrap platform-lsp
echo "  工作区归档: $(du -h "$OUT/cnlsp-workspace.tar" | cut -f1)"

echo "== 2/3 导出 Docker 镜像（共享层去重，批 1/2）=="
docker save -o "$OUT/cnlsp-images-1.tar" \
  folioci/alpine-jre-openjdk17:latest folioci/alpine-jre-openjdk21:latest \
  folioci/folio-module-sidecar:latest folioci/folio-kong:latest folioci/folio-keycloak:latest \
  folio-vault:1.13.3 \
  folioci/mgr-tenants:latest folioci/mgr-applications:latest folioci/mgr-tenant-entitlements:latest
echo "  批 1: $(du -h "$OUT/cnlsp-images-1.tar" | cut -f1)"

echo "== 3/3 导出 Docker 镜像（批 2/2：13 个业务模块）=="
docker save -o "$OUT/cnlsp-images-2.tar" \
  folioorg/mod-configuration:5.13.0 folioorg/mod-login-keycloak:4.0.1 \
  folioorg/mod-notes:8.0.0 folioorg/mod-password-validator:4.0.0 \
  folioorg/mod-permissions:6.8.0 folioorg/mod-record-specifications:2.0.3 \
  folioorg/mod-roles-keycloak:4.0.4 folioorg/mod-scheduler:4.0.2 \
  folioorg/mod-settings:1.3.2 folioorg/mod-tags:3.0.0 \
  folioorg/mod-users-bl:8.0.0 folioorg/mod-users-keycloak:4.0.2 folioorg/mod-users:19.6.0
echo "  批 2: $(du -h "$OUT/cnlsp-images-2.tar" | cut -f1)"

cp "$WS/poc/migrate-restore.sh" "$OUT/"
echo
echo "导出完成。迁移包内容："
ls -lh "$OUT"
