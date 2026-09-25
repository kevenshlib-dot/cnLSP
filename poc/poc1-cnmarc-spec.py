#!/usr/bin/env python3
"""PoC-1: 通过 Mr. Specs API 零代码配置 CNMARC 核心字段规则。

在种子化的 MARC Bibliographic Specification 上，以 local scope 添加
CNMARC 核心字段（010/200/205/210/215/606/690/701/856）及其子字段、指示符。
全程只调用 mod-record-specifications 的 REST API，不改任何代码。
"""
import json
import sys
import urllib.request

GW = "http://localhost:18000"
TENANT = "diku"
SPEC_ID = "6eefa4c6-bbf7-4845-ad82-de7fc4abd0e3"  # MARC Bibliographic

# CNMARC 核心字段定义（依据《中国机读目录格式使用手册》/CALIS 联合目录规则）
CNMARC_FIELDS = [
    {
        "tag": "010", "label": "国际标准书号 (ISBN)", "repeatable": True, "required": False,
        "url": "https://www.calis.edu.cn/",
        "subfields": [
            {"code": "a", "label": "ISBN", "repeatable": False, "required": False},
            {"code": "b", "label": "装订方式", "repeatable": False, "required": False},
            {"code": "d", "label": "价格", "repeatable": False, "required": False},
            {"code": "z", "label": "错误ISBN", "repeatable": True, "required": False},
        ],
        "indicators": [],
    },
    {
        "tag": "200", "label": "题名与责任说明", "repeatable": False, "required": True,
        "url": "https://www.calis.edu.cn/",
        "subfields": [
            {"code": "a", "label": "正题名", "repeatable": False, "required": True},
            {"code": "d", "label": "并列题名", "repeatable": True, "required": False},
            {"code": "e", "label": "其他题名信息", "repeatable": True, "required": False},
            {"code": "f", "label": "第一责任说明", "repeatable": True, "required": False},
            {"code": "g", "label": "其余责任说明", "repeatable": True, "required": False},
            {"code": "h", "label": "分辑(册)号", "repeatable": True, "required": False},
            {"code": "i", "label": "分辑(册)题名", "repeatable": True, "required": False},
            {"code": "v", "label": "卷册标识", "repeatable": True, "required": False},
            {"code": "9", "label": "正题名汉语拼音", "repeatable": False, "required": False},
        ],
        "indicators": [
            {"order": 1, "label": "题名检索意义", "codes": [
                {"code": "0", "label": "题名无检索意义"},
                {"code": "1", "label": "题名有检索意义"},
            ]},
            {"order": 2, "label": "未定义", "codes": [{"code": "#", "label": "未定义"}]},
        ],
    },
    {
        "tag": "205", "label": "版本说明", "repeatable": True, "required": False,
        "subfields": [
            {"code": "a", "label": "版本说明", "repeatable": False, "required": False},
            {"code": "b", "label": "其余版本说明", "repeatable": True, "required": False},
        ],
        "indicators": [],
    },
    {
        "tag": "210", "label": "出版发行", "repeatable": False, "required": False,
        "subfields": [
            {"code": "a", "label": "出版发行地", "repeatable": True, "required": False},
            {"code": "c", "label": "出版发行者", "repeatable": True, "required": False},
            {"code": "d", "label": "出版发行日期", "repeatable": True, "required": False},
        ],
        "indicators": [],
    },
    {
        "tag": "215", "label": "载体形态", "repeatable": True, "required": False,
        "subfields": [
            {"code": "a", "label": "页数或卷册数", "repeatable": False, "required": False},
            {"code": "c", "label": "图表及其他形态细节", "repeatable": False, "required": False},
            {"code": "d", "label": "尺寸", "repeatable": False, "required": False},
            {"code": "e", "label": "附件", "repeatable": True, "required": False},
        ],
        "indicators": [],
    },
    {
        "tag": "606", "label": "普通主题", "repeatable": True, "required": False,
        "subfields": [
            {"code": "a", "label": "款目要素", "repeatable": False, "required": False},
            {"code": "x", "label": "学科复分", "repeatable": True, "required": False},
            {"code": "y", "label": "地区复分", "repeatable": True, "required": False},
            {"code": "z", "label": "年代复分", "repeatable": True, "required": False},
        ],
        "indicators": [
            {"order": 1, "label": "主题词级别", "codes": [
                {"code": "0", "label": "未指定级别"},
                {"code": "1", "label": "主要词"},
                {"code": "2", "label": "次要词"},
            ]},
            {"order": 2, "label": "未定义", "codes": [{"code": "#", "label": "未定义"}]},
        ],
    },
    {
        "tag": "690", "label": "中国图书馆分类法分类号", "repeatable": True, "required": False,
        "subfields": [
            {"code": "a", "label": "分类号", "repeatable": False, "required": False},
            {"code": "v", "label": "版次", "repeatable": False, "required": False},
        ],
        "indicators": [],
    },
    {
        "tag": "701", "label": "个人名称-主要责任方式", "repeatable": True, "required": False,
        "subfields": [
            {"code": "a", "label": "款目要素(姓)", "repeatable": False, "required": False},
            {"code": "b", "label": "名的其余部分", "repeatable": False, "required": False},
            {"code": "f", "label": "年代", "repeatable": False, "required": False},
            {"code": "4", "label": "责任方式", "repeatable": True, "required": False},
            {"code": "9", "label": "款目要素汉语拼音", "repeatable": False, "required": False},
        ],
        "indicators": [
            {"order": 1, "label": "未定义", "codes": [{"code": "#", "label": "未定义"}]},
            {"order": 2, "label": "名称著录形式", "codes": [
                {"code": "0", "label": "名称按直序(中国人名)著录"},
                {"code": "1", "label": "名称按倒序著录"},
            ]},
        ],
    },
    {
        "tag": "856", "label": "电子资源定位与检索", "repeatable": True, "required": False,
        "subfields": [
            {"code": "u", "label": "统一资源标识(URI)", "repeatable": False, "required": False},
            {"code": "z", "label": "附注", "repeatable": True, "required": False},
            {"code": "2", "label": "访问方法", "repeatable": False, "required": False},
        ],
        "indicators": [
            {"order": 1, "label": "访问方法", "codes": [
                {"code": "0", "label": "电子邮件"},
                {"code": "1", "label": "FTP"},
                {"code": "2", "label": "远程登录"},
                {"code": "3", "label": "拨号入网"},
                {"code": "4", "label": "HTTP"},
                {"code": "7", "label": "其他方法"},
            ]},
            {"order": 2, "label": "电子资源与文献的关系", "codes": [
                {"code": "0", "label": "资源本身"},
                {"code": "1", "label": "资源版本"},
                {"code": "2", "label": "相关资源"},
                {"code": "#", "label": "未提供信息"},
            ]},
        ],
    },
]


