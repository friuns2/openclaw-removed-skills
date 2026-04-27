#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI-SKILL 可视化面板 API 服务器
端口: 18792
路由前缀: /ailoveworld

用法：
  python3 api_server.py [端口]

目录结构（解压后）：
  解压目录/
  ├── config.json         # 配置文件
  ├── chat_data/          # 聊天数据目录（自动创建）
  └── skills/
      └── ai-love-world/  # Skill 目录
          ├── api_server.py  # 本文件
          └── web/
              └── dashboard.html
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# 路径配置
SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parent  # api_server.py 所在目录
AILOVE_DIR = SKILL_DIR.parent.parent  # /AILOVE_V1/skills/ai-love-world/ -> /AILOVE_V1/
CHAT_DATA_DIR = AILOVE_DIR / "chat_data"
WEB_DIR = AILOVE_DIR / "web"   # 主站前端文件目录
CONFIG_PATH = AILOVE_DIR / "config.json"

# 如果 chat_data 不存在，尝试在当前目录创建
if not CHAT_DATA_DIR.exists():
    # 尝试多个可能的路径
    possible_paths = [
        Path("chat_data"),
        Path("/root/AILOVE_V1/chat_data"),
        Path.cwd() / "chat_data",
    ]
    for p in possible_paths:
        if p.exists():
            CHAT_DATA_DIR = p
            break

# 路由前缀
ROUTE_PREFIX = "/ailoveworld"

# Analytics 数据库
ANALYTICS_DB = AILOVE_DIR / "analytics.db"

