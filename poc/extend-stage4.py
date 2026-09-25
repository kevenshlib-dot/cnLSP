#!/usr/bin/env python3
"""把采购/期刊链 11 模块加入描述符（0.0.20→0.0.21）与两份 compose 文件。幂等。

特殊配置（依据官方 eureka-cli config.combined.yaml / config.erm.yaml）：
- mod-orders / mod-invoice: disable-system-user（同 mod-pubsub 的 5 个 env）
- mod-finance-storage: use-vault（vault-env）
- mod-serials-management: private-port 8080（Grails/Spring Boot）
"""
import json
import re
from pathlib import Path

ROOT = str(Path(__file__).resolve().parent.parent / "eureka-platform-bootstrap")
DESC = f"{ROOT}/descriptors/app-platform-minimal/descriptor.json"
MOD_COMPOSE = f"{ROOT}/docker/docker-compose.minimal.module.yml"
SC_COMPOSE = f"{ROOT}/docker/docker-compose.minimal.sidecar.yml"

NEW_MODULES = [
    "mod-orders-storage-13.9.8", "mod-orders-13.0.10",
    "mod-invoice-storage-6.0.1", "mod-invoice-6.0.4",
    "mod-finance-5.1.3", "mod-finance-storage-8.8.8",
    "mod-organizations-storage-4.9.2", "mod-organizations-2.1.1",
    "mod-courses-1.4.13", "mod-oai-pmh-3.15.4",
    "mod-serials-management-2.0.5",
]
BASE_PORT = 29050  # 模块 HTTP 29050-29060 / 调试 10050-10060 / sidecar 19050-19060、11050-11060

DISABLE_SU = {"mod-orders", "mod-invoice"}
VAULT = {"mod-finance-storage"}
PRIVATE_PORT = {"mod-serials-management": 8080}
BIG_MEM = {"mod-serials-management": 768, "mod-orders": 512}


def env_prefix(mid):
    name = re.sub(r"-\d.*$", "", mid)
    return name.upper().replace("-", "_")


def main():
    # ---- 1. 描述符 ----
    d = json.load(open(DESC))
    existing = {m["id"] for m in d["modules"]}
    added = 0
    for mid in NEW_MODULES:
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
        d["id"] = "app-platform-minimal-0.0.21"
        d["version"] = "0.0.21"
        d["description"] = ("Minimal FOLIO platform + record-specifications + "
                            "MARC catalog chain + circulation chain + "
                            "acquisitions/serials chain (cnLSP stage 4)")
        json.dump(d, open(DESC, "w"), indent=1, ensure_ascii=False)
        open(DESC, "a").write("\n")
    print(f"描述符: 新增 {added}，共 {len(d['modules'])}，版本 {d['version']}")

    # ---- 2. 模块 compose ----
    mc = open(MOD_COMPOSE).read()
    blocks = []
    mc_added = 0
    for i, mid in enumerate(NEW_MODULES):
        name = re.sub(r"-\d.*$", "", mid)
        if f"container_name: {name}" in mc:
            continue
        p = BASE_PORT + i
        envp = env_prefix(mid)
        listen = PRIVATE_PORT.get(name, 8081)
        block = f"""
  {name}:
    <<: *folio-module
    container_name: {name}
    image: ${{{envp}_IMAGE}}
    profiles: [ app-platform-minimal ]
    ports:
      - "{p}:{listen}"
      - "{p - 19000}:5005"
"""
        extras = []
        if name in PRIVATE_PORT:
            block += f"""    healthcheck:
      test: [ "CMD-SHELL", "wget -q --spider http://localhost:{listen}/admin/health || exit 1" ]
      interval: 30s
      timeout: 10s
      retries: 10
      start_period: 60s
"""
        if name in DISABLE_SU:
            extras.append(f"""      # 官方 eureka-cli 标 disable-system-user
      FOLIO_SYSTEM_USER_ENABLED: "false"
      SYSTEM_USER_CREATE: "false"
      SYSTEM_USER_ENABLED: "false"
      SYSTEM_USER_NAME: {name}
      SYSTEM_USER_USERNAME: {name}""")
        env_lines = ""
        if name in VAULT or extras:
            merge = "[ *folio-module-env, *vault-env ]" if name in VAULT else "*folio-module-env"
            env_lines = f"    environment:\n      <<: {merge}\n"
            if extras:
                env_lines += "\n".join(extras) + "\n"
        block += env_lines
        if name in BIG_MEM:
            block += f"""    deploy:
      resources:
        limits:
          memory: {BIG_MEM[name]}m
        reservations:
          memory: 384m
"""
        blocks.append(block)
        mc_added += 1
    if blocks:
        if not mc.endswith("\n"):
            mc += "\n"
        mc += "".join(blocks)
        open(MOD_COMPOSE, "w").write(mc)
    print(f"模块 compose: 新增 {mc_added} 个服务块")

    # ---- 3. sidecar compose ----
    sc = open(SC_COMPOSE).read()
    sblocks = []
    sc_added = 0
    for i, mid in enumerate(NEW_MODULES):
        name = re.sub(r"-\d.*$", "", mid)
        sname = name.replace("mod-", "sc-", 1)
        if f"container_name: {sname}" in sc:
            continue
        p = BASE_PORT + i
        envp = env_prefix(mid)
        listen = PRIVATE_PORT.get(name, 8081)
        sblocks.append(f"""
  {sname}:
    <<: *sidecar-module
    container_name: {sname}
    profiles: [ app-platform-minimal ]
    ports:
      - "{p - 10000}:8081"
      - "{p - 18000}:5005"
    environment:
      <<: *sidecar-env
      MODULE_NAME: {name}
      MODULE_VERSION: ${{{envp}_VERSION}}
      MODULE_URL: http://{name}:{listen}
      SIDECAR_URL: http://{sname}:8081
""")
        sc_added += 1
    if sblocks:
        if not sc.endswith("\n"):
            sc += "\n"
        sc += "".join(sblocks)
        open(SC_COMPOSE, "w").write(sc)
    print(f"sidecar compose: 新增 {sc_added} 个服务块")


if __name__ == "__main__":
    main()
