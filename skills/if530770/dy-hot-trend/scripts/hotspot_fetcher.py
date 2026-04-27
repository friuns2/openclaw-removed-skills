#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抖音热榜数据获取脚本

功能：调用热榜API获取抖音实时热点数据
接口：https://onetotenvip.com/story/hotSpot/getListByPlatform
参数：platform=2, source=抖音热榜神器-ClawHub, startDate, endDate（可选）
方法：GET

特殊处理：未启用SNI（Server Name Indication）以适配特定SSL握手场景
"""

import json
import sys
import socket
import ssl
from datetime import datetime, timedelta
from urllib.parse import quote


def fetch_douyin_hotspot(start_date=None, end_date=None, days=None):
    """
    获取抖音热榜数据

    使用原生socket+ssl实现，未发送SNI以适配特定网络环境

    Args:
        start_date: 开始日期，格式 YYYY-MM-DD
        end_date: 结束日期，格式 YYYY-MM-DD
        days: 查询天数，如7表示近7天，30表示近30天

    Returns:
        None (结果直接打印到标准输出)
    """
    host = "onetotenvip.com"
    ip = "8.154.41.7"
    path = "/story/hotSpot/getListByPlatform"

    # 构建基础参数（source 固定为“抖音热榜神器 -SkillHub”）
    source = quote("抖音热榜神器-ClawHub")
    base_params = f"platform=2&source={source}"

    # 处理日期参数
    date_range = ""
    query_type = "实时"

    if days:
        # 根据天数计算日期范围
        # 日期范围是 [start_date, end_date)，end_date 为今天
        today = datetime.now().date()
        end_date_obj = today
        start_date_obj = today - timedelta(days=days)
        start_date = start_date_obj.strftime("%Y-%m-%d")
        end_date = end_date_obj.strftime("%Y-%m-%d")
        query_type = f"近{days}天"

    if start_date and end_date:
        date_range = f"&startDate={start_date}&endDate={end_date}"
        query_type = f"{start_date} 至 {end_date}"

    params = base_params + date_range

    http_request = (
        "GET {}?{} HTTP/1.1\r\n"
        "Host: {}\r\n"
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0\r\n"
        "Accept: application/json, text/plain, */*\r\n"
        "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).format(path, params, host)

    try:
        raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        raw_socket.settimeout(30)
        raw_socket.connect((ip, 443))

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        ssl_socket = context.wrap_socket(raw_socket, server_hostname=None)
        ssl_socket.send(http_request.encode('utf-8'))

        response = b""
        while True:
            try:
                chunk = ssl_socket.recv(8192)
                if not chunk:
                    break
                response += chunk
            except socket.timeout:
                break

        ssl_socket.close()
        raw_socket.close()

        response_text = response.decode('utf-8', errors='ignore')

        # 分离响应头和响应体
        if "\r\n\r\n" in response_text:
            _, body = response_text.split("\r\n\r\n", 1)
        elif "\n\n" in response_text:
            _, body = response_text.split("\n\n", 1)
        else:
            body = response_text

        # 解析JSON
        api_response = json.loads(body)

        # 处理不同的响应格式
        if isinstance(api_response, dict):
            # 格式1: {"code":2000, "data":[...]}
            if "data" in api_response:
                data = api_response["data"]
            elif "list" in api_response:
                data = api_response["list"]
            else:
                data = []
        elif isinstance(api_response, list):
            # 格式2: 直接是数组 [...]
            data = api_response
        else:
            data = []

        # 提取并格式化热榜数据
        if isinstance(data, list):
            # 获取当前时间
            now = datetime.now()
            fetch_time = now.strftime("%Y-%m-%d %H:00")

            result = {
                "fetch_time": fetch_time,
                "query_type": query_type,
                "start_date": start_date,
                "end_date": end_date,
                "hot_list": []
            }
            for item in data:
                # 处理标题：去除所有空格（半角空格、全角空格、制表符、换行符等）
                title = item.get("title", "")
                if title:
                    title = ''.join(title.split())
                result["hot_list"].append({
                    "index": item.get("index"),
                    "title": title,
                    "hotCount": item.get("hotCount", ""),
                    "url": item.get("url", "")
                })
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps([], ensure_ascii=False))

    except json.JSONDecodeError as e:
        error_msg = {"error": f"JSON解析失败: {str(e)}"}
        print(json.dumps(error_msg, ensure_ascii=False))
        sys.exit(1)
    except ssl.SSLError as e:
        error_msg = {"error": f"SSL错误: {str(e)}"}
        print(json.dumps(error_msg, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        error_msg = {"error": f"错误: {str(e)}"}
        print(json.dumps(error_msg, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='获取抖音热榜数据')
    parser.add_argument('--start-date', type=str, help='开始日期，格式 YYYY-MM-DD')
    parser.add_argument('--end-date', type=str, help='结束日期，格式 YYYY-MM-DD')
    parser.add_argument('--days', type=int, help='查询天数，如7表示近7天，30表示近30天')

    args = parser.parse_args()

    fetch_douyin_hotspot(
        start_date=args.start_date,
        end_date=args.end_date,
        days=args.days
    )
