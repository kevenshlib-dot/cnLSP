#!/usr/bin/env python3
"""流通链模块接口依赖分析：拉取候选模块描述符，计算 requires 的传递闭包，
对照现有 19 模块已提供的接口，输出最小必需集合。"""
import json
import re
import sys
import time
import urllib.request

REG = "https://folio-registry.dev.folio.org/_/proxy/modules/{}"

# 现有 19 模块（0.0.19）
EXISTING = [
    "mod-configuration-5.13.0", "mod-permissions-6.8.0", "mod-tags-3.0.0",
    "mod-users-19.6.0", "mod-users-bl-8.0.0", "mod-password-validator-4.0.0",
    "mod-login-keycloak-4.0.1", "mod-users-keycloak-4.0.2", "mod-roles-keycloak-4.0.4",
    "mod-notes-8.0.0", "mod-scheduler-4.0.2", "mod-settings-1.3.2",
    "mod-record-specifications-2.0.3", "mod-source-record-storage-5.10.15",
    "mod-source-record-manager-3.10.14", "mod-di-converter-storage-2.4.3",
    "mod-inventory-storage-29.0.23", "mod-entities-links-4.0.3", "mod-quick-marc-7.0.0",
]

# 流通链候选（R1-2025 Sunflower 版本线）
CANDIDATES = [
    "mod-circulation-24.4.20", "mod-circulation-storage-17.4.3",
    "mod-feesfines-19.3.3", "mod-patron-blocks-1.12.3",
    "mod-patron-6.3.6", "mod-notify-3.4.1", "mod-sender-1.14.2",
    "mod-email-1.19.1", "mod-template-engine-1.22.2",
    "mod-calendar-3.3.1", "mod-pubsub-2.16.3", "mod-audit-2.11.5",
    "mod-inventory-21.1.20",
]


def fetch(mid):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(REG.format(mid), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 3:
                print(f"  ! {mid} 拉取失败: {e}")
                return None
            time.sleep(2 * (attempt + 1))


def provides(md):
    return {(i["id"], i["version"]) for i in md.get("provides", [])}


def main():
    desc = {}
    for mid in EXISTING + CANDIDATES:
        md = fetch(mid)
        if md:
            desc[mid] = md
    print(f"描述符拉取: {len(desc)}/{len(EXISTING)+len(CANDIDATES)}")

    def satisfies(req_id, req_ver, provider_set):
        # require 的 version 字段可含空格分隔的多个可接受版本（任一满足即可）
        for alt in req_ver.split():
            parts = alt.split(".")
            req_major, req_minor = parts[0], int(parts[1]) if len(parts) > 1 else 0
            for pid, pver in provider_set:
                if pid == req_id:
                    pp = pver.split(".")
                    if pp[0] == req_major and (int(pp[1]) if len(pp) > 1 else 0) >= req_minor:
                        return True
        return False

    existing_provides = set()
    for mid in EXISTING:
        if mid in desc:
            existing_provides |= provides(desc[mid])

    print("\n== 各候选模块的 requires 满足情况 ==")
    all_missing = {}
    for mid in CANDIDATES:
        md = desc.get(mid)
        if not md:
            continue
        missing = []
        for r in md.get("requires", []):
            if not satisfies(r["id"], r["version"], existing_provides):
                missing.append((r["id"], r["version"]))
        print(f"\n{mid}: requires {len(md.get('requires', []))} 个接口, 未满足 {len(missing)}")
        for rid, rver in missing:
            print(f"    缺 {rid} {rver}")
        all_missing[mid] = missing

    # 汇总：哪些缺口能由候选集内部互相满足
    cand_provides = set()
    for mid in CANDIDATES:
        if mid in desc:
            cand_provides |= provides(desc[mid])
    print("\n== 候选集内部可满足的缺口 ==")
    for mid, missing in all_missing.items():
        for rid, rver in missing:
            inner = satisfies(rid, rver, cand_provides)
            print(f"  {mid} 缺 {rid} {rver}: {'候选集内可解决' if inner else '★ 需额外模块'}")


if __name__ == "__main__":
    main()
