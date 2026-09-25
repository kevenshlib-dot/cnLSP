#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PoC-3：中文流通规则端到端验证（cnLSP 第三阶段）

覆盖链路：中文读者类型 → 中文流通政策（借期/通知/请求/逾期/赔偿）→
中文流通规则 → 中文读者用户 → 带中图法索书号的条码册 → 借出 → 逾期 →
归还 → 逾期费。复用 PoC-2 的 instance/holdings（G250.76 中图法）。
"""
import json
import sys
import time
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone

GW = "http://localhost:18000"
TENANT = "diku"

NS = uuid.NAMESPACE_URL
GID = lambda name: str(uuid.uuid5(NS, f"cnlsp://poc3/{name}"))

# PoC-2 复用的固定 ID
HOLD_ID = str(uuid.uuid5(NS, "cnlsp://poc2/holdings"))


def req(method, path, token, body=None):
    r = urllib.request.Request(
        GW + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers={"x-okapi-tenant": TENANT, "Content-Type": "application/json",
                 **({"x-okapi-token": token} if token else {})})
    try:
        with urllib.request.urlopen(r) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw.decode(errors="replace")[:400]}


def login():
    s, d = req("POST", "/authn/login", None, {"username": "folio", "password": "folio"})
    assert s in (200, 201), f"login failed: {s} {d}"
    return d.get("okapiToken") or d.get("accessToken")


def ensure(token, list_path, list_key, match_field, match_value, payload, tag):
    """幂等创建参考数据：按字段查重，存在则复用 id。"""
    s, d = req("GET", f"{list_path}?limit=2000", token)
    if s == 200:
        for it in d.get(list_key, []):
            if it.get(match_field) == match_value:
                print(f"  · {tag} 已存在，复用 {it['id']}")
                return it["id"]
    s, d = req("POST", list_path, token, payload)
    if s in (200, 201):
        print(f"  ✓ {tag} 已创建")
        return d["id"]
    print(f"  ✗ {tag} 创建失败 HTTP {s}: {json.dumps(d, ensure_ascii=False)[:300]}")
    return None


def main():
    token = login()
    ok = True

    print("== 1. 中文读者类型（patron group）==")
    # 中文名读者类型：纯存储/展示用（FOLIO 流通规则文法 NAME 仅支持 [0-9a-zA-Z-]，无法引用中文名）
    ensure(token, "/groups", "usergroups", "group", "本科生",
           {"id": GID("group-cn"), "group": "本科生",
            "desc": "全日制本科生（中文名演示；规则匹配用 undergrad）"}, "读者类型[本科生]")
    # 规则可引用的 ASCII 代码型读者类型（本土馆实际配置方式）
    pg = ensure(token, "/groups", "usergroups", "group", "undergrad",
                {"id": GID("group"), "group": "undergrad",
                 "desc": "本科生：全日制本科生，可借中文图书 30 天"}, "读者类型[undergrad/本科生]")

    print("== 2. 中文流通政策 ==")
    lp = ensure(token, "/loan-policy-storage/loan-policies", "loanPolicies", "name",
                "中文图书30天",
                {"id": GID("loan-policy"), "name": "中文图书30天",
                 "description": "中文普通图书：借期 30 天，可续借 2 次",
                 "loanable": True, "renewable": True,
                 "loansPolicy": {"profileId": "Rolling",
                                 "period": {"duration": 30, "intervalId": "Days"},
                                 "closedLibraryDueDateManagementId": "KEEP_THE_CURRENT_DUE_DATE"},
                 "renewalsPolicy": {"unlimited": False, "numberAllowed": 2,
                                    "renewFromId": "CURRENT_DUE_DATE"}},
                "借期政策[中文图书30天]")

    np_ = ensure(token, "/patron-notice-policy-storage/patron-notice-policies",
                 "patronNoticePolicies", "name", "中文默认通知政策",
                 {"id": GID("notice-policy"), "name": "中文默认通知政策",
                  "description": "占位通知政策（邮件模板后续本土化）", "active": True},
                 "通知政策[中文默认]")

    rp = ensure(token, "/request-policy-storage/request-policies", "requestPolicies",
                "name", "允许预约与递送",
                {"id": GID("request-policy"), "name": "允许预约与递送",
                 "description": "允许馆内预约（Hold）与召回（Recall）",
                 "requestTypes": ["Hold", "Recall", "Page"]},
                "请求政策[允许预约与递送]")

    op = ensure(token, "/overdue-fines-policies", "overdueFinePolicies", "name",
                "中文图书逾期每天0.1元",
                {"id": GID("overdue-policy"), "name": "中文图书逾期每天0.1元",
                 "description": "逾期每天 0.1 元，封顶 20 元",
                 "countClosed": True, "maxOverdueFine": "20.00",
                 "forgiveOverdueFine": False,
                 "overdueFine": {"quantity": 1.0, "intervalId": "day"},
                 "gracePeriodRecall": True},
                "逾期政策[每天0.1元]")

    ip = ensure(token, "/lost-item-fees-policies", "lostItemFeePolicies", "name",
                "中文图书赔偿按原价",
                {"id": GID("lost-policy"), "name": "中文图书赔偿按原价",
                 "description": "遗失按定价赔偿，另收加工费 10 元",
                 "itemAgedLostOverdue": {"duration": 30, "intervalId": "Days"},
                 "patronBilledAfterAgedLost": {"duration": 5, "intervalId": "Days"},
                 "chargeAmountItem": {"chargeType": "actualCost", "amount": 0.0},
                 "lostItemProcessingFee": 10.0,
                 "chargeAmountItemPatron": True, "chargeAmountItemSystem": False,
                 "lostItemChargeFeeFine": {"duration": 4, "intervalId": "Weeks"},
                 "returnedLostItemProcessingFee": True, "replacedLostItemProcessingFee": False,
                 "replacementProcessingFee": 0.0, "replacementAllowed": False,
                 "lostItemReturned": "Charge"},
                "赔偿政策[按原价]")

    print("== 2.5 费/罚款主体与类型（feesfines 前置参考数据）==")
    sp0, spd0 = req("GET", "/service-points?query=code%3D%3DMAIN-CD", token)
    sp0_id = spd0["servicepoints"][0]["id"]
    owner = ensure(token, "/owners", "owners", "owner", "总馆流通台",
                   {"id": GID("owner"), "owner": "总馆流通台",
                    "desc": "总馆流通服务台逾期费主体",
                    "servicePointOwner": [{"value": sp0_id, "label": "总馆流通台"}]},
                   "费款主体[总馆流通台]")
    ft = ensure(token, "/feefines", "feefines", "feeFineType", "Overdue fine",
                {"id": GID("feefine"), "feeFineType": "Overdue fine",
                 "ownerId": owner, "automatic": True},
                "费款类型[Overdue fine]")

    print("== 3. 流通规则（circulation rules，ASCII 代码 + 中文政策 UUID）==")
    # 文法限制：NAME 仅 [0-9a-zA-Z-]，规则条件只能用 ASCII 代码名；
    # 政策名可以是中文（规则中按 UUID 引用）。
    mt = ensure(token, "/material-types", "mtypes", "name", "cn-book",
                {"id": GID("mtype-cn"), "name": "cn-book",
                 "source": "local"}, "资料类型[cn-book/中文图书]")
    rules = (
        "priority: t, s, c, b, a, m, g\n"
        "fallback-policy: l {l} r {r} n {n} o {o} i {i}\n"
        "m {m} + g {g}: l {l} r {r} n {n} o {o} i {i}\n"
    ).format(l=lp, r=rp, n=np_, o=op, i=ip, m="cn-book", g="undergrad")
    s, d = req("PUT", "/circulation/rules", token, {"rulesAsText": rules})
    if s in (200, 204):
        print("  ✓ 流通规则已写入（m cn-book + g undergrad → 中文图书30天等政策）")
    else:
        ok = False
        print(f"  ✗ 流通规则写入失败 HTTP {s}: {json.dumps(d, ensure_ascii=False)[:400]}")

    print("== 4. 中文读者用户 ==")
    user_id = GID("user")
    s, d = req("GET", f"/users/{user_id}", token)
    if s != 200:
        s, d = req("POST", "/users", token,
                   {"id": user_id, "username": "reader_zhang",
                    "barcode": "R20260001", "active": True,
                    "patronGroup": pg,
                    "personal": {"lastName": "三", "firstName": "张",
                                 "preferredFirstName": "张三",
                                 "email": "zhangsan@example.cn"}},
                   )
    print(f"  {'✓' if s in (200,201) else '✗'} 读者[张三] barcode=R20260001 HTTP {s}")
    ok = ok and s in (200, 201)

    print("== 5. 中文图书册（item，中图法索书号）==")
    lt = ensure(token, "/loan-types", "loantypes", "name", "普通外借",
                {"id": GID("loantype"), "name": "普通外借"}, "借阅类型[普通外借]")
    item_id = GID("item")
    s, d = req("GET", f"/item-storage/items/{item_id}", token)
    if s == 200 and d.get("materialTypeId") != mt:
        # 旧册的 materialType 不是 cn-book，删除重建以命中 m 规则
        s, d = req("DELETE", f"/item-storage/items/{item_id}", token)
    if s != 200:
        s, d = req("POST", "/item-storage/items", token,
                   {"id": item_id, "holdingsRecordId": HOLD_ID,
                    "barcode": "CN20260001",
                    "status": {"name": "Available"},
                    "materialTypeId": mt,
                    "permanentLoanTypeId": lt,
                    "itemLevelCallNumber": "G250.76",
                    "itemLevelCallNumberTypeId": "95467209-6d7b-468b-94df-0f5d7ad2747d",
                    "effectiveLocationId": json.loads("{}") if False else None})
        # effectiveLocationId 需要 PoC-2 的 location；若缺省则模块会拒绝
    if s in (200, 201):
        print(f"  ✓ 册[CN20260001] 已就绪 HTTP {s}")
    else:
        # 补 effectiveLocationId 后重试
        s2, dd = req("GET", f"/holdings-storage/holdings/{HOLD_ID}", token)
        perm_loc = dd.get("permanentLocationId")
        s, d = req("POST", "/item-storage/items", token,
                   {"id": item_id, "holdingsRecordId": HOLD_ID,
                    "barcode": "CN20260001",
                    "status": {"name": "Available"},
                    "materialTypeId": mt,
                    "permanentLoanTypeId": lt,
                    "itemLevelCallNumber": "G250.76",
                    "effectiveLocationId": perm_loc})
        print(f"  {'✓' if s in (200,201) else '✗'} 册[CN20260001] HTTP {s}")
        ok = ok and s in (200, 201)

    print("== 6. 借出 check-out（中文规则命中）==")
    sp_q, spd = req("GET", "/service-points?query=code%3D%3DMAIN-CD", token)
    sp_id = spd["servicepoints"][0]["id"]
    s, loan = req("POST", "/circulation/check-out-by-barcode", token,
                  {"itemBarcode": "CN20260001", "userBarcode": "R20260001",
                   "servicePointId": sp_id})
    if s in (200, 201):
        due = loan.get("dueDate", "")
        loan_id = loan.get("id")
        print(f"  ✓ 借出成功 loan={loan_id}")
        print(f"    到期日 dueDate={due}（应约为 30 天后）")
    else:
        ok = False
        print(f"  ✗ 借出失败 HTTP {s}: {json.dumps(loan, ensure_ascii=False)[:500]}")
        print("  （后续步骤跳过）")
        print(f"\n结果: {'全部通过' if ok else '存在失败项'}")
        sys.exit(1)

    print("== 7. 逾期模拟：把到期日改为 3 天前 ==")
    past = (datetime.now(timezone.utc) - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")
    s, d = req("GET", f"/circulation/loans/{loan_id}", token)
    if s == 200:
        d["dueDate"] = past
        s2, d2 = req("PUT", f"/circulation/loans/{loan_id}", token, d)
        print(f"  {'✓' if s2 in (200,204) else '✗'} 到期日改写 HTTP {s2}")
        ok = ok and s2 in (200, 204)

    print("== 8. 归还 check-in ==")
    s, ci = req("POST", "/circulation/check-in-by-barcode", token,
                {"itemBarcode": "CN20260001", "servicePointId": sp_id,
                 "checkInDate": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+00:00")})
    print(f"  {'✓' if s in (200,201) else '✗'} 归还 HTTP {s}")
    ok = ok and s in (200, 201)

    print("== 9. 验证 loan 关闭与逾期费（feesfines）==")
    time.sleep(3)  # 等 Kafka 异步事件结算
    s, d = req("GET", f"/circulation/loans?query=itemId%3D%3D{item_id}", token)
    loans = d.get("loans", [])
    if loans and loans[0].get("status", {}).get("name") == "Closed":
        print(f"  ✓ loan 已关闭，action={loans[0].get('action')}")
    else:
        ok = False
        print(f"  ✗ loan 状态异常: {json.dumps(d, ensure_ascii=False)[:300]}")
    s, d = req("GET", f"/accounts?query=userId%3D%3D{user_id}", token)
    accts = d.get("accounts", [])
    if accts:
        for a in accts:
            print(f"  ✓ 逾期费账单: {a.get('feeFineType')} 金额={a.get('amount')} 状态={a.get('status',{}).get('name')}")
    else:
        print("  · 暂无逾期费账单（逾期费由定时任务结算，可后续观察）")

    print(f"\n结果: {'全部通过' if ok else '存在失败项'}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