def api(method, path, token, body=None):
    req = urllib.request.Request(
        GW + path,
        method=method,
        headers={
            "x-okapi-tenant": TENANT,
            "x-okapi-token": token,
            "Content-Type": "application/json",
        },
        data=json.dumps(body).encode() if body is not None else None,
    )
    try:
        with urllib.request.urlopen(req) as resp:
            text = resp.read().decode()
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")


def main():
    token = open("/tmp/user-token.txt").read().strip()
    created, existed, failed = 0, 0, 0

    for f in CNMARC_FIELDS:
        payload = {k: f[k] for k in ("tag", "label", "repeatable", "required") if k in f}
        if f.get("url"):
            payload["url"] = f["url"]
        status, resp = api("POST", f"/specification-storage/specifications/{SPEC_ID}/fields", token, payload)
        if status == 409 or (status >= 400 and "already" in json.dumps(resp).lower()):
            print(f"  = {f['tag']} 已存在，跳过")
            existed += 1
            continue
        if status >= 300:
            print(f"  x {f['tag']} 创建失败 HTTP {status}: {json.dumps(resp, ensure_ascii=False)[:200]}")
            failed += 1
            continue
        field_id = resp["id"]
        print(f"  + {f['tag']} {f['label']} (id={field_id[:8]}...)")
        created += 1

        for sf in f["subfields"]:
            s, r = api("POST", f"/specification-storage/fields/{field_id}/subfields", token, sf)
            mark = "+" if s < 300 else "x"
            print(f"      {mark} ${sf['code']} {sf['label']}  HTTP {s}")

        for ind in f["indicators"]:
            s, r = api("POST", f"/specification-storage/fields/{field_id}/indicators", token,
                       {"order": ind["order"], "label": ind["label"]})
            if s >= 300:
                print(f"      x ind{ind['order']} 创建失败 HTTP {s}: {json.dumps(r, ensure_ascii=False)[:150]}")
                continue
            ind_id = r["id"]
            print(f"      + ind{ind['order']} {ind['label']}")
            for c in ind["codes"]:
                s2, r2 = api("POST", f"/specification-storage/indicators/{ind_id}/indicator-codes", token, c)
                mark = "+" if s2 < 300 else "x"
                print(f"          {mark} [{c['code']}] {c['label']}  HTTP {s2}")

    print(f"\n结果: 新建字段 {created}，已存在 {existed}，失败 {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
