#!/usr/bin/env python3
import os
import sys
import json
import requests
import re
from datetime import datetime

# 配置：高反爬域名黑名单，这些域名强制走专业提取接口
HIGH_ANTIBOT_DOMAINS = [
    'toutiao.com',
    'juejin.cn',
    'mp.weixin.qq.com',
    'zhihu.com',
    'weibo.com'
]

def is_high_antibot(url):
    """检测 URL 是否属于高倾斜反爬域名"""
    return any(domain in url for domain in HIGH_ANTIBOT_DOMAINS)

def fetch_via_tavily(url, api_key):
    """使用 Tavily Extract API 提取正文 (目前最稳的方法)"""
    if not api_key:
        return None
    
    print(f"[INFO] 正在调用 Tavily 专业级提取引擎: {url}")
    try:
        # Tavily Extract API 结构
        res = requests.post(
            "https://api.tavily.com/extract",
            json={
                "api_key": api_key,
                "urls": [url]
            },
            timeout=30
        )
        data = res.json()
        if data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            # Tavily 返回的是对象，包含 raw_content 或 markdown
            content = result.get('raw_content') or result.get('markdown')
            return content
    except Exception as e:
        print(f"[WARNING] Tavily 提取失败: {e}")
    return None

def fetch_via_jina(url):
    """使用 Jina.ai Reader 代理 (免费方案)"""
    print(f"[INFO] 正在尝试 Jina Reader 轻量提取: {url}")
    try:
        reader_url = f"https://r.jina.ai/{url}"
        headers = {
            "Accept": "text/markdown",
            "X-Target-Selector": "article, .content, .main" # 提示提取范围
        }
        res = requests.get(reader_url, headers=headers, timeout=20)
        if res.status_code == 200 and len(res.text) > 200:
            return res.text
    except Exception as e:
        print(f"[WARNING] Jina 提取失败: {e}")
    return None

def fetch_via_llm_reader(url):
    """备选的 LLM-Reader 接口"""
    print(f"[INFO] 正在尝试 LLM-Reader 节点提取: {url}")
    try:
        # 这是一个针对字节跳动优化过的公共接口镜像
        reader_url = f"https://reader.llm.report/api/read?url={url}"
        res = requests.get(reader_url, timeout=20)
        data = res.json()
        return data.get('markdown', '')
    except:
        return None

def fetch_basic(url):
    """最基础的多头 Requests 抓取 (针对 80% 的普通网站)"""
    print(f"[INFO] 正在执行标准请求协议: {url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        # 这里返回原始内容，后面可以接 Readability 提取
        return res.text
    except Exception as e:
        print(f"[ERROR] 标准抓取彻底瘫痪: {e}")
    return None

def smart_extract(url):
    """全自动智能路由提取逻辑"""
    # 1. 检测域名属性
    is_hard = is_high_antibot(url)
    
    # 2. 获取环境变量中的密钥
    tavily_key = os.environ.get("TAVILY_API_KEY")
    apify_token = os.environ.get("APIFY_TOKEN")

    content = None

    # 3. 路由策略：
    # 如果是硬骨头网站，优先走 Tavily
    if is_hard:
        if tavily_key:
            content = fetch_via_tavily(url, tavily_key)
        
        if not content:
            content = fetch_via_llm_reader(url)
            
        if not content:
            content = fetch_via_jina(url)
    else:
        # 普通网站先试免费的 Jina 或 LLM-Reader，效果最好
        content = fetch_via_jina(url)
        if not content:
            content = fetch_via_llm_reader(url)
        if not content:
            content = fetch_basic(url)

    if not content or len(content.strip()) < 50:
        print(f"[FATAL] 所有的抓取链路均被拦截或无法提取正文。")
        return None

    return content

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 smart_fetcher.py <url>")
        sys.exit(1)
    
    target_url = sys.argv[1]
    result = smart_extract(target_url)
    if result:
        print("\n--- EXTRACTED CONTENT START ---")
        print(result)
        print("--- EXTRACTED CONTENT END ---\n")
    else:
        sys.exit(1)
