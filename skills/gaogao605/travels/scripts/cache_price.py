#!/usr/bin/env python3
"""
价格缓存模块 - 缓存酒店价格查询结果，加快预订速度
"""
import json
import os
from datetime import datetime

CACHE_FILE = os.path.expanduser("~/.fbt_price_cache.json")

def save_price_cache(hotel_id: str, hotel_name: str, check_in: str, check_out: str, rooms: list):
    """保存价格查询结果到缓存"""
    cache = {
        "hotel_id": hotel_id,
        "hotel_name": hotel_name,
        "check_in": check_in,
        "check_out": check_out,
        "rooms": rooms,
        "timestamp": datetime.now().isoformat()
    }
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, ensure_ascii=False)
    return cache

def load_price_cache() -> dict:
    """读取价格缓存"""
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)

def get_room_plan(hotel_id: str, room_name: str) -> tuple:
    """从缓存获取room_id和plan_id"""
    cache = load_price_cache()
    if not cache or cache.get("hotel_id") != hotel_id:
        return None, None
    
    for room in cache.get("rooms", []):
        if room.get("room_name") == room_name or room_name in room.get("room_name", ""):
            room_id = room.get("room_id")
            plans = room.get("plan_list", [])
            if plans:
                plan = plans[0]
                plan_id = plan.get("plan_id")
                total_price = plan.get("total_price")
                return room_id, plan_id, total_price
    return None, None, None

def clear_cache():
    """清除缓存"""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "show":
            cache = load_price_cache()
            if cache:
                print(json.dumps(cache, indent=2, ensure_ascii=False)[:500])
            else:
                print("无缓存")
        elif sys.argv[1] == "clear":
            clear_cache()
            print("缓存已清除")