def get_analytics_db():
    """确保 analytics 数据库存在"""
    import sqlite3
    conn = sqlite3.connect(str(ANALYTICS_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS page_views (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT NOT NULL,
            visitor_id TEXT,
            referer TEXT,
            viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn

# 加载配置
def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"配置文件不存在: {CONFIG_PATH}，请确保 config.json 在正确位置")
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
    
    # 检查是否配置了有效的 appid
    if config.get('appid', '').startswith('替换成'):
        raise ValueError("config.json 中的 appid 尚未配置，请替换成真实的 APPID")
    
    return config

try:
    config = load_config()
except Exception as e:
    print(f"⚠️ 配置加载失败: {e}")
    config = {"appid": "未配置", "owner_nickname": "未配置", "server_url": ""}

# 加载 sessions
def load_sessions():
    sessions_file = CHAT_DATA_DIR / "sessions.json"
    if sessions_file.exists():
        try:
            with open(sessions_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

# 获取今日发起私聊次数限制
def get_daily_chat_limit():
    return config.get('auto_tasks', {}).get('max_daily_chats', 10)

# 获取今日已发起私聊次数（从记录文件）
def get_today_initiated_chats():
    record_file = SKILL_DIR / "auto_interact_record.json"
    if record_file.exists():
        try:
            with open(record_file, 'r') as f:
                record = json.load(f)
                today = datetime.now().strftime('%Y-%m-%d')
                if record.get('date') == today:
                    return record.get('chats_initiated', 0)
        except:
            pass
    return 0

# 触发 love chat
def trigger_love_chat():
    nudge_file = SKILL_DIR / "nudge_chat.flag"
    with open(nudge_file, 'w') as f:
        f.write(datetime.now().isoformat())
    return True

# 触发 community interaction
def trigger_community():
    nudge_file = SKILL_DIR / "nudge_community.flag"
    with open(nudge_file, 'w') as f:
        f.write(datetime.now().isoformat())
    return True

class DashboardHandler(BaseHTTPRequestHandler):
    """API 请求处理"""
    
    def strip_prefix(self, path):
        """移除路由前缀"""
        if path.startswith(ROUTE_PREFIX):
            return path[len(ROUTE_PREFIX):]
        return path
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = self.strip_prefix(parsed.path)
        
        if path == '/api/stats':
            self.send_json(self.get_stats())
        elif path == '/api/chats':
            self.send_json(self.get_chats())
        elif path.startswith('/api/chat/'):
            partner_id = path.split('/')[-1]
            self.send_json(self.get_chat_detail(partner_id))
        elif path == '/api/config':
            self.send_json({'server_url': config.get('server_url', '')})
        elif path == '/api/bot-info':
            self.send_json({
                'appid': config.get('appid', ''),
                'nickname': config.get('owner_nickname', ''),
                'personality': config.get('personality', ''),
                'server_url': config.get('server_url', ''),
                'chat_data_path': str(CHAT_DATA_DIR),
                'config_path': str(CONFIG_PATH)
            })
        elif path == '/api/analytics/stats':
            self.send_json(self.get_analytics_stats())
        elif path.startswith('/api/analytics/track'):
            parsed_qs = parsed.query
            params = dict(p.split('=') for p in parsed_qs.split('&') if '=' in p) if parsed_qs else {}
            self.track_page_view(params.get('path', '/'), params.get('visitor_id', ''), params.get('referer', ''))
            self.send_response(200)
            self.send_header('Content-Type', 'image/gif')
            gif = bytes.fromhex('474946383961010001000080000000000000ffffff000000210f90000010000002c00000000010001000002020d204f0063003b')
            self.send_header('Content-Length', len(gif))
            self.end_headers()
            self.wfile.write(gif)
        elif path == '/' or path == '':
            # 重定向到 dashboard
            self.send_response(302)
            self.send_header('Location', ROUTE_PREFIX + '/dashboard.html')
            self.end_headers()
        else:
            # 静态文件 - 去掉开头的 /
            file_path = path.lstrip('/')
            # 检查原始路径是否带 /ailoveworld 前缀
            original_path = parsed.path
            if original_path.startswith('/ailoveworld/'):
                # skill dashboard 等资源
                relative_path = original_path.replace('/ailoveworld/', '').lstrip('/')
                full_path = SKILL_DIR / 'web' / relative_path
            else:
                # 主站静态资源
                full_path = WEB_DIR / file_path
            
            if full_path.exists() and full_path.is_file():
                self.send_response(200)
                if file_path.endswith('.html'):
                    self.send_header('Content-Type', 'text/html; charset=utf-8')
                elif file_path.endswith('.js'):
                    self.send_header('Content-Type', 'application/javascript; charset=utf-8')
                elif file_path.endswith('.css'):
                    self.send_header('Content-Type', 'text/css; charset=utf-8')
                else:
                    self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Length', full_path.stat().st_size)
                self.end_headers()
                with open(full_path, 'rb') as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = self.strip_prefix(parsed.path)
        
        if path == '/api/trigger/love':
            result = trigger_love_chat()
            self.send_json({'success': True, 'message': '已触发私聊任务'})
        elif path == '/api/trigger/community':
            result = trigger_community()
            self.send_json({'success': True, 'message': '已触发社区互动任务'})
        else:
            self.send_error(404)
    
    def get_stats(self):
        sessions = load_sessions()
        total_chats = len(sessions)
        total_messages = sum(s.get('total_messages', 0) for s in sessions.values())
        avg_affinity = sum(s.get('affinity', 0) for s in sessions.values()) / total_chats if total_chats > 0 else 0
        today_initiated = get_today_initiated_chats()
        daily_limit = get_daily_chat_limit()
        remaining = max(0, daily_limit - today_initiated)
        
        return {
            'success': True,
            'stats': {
                'total_chats': total_chats,
                'total_messages': total_messages,
                'avg_affinity': round(avg_affinity, 1),
                'today_remaining': remaining,
                'daily_limit': daily_limit
            }
        }
    
    def get_chats(self):
        sessions = load_sessions()
        chats = []
        for partner_id, session in sessions.items():
            chat_file = CHAT_DATA_DIR / f"chat_{partner_id}.json"
            last_message = ''
            if chat_file.exists():
                try:
                    with open(chat_file, 'r') as f:
                        messages = json.load(f)
                        if messages:
                            last = messages[-1]
                            last_message = last.get('content', '')[:100]
                except:
                    pass
            
            chats.append({
                'partner_id': partner_id,
                'partner_name': session.get('partner_name', '未知'),
                'relationship_stage': session.get('relationship_stage', '陌生'),
                'affinity': session.get('affinity', 0),
                'total_messages': session.get('total_messages', 0),
                'last_chat': session.get('last_chat', ''),
                'last_message': last_message
            })
        
        # 按最后聊天时间排序
        chats.sort(key=lambda x: x.get('last_chat', ''), reverse=True)
        return {'success': True, 'chats': chats}
    
    def get_chat_detail(self, partner_id):
        chat_file = CHAT_DATA_DIR / f"chat_{partner_id}.json"
        if not chat_file.exists():
            return {'success': False, 'error': '聊天记录不存在'}
        
        try:
            with open(chat_file, 'r') as f:
                messages = json.load(f)
        except:
            return {'success': False, 'error': '聊天记录读取失败'}
        
        sessions = load_sessions()
        session = sessions.get(partner_id, {})
        
        return {
            'success': True,
            'chat': {
                'partner_id': partner_id,
                'partner_name': session.get('partner_name', '未知'),
                'relationship_stage': session.get('relationship_stage', '陌生'),
                'affinity': session.get('affinity', 0),
                'messages': messages
            }
        }
    
    def track_page_view(self, path, visitor_id, referer):
        """记录页面访问"""
        try:
            conn = get_analytics_db()
            conn.execute(
                "INSERT INTO page_views (path, visitor_id, referer) VALUES (?, ?, ?)",
                (path, visitor_id, referer)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Analytics track error: {e}")
    
    def get_analytics_stats(self):
        """获取统计数据"""
        import sqlite3
        from datetime import datetime, timedelta
        try:
            conn = get_analytics_db()
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            # 总 PV
            cursor.execute("SELECT COUNT(*) FROM page_views")
            total_pv = cursor.fetchone()[0] or 0
            
            # 总 UV
            cursor.execute("SELECT COUNT(DISTINCT visitor_id) FROM page_views WHERE visitor_id IS NOT NULL")
            total_uv = cursor.fetchone()[0] or 0
            
            # 今日 PV
            cursor.execute("SELECT COUNT(*) FROM page_views WHERE date(viewed_at) = ?", (today,))
            today_pv = cursor.fetchone()[0] or 0
            
            # 今日 UV
            cursor.execute("SELECT COUNT(DISTINCT visitor_id) FROM page_views WHERE date(viewed_at) = ? AND visitor_id IS NOT NULL", (today,))
            today_uv = cursor.fetchone()[0] or 0
            
            # 昨日 PV
            cursor.execute("SELECT COUNT(*) FROM page_views WHERE date(viewed_at) = ?", (yesterday,))
            yesterday_pv = cursor.fetchone()[0] or 0
            
            # 昨日 UV
            cursor.execute("SELECT COUNT(DISTINCT visitor_id) FROM page_views WHERE date(viewed_at) = ? AND visitor_id IS NOT NULL", (yesterday,))
            yesterday_uv = cursor.fetchone()[0] or 0
            
            # 近 7 天 PV
            cursor.execute("SELECT COUNT(*) FROM page_views WHERE date(viewed_at) >= ?", (week_ago,))
            week_pv = cursor.fetchone()[0] or 0
            
            # 近 7 天 UV
            cursor.execute("SELECT COUNT(DISTINCT visitor_id) FROM page_views WHERE date(viewed_at) >= ? AND visitor_id IS NOT NULL", (week_ago,))
            week_uv = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'success': True,
                'stats': {
                    'total_pv': total_pv,
                    'total_uv': total_uv,
                    'today_pv': today_pv,
                    'today_uv': today_uv,
                    'yesterday_pv': yesterday_pv,
                    'yesterday_uv': yesterday_uv,
                    'week_pv': week_pv,
                    'week_uv': week_uv
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_json(self, data):
        response = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

def run_server(port=18792):
    """启动服务器"""
    print(f"🤖 AI-SKILL 可视化面板启动")
    print(f"📁 配置路径: {CONFIG_PATH}")
    print(f"📁 聊天数据: {CHAT_DATA_DIR}")
    print(f"🌐 看板地址: http://0.0.0.0:{port}{ROUTE_PREFIX}/dashboard.html")
    
    if not CONFIG_PATH.exists():
        print(f"⚠️ 警告: 配置文件不存在!")
    elif config.get('appid', '').startswith('替换成'):
        print(f"⚠️ 警告: config.json 中的 appid 尚未配置!")
    
    if not CHAT_DATA_DIR.exists():
        print(f"⚠️ 警告: 聊天数据目录不存在!")
    
    server = HTTPServer(('0.0.0.0', port), DashboardHandler)
    print(f"✅ 服务已启动")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
        server.shutdown()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18792
    run_server(port)
