#!/usr/bin/env python3
"""将全部模块的 permissionSets 灌入 mod-permissions（模拟 Okapi 时代的
/_/tenantPermissions 注册，补上 Eureka minimal 平台缺失的权限注册环节）。
幂等：重复执行安全（mod-permissions 按 moduleId 替换）。"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "descriptors")
os.makedirs(CACHE, exist_ok=True)

GW = "http://localhost:29003"  # mod-permissions 直连（/_/* 系统端点无网关路由；docker port mod-permissions 实测为 29003）
TENANT = "diku"
DESCRIPTOR = str(Path(__file__).resolve().parent.parent / "eureka-platform-bootstrap"
                 / "descriptors/app-platform-minimal/descriptor.json")


def req(method, url, token=None, tenant=None, body=None, retries=3):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["x-okapi-token"] = token
    if tenant:
        headers["x-okapi-tenant"] = tenant
    last = None
    for attempt in range(retries):
        r = urllib.request.Request(url, method=method, headers=headers,
                                   data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(r, timeout=60) as resp:
                t = resp.read().decode()
                return resp.status, json.loads(t) if t else {}
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception as e:  # 网络抖动：SSL EOF / 超时等，重试
            last = e
            time.sleep(2 * (attempt + 1))
    raise last


def main():
    token = open("/tmp/user-token.txt").read().strip()
    d = json.load(open(DESCRIPTOR))
    ok, failed = 0, 0
    for m in d["modules"]:
        cache_file = os.path.join(CACHE, f"{m['id']}.json")
        if os.path.exists(cache_file):
            md = json.load(open(cache_file))
        else:
            s, md = req("GET", m["url"])
            if s >= 300:
                print(f"  x {m['id']} 描述符拉取失败 HTTP {s}")
                failed += 1
                continue
            json.dump(md, open(cache_file, "w"))
        perms = md.get("permissionSets", [])
        if not perms:
            print(f"  - {m['id']} 无权限集，跳过")
            continue
        payload = {"moduleId": m["id"], "perms": perms}
        s2, resp = req("POST", f"{GW}/_/tenantpermissions", token, TENANT, payload)
        if s2 < 300:
            print(f"  + {m['id']}: {len(perms)} 个权限集已注册")
            ok += 1
        else:
            print(f"  x {m['id']}: HTTP {s2} {json.dumps(resp, ensure_ascii=False)[:150]}")
            failed += 1
    print(f"\n完成: 成功 {ok}，失败 {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
