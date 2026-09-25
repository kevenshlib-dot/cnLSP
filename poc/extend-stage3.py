#!/usr/bin/env python3
"""把流通链 15 模块加入描述符（0.0.19→0.0.20）与两份 compose 文件。幂等。"""
import json
import re
import sys
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent.parent / "eureka-platform-bootstrap")
DESC = f"{ROOT}/descriptors/app-platform-minimal/descriptor.json"
MOD_COMPOSE = f"{ROOT}/docker/docker-compose.minimal.module.yml"
SC_COMPOSE = f"{ROOT}/docker/docker-compose.minimal.sidecar.yml"

# (模块id, 起始端口偏移) 端口分配：模块 2902x/1002x，sidecar 1902x/1102x
NEW_MODULES = [
    "mod-circulation-storage-17.4.3", "mod-circulation-24.4.20",
    "mod-feesfines-19.3.3", "mod-patron-blocks-1.12.3",
    "mod-patron-6.3.6", "mod-notify-3.4.1",
    "mod-sender-1.14.2", "mod-email-1.19.1",
    "mod-template-engine-1.22.2", "mod-calendar-3.3.1",
    "mod-pubsub-2.16.3", "mod-audit-2.11.5",
    "mod-inventory-21.1.20", "mod-event-config-2.9.1",
    "mod-batch-print-1.3.0",
]
BASE_PORT = 29020  # 依次递增

def env_prefix(mid):
    name = re.sub(r"-\d.*$", "", mid)          # mod-quick-marc-7.0.0 -> mod-quick-marc
    return name.upper().replace("-", "_")      # -> MOD_QUICK_MARC（与 run.py 一致）

def main():
    # ---- 1. 描述符 ----
    d = json.load(open(DESC))
    existing = {m["id"] for m in d["modules"]}
    added = 0
    for i, mid in enumerate(NEW_MODULES):
        if mid in existing:
            continue
        name = re.sub(r"-\d.*$", "", mid)
        ver = mid[len(name) + 1:]
        d["modules"].append({
            "id": mid, "name": name, "version": ver,
            "url": f"https://folio-registry.dev.folio.org/_/proxy/modules/{mid}",
        })
        added += 1
    if added:
        d["id"] = "app-platform-minimal-0.0.20"
        d["version"] = "0.0.20"
        d["description"] = ("Minimal FOLIO platform + record-specifications + "
                            "MARC catalog chain + circulation chain (cnLSP stage 3)")
        json.dump(d, open(DESC, "w"), indent=1, ensure_ascii=False)
        open(DESC, "a").write("\n")
    print(f"描述符: 新增 {added} 个模块，现共 {len(d['modules'])} 个，版本 {d['version']}")

    # ---- 2. 模块 compose ----
    mc = open(MOD_COMPOSE).read()
    mc_added = 0
    blocks = []
    for i, mid in enumerate(NEW_MODULES):
        name = re.sub(r"-\d.*$", "", mid)
        if f"{name}:" in mc and f"container_name: {name}" in mc:
            continue
        p = BASE_PORT + i
        envp = env_prefix(mid)
        blocks.append(f"""
  {name}:
    <<: *folio-module
    container_name: {name}
    image: ${{{envp}_IMAGE}}
    profiles: [ app-platform-minimal ]
    ports:
      - "{p}:8081"
      - "{p - 19000}:5005"
""")
        mc_added += 1
    if blocks:
        # 插到文件末尾 services 区（compose yaml 顶层 services 下，直接追加即可）
        if not mc.endswith("\n"):
            mc += "\n"
        mc += "".join(blocks)
        open(MOD_COMPOSE, "w").write(mc)
    print(f"模块 compose: 新增 {mc_added} 个服务块")

    # ---- 3. sidecar compose ----
    sc = open(SC_COMPOSE).read()
    sc_added = 0
    blocks = []
    for i, mid in enumerate(NEW_MODULES):
        name = re.sub(r"-\d.*$", "", mid)
        scname = name.replace("mod-", "sc-", 1)
        if f"sc-{scname}:" in sc or f"{scname}:" in sc:
            continue
        p = BASE_PORT + i
        envp = env_prefix(mid)
        blocks.append(f"""
  {scname}:
    <<: *sidecar-module
    container_name: {scname}
    profiles: [ app-platform-minimal ]
    ports:
      - "{p - 10000}:8081"
      - "{p - 18000}:5005"
    environment:
      <<: *sidecar-env
      MODULE_NAME: {name}
      MODULE_VERSION: ${{{envp}_VERSION}}
      MODULE_URL: http://{name}:8081
      SIDECAR_URL: http://{scname}:8081
""")
        sc_added += 1
    if blocks:
        if not sc.endswith("\n"):
            sc += "\n"
        sc += "".join(blocks)
        open(SC_COMPOSE, "w").write(sc)
    print(f"sidecar compose: 新增 {sc_added} 个服务块")

if __name__ == "__main__":
    main()
