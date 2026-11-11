#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从红狐Hub API 拉取抖音实时热榜 -> 过滤敏感类 -> 分类 -> 输出 hotspots.json
供抖音运营工作台 onload 自动 fetch 使用（打开即最新真实热点）。

用法（需环境变量 REDFOX_API_KEY）：
  REDFOX_API_KEY=ak_xxx python gen_hotspots.py
输出：hotspots.json（同目录）
"""
import json
import os
import sys
from datetime import datetime

import requests

API_URL = "https://redfox.hk/story/api/hotSpot/getListByPlatform"


def fetch_raw():
    key = os.getenv("REDFOX_API_KEY")
    if not key:
        sys.stderr.write("缺少 REDFOX_API_KEY\n")
        sys.exit(1)
    params = {"platform": 2, "source": "抖音热榜-WorkBuddy"}
    headers = {"X-API-KEY": key.strip(), "Accept": "application/json"}
    r = requests.get(API_URL, params=params, headers=headers, timeout=30)
    r.raise_for_status()
    j = r.json()
    return j.get("data") or j.get("list") or []


# 敏感类关键词（时政/军事/涉外/灾害/官方硬宣）——自动剔除，不在工作台展示
SENSITIVE = [
    "一带一路", "空军", "地震", "赖清德", "两岸统一", "孙中山", "锐评",
    "护航消费季", "人民空军", "网友记录扬州", "扬州江都", "人民", "官方",
    "主席", "政府", "外交部", "国庆", "两会", "烈士", "制裁", "疫情",
]

# 分类关键词（命中即归类，按顺序优先）
RULES = [
    ("情感/情侣", ["浪漫", "聊天", "恋", "爱", "我们", "男主", "女主", "情侣",
                  "约会", "异地", "怎么", "你又", "正缘", "怼脸"]),
    ("美食/生活", ["吃", "美食", "菜", "红果", "饺子", "零食", "喝", "秋裤",
                  "被窝", "天冷", "生活", "实况"]),
    ("穿搭/时尚", ["穿搭", "千禧", "毛衣", "cos", "造型", "时尚", "妆", "服饰",
                  "编织", "白色", "allwhite"]),
    ("萌宠", ["萌宠", "毛茸茸", "宠物", "狗", "猫", "萌宝"]),
    ("娱乐", ["金鸡", "奖", "MV", "明星", "剧", "综艺", "电影", "歌手",
              "最佳", "名场面", "公开"]),
    ("游戏", ["和平精英", "影之刃", "瓦", "火影", "游戏", "教学", "BLG",
              "应援", "JYP", "男团"]),
    ("创作/挑战", ["挑战", "对口型", "二创", "手势舞", "漫剧", "cos"]),
    ("风景/秋日", ["秋天", "初雪", "大理", "雪", "景", "交换", "定格"]),
]


def is_sensitive(t):
    return any(k in t for k in SENSITIVE)


def classify(t):
    for typ, kws in RULES:
        if any(k in t for k in kws):
            return typ
    return "生活"


def star_of(t, typ):
    # 与用户素材库（对象的蔬菜静物+人像、情侣日常、秋日）强契合给 5
    if any(k in t for k in ["秋天", "秋日", "实况", "浪漫", "我们", "情侣",
                            "交换", "菜", "定格", "红果", "秋裤"]):
        return 5
    if typ in ("情感/情侣", "萌宠", "美食/生活", "风景/秋日"):
        return 4
    return 3


def main():
    raw = fetch_raw()
    out_items = []
    for it in raw:
        t = (it.get("title") or "").replace(" ", "")
        if not t or is_sensitive(t):
            continue
        typ = classify(t)
        hc = str(it.get("hotCount") or "")
        try:
            heat = "抖音实时 · " + str(round(int(hc) / 10000, 1)) + "万"
        except ValueError:
            heat = "抖音实时"
        out_items.append({
            "title": t,
            "star": star_of(t, typ),
            "heat": heat,
            "type": typ,
        })
    now = datetime.now()
    out = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "list": out_items,
    }
    with open("hotspots.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print("OK wrote %d items to hotspots.json" % len(out_items))


if __name__ == "__main__":
    main()
