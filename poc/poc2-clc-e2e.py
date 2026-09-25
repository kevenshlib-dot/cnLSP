#!/usr/bin/env python3
"""PoC-2: 中图法（CLC）索书号 + CNMARC 端到端验证。

两部分：
1) 编目规范验证：向 mod-quick-marc 的 POST /records-editor/validate 提交
   含 CNMARC 字段（010/200/690）的书目记录，验证 PoC-1 注册的 CNMARC 规则
   确实生效（690$a 中图法分类号合法；未定义的字段如 133 应被标记）。
   注意：该端点的字段 content 必须是字符串（"$a xxx $b yyy" 格式），
   传 Map 会触发上游缺陷（010 LCCN 填充器 Map.toString 崩溃 500；
   其他字段报 "Invalid converter" 400）。
2) 馆藏存储验证：补齐 0.0.19 升级未加载的参考数据（实例类型/标识符类型/
   位置四级结构），创建带"中图法/CLC"索书号类型的 instance + holdings，
   回读验证持久化（mod-inventory-storage）。
"""
import json
import sys
import urllib.request
import uuid

GW = "http://localhost:18000"
TENANT = "diku"
CLC_TYPE_NAME = "中国图书馆分类法（中图法/CLC）"


def req(method, path, token, body=None):
    headers = {"Content-Type": "application/json", "x-okapi-tenant": TENANT}
    if token:
        headers["x-okapi-token"] = token
    r = urllib.request.Request(
        f"{GW}{path}", method=method, headers=headers,
        data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            t = resp.read().decode()
            return resp.status, json.loads(t) if t else {}
    except urllib.error.HTTPError as e:
        t = e.read().decode()
        try:
            return e.code, json.loads(t)
        except json.JSONDecodeError:
            return e.code, {"raw": t[:300]}


def login():
    s, d = req("POST", "/authn/login", None, {"username": "folio", "password": "folio"})
    assert s in (200, 201), f"登录失败: {s} {d}"
    return d["okapiToken"]


def ensure_ref(token, list_path, list_key, name_field, name_value, payload):
    """幂等创建参考数据，返回 id。"""
    s, d = req("GET", f"{list_path}?limit=500", token)
    assert s == 200, f"查询 {list_path} 失败: {s} {d}"
    for item in d.get(list_key, []):
        if item.get(name_field) == name_value:
            return item["id"]
    payload.setdefault("id", str(uuid.uuid4()))
    s, d = req("POST", list_path, token, payload)
    assert s in (200, 201), f"创建 {list_path} 失败: {s} {json.dumps(d, ensure_ascii=False)[:300]}"
    return d.get("id", payload["id"])


def main():
    token = login()
    failures = 0

    # ---------- 第一部分：CNMARC 记录验证 ----------
    print("== 1. CNMARC 记录验证（quick-marc /records-editor/validate）==")
    cnmarc_record = {
        "marcFormat": "BIBLIOGRAPHIC",
        "leader": "00000nam a2200000 a 4500",
        "fields": [
            {"tag": "001", "content": "CNLSP2026001"},
            {"tag": "010", "content": "$a 978-7-302-65432-1 $d CNY 68.00"},
            {"tag": "200", "indicators": ["1", " "],
             "content": "$a 智慧图书馆概论 $f 张三 主编"},
            {"tag": "690", "content": "$a G250.76 $v 5"},
        ],
    }
    s, d = req("POST", "/records-editor/validate", token, cnmarc_record)
    issues = d.get("issues", []) if isinstance(d, dict) else []
    bad = [i for i in issues if i.get("tag", "")[:3] in ("010", "200", "690")]
    if s == 200 and not bad:
        print("  ✓ 010/200/690 全部通过 CNMARC 规则校验（中图法分类号 G250.76 合法）")
    else:
        print(f"  ✗ HTTP {s}: {json.dumps(d, ensure_ascii=False)[:400]}")
        failures += 1

    bad_record = dict(cnmarc_record)
    bad_record["fields"] = cnmarc_record["fields"] + [
        {"tag": "133", "content": "$a 规范外字段"}]
    s2, d2 = req("POST", "/records-editor/validate", token, bad_record)
    issues2 = d2.get("issues", []) if isinstance(d2, dict) else []
    flagged = any(i.get("tag", "").startswith("133") and "undefined" in i.get("message", "").lower()
                  for i in issues2)
    if flagged:
        print("  ✓ 对照组字段 133 被正确标记为 undefined（规格严格校验生效）")
    else:
        print(f"  ✗ 未定义字段 133 未被标记: {json.dumps(d2, ensure_ascii=False)[:300]}")
        failures += 1

    # ---------- 第二部分：CLC 索书号馆藏存储 ----------
    print("== 2. CLC 索书号 instance + holdings 存储（mod-inventory-storage）==")
    s, d = req("GET", "/call-number-types?limit=100", token)
    clc = next((t for t in d.get("callNumberTypes", []) if CLC_TYPE_NAME in t["name"]), None)
    if not clc:
        print("  ✗ 中图法索书号类型不存在")
        sys.exit(1)
    clc_id = clc["id"]
    print(f"  中图法类型 ID: {clc_id}")

    # 参考数据（0.0.19 PUT 升级未带 loadReference，需幂等补齐）
    it_id = ensure_ref(token, "/instance-types", "instanceTypes", "code", "text",
                       {"name": "text", "code": "text", "source": "local"})
    idt_id = ensure_ref(token, "/identifier-types", "identifierTypes", "name", "ISBN",
                        {"name": "ISBN", "source": "local"})
    inst_ = ensure_ref(token, "/location-units/institutions", "locinsts", "code", "LOCAL",
                       {"name": "本地馆", "code": "LOCAL"})
    camp = ensure_ref(token, "/location-units/campuses", "loccamps", "code", "MAIN",
                      {"name": "总馆", "code": "MAIN", "institutionId": inst_})
    lib = ensure_ref(token, "/location-units/libraries", "loclibs", "code", "MAIN",
                     {"name": "总馆", "code": "MAIN", "campusId": camp})
    sp = ensure_ref(token, "/service-points", "servicepoints", "code", "MAIN-CD",
                    {"name": "总馆流通台", "code": "MAIN-CD",
                     "discoveryDisplayName": "总馆流通台"})
    src = ensure_ref(token, "/holdings-sources", "holdingsRecordsSources", "name", "本地",
                     {"name": "本地", "source": "local"})
    loc = ensure_ref(token, "/locations", "locations", "code", "MAIN-ST",
                     {"name": "总馆书库", "code": "MAIN-ST", "primaryServicePoint": sp,
                      "institutionId": inst_, "campusId": camp, "libraryId": lib,
                      "servicePointIds": [sp]})
    print("  参考数据就绪（实例类型/标识符类型/位置/服务点）")

    inst_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "cnlsp://poc2/instance"))
    inst = {
        "id": inst_id,
        "title": "智慧图书馆概论 / 张三 主编",
        "source": "CNMARC-PoC",
        "instanceTypeId": it_id,
        "identifiers": [{"value": "978-7-302-65432-1", "identifierTypeId": idt_id}],
    }
    s, d = req("POST", "/instance-storage/instances", token, inst)
    if s not in (200, 201):
        s, d = req("GET", f"/instance-storage/instances/{inst_id}", token)
    if s not in (200, 201):
        print(f"  ✗ 实例创建失败 HTTP {s}: {json.dumps(d, ensure_ascii=False)[:300]}")
        failures += 1
    else:
        print(f"  ✓ 实例已创建: {inst_id}")

    hold_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "cnlsp://poc2/holdings"))
    hold = {
        "id": hold_id,
        "instanceId": inst_id,
        "permanentLocationId": loc,
        "sourceId": src,
        "callNumber": "G250.76",
        "callNumberTypeId": clc_id,
    }
    s, d = req("POST", "/holdings-storage/holdings", token, hold)
    if s not in (200, 201):
        s, d = req("GET", f"/holdings-storage/holdings/{hold_id}", token)
    if s in (200, 201):
        print("  ✓ holdings 已创建，索书号 G250.76（中图法）")
    else:
        print(f"  ✗ holdings 创建失败 HTTP {s}: {json.dumps(d, ensure_ascii=False)[:300]}")
        failures += 1

    s, d = req("GET", f"/holdings-storage/holdings?query=instanceId%3D%3D{inst_id}", token)
    recs = d.get("holdingsRecords", [])
    hit = [h for h in recs if h.get("callNumberTypeId") == clc_id]
    if hit:
        print(f"  ✓ 回读成功: callNumber={hit[0]['callNumber']}，类型=中图法")
    else:
        print(f"  ✗ 回读未找到 CLC holdings: {json.dumps(d, ensure_ascii=False)[:200]}")
        failures += 1

    print(f"\nPoC-2 结果: {'全部通过' if failures == 0 else f'{failures} 个失败'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
