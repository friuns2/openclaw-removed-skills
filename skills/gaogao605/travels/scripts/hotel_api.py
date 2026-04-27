#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分贝通酒店预订 API 封装
版本: 3.1.0 | 最后更新: 2026-03-25

基于新的统一接口入口: /business/hotel/open/push/skill/access
所有操作通过 skill_type 参数区分
支持鉴权 token 自动保存到 ~/.fbt-auth.json
"""
import requests
import json
import sys
import time
try:
    from scripts.cache_price import save_price_cache
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.cache_price import save_price_cache
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
from datetime import datetime

# ==================== 配置 ====================
# FAT 测试环境
FAT_BASE_URL = "https://app-gate.fenbeitong.com"
# 线上环境
PROD_BASE_URL = "https://app-gate.fenbeitong.com"

# 当前使用环境
BASE_URL = FAT_BASE_URL
API_PATH = "/business/hotel/open/push/skill/access"

# 默认 access-token（测试用）
DEFAULT_ACCESS_TOKEN = "fbsk-2db251f6c8d74ce69ae3dcb82ed1055b"

# 鉴权信息保存路径
AUTH_FILE = Path.home() / ".fbt-auth.json"

# ==================== Skill Types ====================
SKILL_TYPES = {
    # 认证类（需要登录验证）
    "getMobileCaptcha": "获取手机号验证码",
    "getIdentityCode": "获取身份编码接口",
    # 酒店查询类
    "searchHotelList": "搜索酒店列表",
    "queryHotelPrice": "实时查询酒店价格详情",
    "queryHotelDetail": "查询酒店扩展详情",
    "queryHotelComment": "查询酒店评论",
    # 订单类
    "createOrder": "酒店下单",
    "cancelOrder": "取消订单",
    "queryOrder": "查询订单",
}


# ==================== Token 存储管理 ====================

def save_auth_token(token: str, mobile: str = None) -> bool:
    """
    保存认证 token 到 ~/.fbt-auth.json
    
    Args:
        token: identity_code (access-token)
        mobile: 手机号（可选）
    
    Returns:
        是否保存成功
    """
    try:
        auth_data = {
            "identity_code": token,
            "mobile": mobile,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        # 如果文件已存在，保留部分字段
        if AUTH_FILE.exists():
            try:
                existing = json.loads(AUTH_FILE.read_text())
                auth_data["mobile"] = mobile or existing.get("mobile")
                auth_data["created_at"] = existing.get("created_at", auth_data["created_at"])
            except:
                pass
        
        AUTH_FILE.write_text(json.dumps(auth_data, ensure_ascii=False, indent=2))
        return True
    except Exception as e:
        print(f"[fbsk-hotel] 保存token失败: {e}")
        return False


def load_auth_token() -> Optional[str]:
    """
    从 ~/.fbt-auth.json 读取已保存的 token
    
    Returns:
        identity_code 或 None
    """
    try:
        if AUTH_FILE.exists():
            auth_data = json.loads(AUTH_FILE.read_text())
            return auth_data.get("identity_code")
    except Exception as e:
        print(f"[fbsk-hotel] 读取token失败: {e}")
    return None


def get_auth_info() -> Optional[Dict]:
    """
    获取完整的认证信息
    
    Returns:
        {"identity_code": "...", "mobile": "...", "created_at": "..."} 或 None
    """
    try:
        if AUTH_FILE.exists():
            return json.loads(AUTH_FILE.read_text())
    except:
        pass
    return None


def clear_auth_token() -> bool:
    """
    清除保存的认证信息
    
    Returns:
        是否清除成功
    """
    try:
        if AUTH_FILE.exists():
            AUTH_FILE.unlink()
        return True
    except:
        return False


class FbHotelApiError(Exception):
    """分贝通酒店API异常"""
    pass


class FbHotelApi:
    """分贝通酒店API客户端"""
    
    def __init__(self, access_token: str = None, context: Optional[Dict] = None):
        """
        初始化API客户端
        
        Token 获取优先级：
        1. 参数传入的 access_token
        2. 从 ~/.fbt-auth.json 读取已保存的 token
        3. 使用默认 token（测试用）
        
        Args:
            access_token: 身份编码（可选）
            context: 用户上下文信息
        """
        self.context = context
        self.session = requests.Session()
        self.base_url = BASE_URL
        self.api_path = API_PATH
        
        # 获取 token（优先级：参数 > 文件 > 默认）
        if access_token:
            self.access_token = access_token
        else:
            saved_token = load_auth_token()
            self.access_token = saved_token or DEFAULT_ACCESS_TOKEN
    
    def _get_headers(self, with_auth: bool = True) -> Dict:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json"
        }
        if with_auth:
            headers["access-token"] = self.access_token
        return headers
    
    def _request(self, skill_type: str, data: Dict = None, with_auth: bool = True) -> Dict:
        """
        通用请求方法
        
        Args:
            skill_type: 技能类型
            data: 请求参数
            with_auth: 是否需要认证header
        
        Returns:
            接口响应
        """
        url = f"{self.base_url}{self.api_path}"
        
        # 构建请求体
        body = {"skill_type": skill_type}
        if data:
            body.update(data)
        
        headers = self._get_headers(with_auth)
        
        try:
            response = self.session.post(
                url,
                json=body,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            res_json = response.json()
            
            # 检查响应状态
            if res_json.get("code") == 0 or res_json.get("success"):
                return res_json
            else:
                error_msg = res_json.get("msg", res_json.get("message", "未知错误"))
                raise FbHotelApiError(f"接口失败: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            raise FbHotelApiError(f"网络请求失败: {str(e)}")
        except json.JSONDecodeError:
            raise FbHotelApiError("接口响应非JSON格式")
        except Exception as e:
            raise FbHotelApiError(f"请求异常: {str(e)}")
    
    # ==================== 认证类接口 ====================
    
    def send_captcha(self, mobile: str) -> Dict:
        """
        发送手机验证码
        
        Args:
            mobile: 手机号
        
        Returns:
            {"code": 0, "msg": "success", "data": true}
        """
        return self._request(
            "getMobileCaptcha",
            {"mobile": mobile},
            with_auth=False
        )
    
    def verify_captcha(self, mobile: str, captcha: str) -> Dict:
        """
        验证验证码并获取身份编码
        
        Args:
            mobile: 手机号
            captcha: 验证码
        
        Returns:
            {"code": 0, "data": {"identity_code": "fbsk-xxx"}}
        """
        return self._request(
            "getIdentityCode",
            {"mobile": mobile, "captcha": captcha},
            with_auth=False
        )
    
    # ==================== 酒店查询接口 ====================
    
    def search_hotel_list(
        self,
        city_name: str,
        keywords: str = "",
        hotel_name: str = "",
        page_index: int = 1,
        page_size: int = 5
    ) -> Dict:
        """
        搜索酒店列表
        
        Args:
            city_name: 城市名称（如"北京市"）
            keywords: 关键词（用户输入的全部内容，原样传递）
            hotel_name: 酒店名称
            page_index: 页码
            page_size: 每页数量
        
        Returns:
            酒店列表数据
        """
        data = {
            "city_name": city_name,
            "keywords": keywords,
            "hotel_name": hotel_name,
            "page_index": page_index,
            "page_size": page_size
        }
        return self._request("searchHotelList", data)
    
    def query_hotel_price(
        self,
        hotel_id: str,
        check_in_date: str,
        check_out_date: str,
        payment_type: str = "PP",
        nation_type: int = 1
    ) -> Dict:
        """
        查询酒店价格详情（含房型和产品）
        
        Args:
            hotel_id: 酒店ID
            check_in_date: 入住日期 yyyy-MM-dd
            check_out_date: 退房日期 yyyy-MM-dd
            payment_type: 支付方式 PP=预付 SP=现付
            nation_type: 1=国内 2=国际
        
        Returns:
            酒店详情 + 房型 + 产品数据
        """
        data = {
            "hotel_id": hotel_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "payment_type": payment_type,
            "nation_type": nation_type
        }
        result = self._request("queryHotelPrice", data)
        # 保存价格缓存，加快预订速度
        if result.get("success"):
            save_price_cache(hotel_id, "", check_in_date, check_out_date, result.get("data", {}).get("rooms", []))
        return result
    
    def query_hotel_detail(self, hotel_id: str) -> Dict:
        """
        查询酒店扩展详情
        
        Args:
            hotel_id: 酒店ID
        
        Returns:
            酒店详细信息（星级、评分、地址、电话、周边等）
        """
        return self._request("queryHotelDetail", {"hotel_id": hotel_id})
    
    def query_hotel_comment(
        self,
        hotel_id: str,
        page_index: int = 1,
        page_size: int = 5
    ) -> Dict:
        """
        查询酒店评论
        
        Args:
            hotel_id: 酒店ID
            page_index: 页码
            page_size: 每页数量
        
        Returns:
            酒店评论数据
        """
        data = {
            "hotel_id": hotel_id,
            "page_index": page_index,
            "page_size": page_size
        }
        return self._request("queryHotelComment", data)
    
    # ==================== 订单接口 ====================
    
    def create_order(
        self,
        hotel_id: str,
        room_id: str,
        plan_id: str,
        check_in_date: str,
        check_out_date: str,
        total_price: float,
        contact: Dict,
        guest_list: List = None,
        room_count: int = 1,
        payment_type: str = "PP",
        nation_type: int = 1
    ) -> Dict:
        """
        创建酒店订单
        
        Args:
            hotel_id: 酒店ID
            room_id: 房型ID
            plan_id: 产品ID（plan_id）
            check_in_date: 入住日期
            check_out_date: 退房日期
            total_price: 总价
            contact: 联系人 {"name": "", "phone": ""}
            guest_list: 入住人列表（二维数组）
            room_count: 房间数
            payment_type: 支付方式
            nation_type: 1=国内 2=国际
        
        Returns:
            订单创建结果，包含 order_id
        """
        # 生成第三方订单ID
        third_order_id = f"SK{int(time.time() * 1000)}"
        
        data = {
            "nation_type": nation_type,
            "payment_type": payment_type,
            "hotel_id": hotel_id,
            "check_in_date": check_in_date,
            "check_out_date": check_out_date,
            "room_id": room_id,
            "plan_id": plan_id,
            "total_price": total_price,
            "room_count": room_count,
            "contact": contact
        }
        
        if guest_list:
            data["guestList1"] = guest_list
        
        return self._request("createOrder", data)
    
    def cancel_order(self, order_id: str, cancel_reason: str = "") -> Dict:
        """
        取消订单
        
        Args:
            order_id: 订单ID
            cancel_reason: 取消原因
        
        Returns:
            取消结果
        """
        data = {"order_id": order_id}
        if cancel_reason:
            data["cancel_reason"] = cancel_reason
        return self._request("cancelOrder", data)
    
    def query_order(self, order_id: str) -> Dict:
        """
        查询订单详情
        
        Args:
            order_id: 订单ID
        
        Returns:
            订单详情
        """
        return self._request("queryOrder", {"order_id": order_id})
    
    # ==================== 格式化输出 ====================
    
    def format_hotel_list(self, data: Dict, check_in_date: str = None, budget: float = None, star_level: str = None, keywords: str = None) -> str:
        """格式化酒店列表 - 支持图片内嵌展示，按价格排序，显示推荐理由"""
        hotel_list = data.get("data", {}).get("hotel_list", [])
        if not hotel_list:
            return "🔍 未找到符合条件的酒店，建议调整搜索关键词"
        
        # 按价格排序（低价优先）
        hotel_list = sorted(hotel_list, key=lambda x: float(x.get('min_price', 999999) or 999999))
        
        # 过滤预算范围（如果有）
        if budget and budget > 0:
            hotel_list = [h for h in hotel_list if float(h.get('min_price', 999999) or 999999) <= budget]
        
        # 过滤酒店等级（如果有）
        if star_level:
            star_map = {
                '经济型': ['经济型'],
                '舒适型': ['舒适型'],
                '豪华型': ['豪华型', '高档型', '五星级', '四星级']
            }
            allowed_stars = star_map.get(star_level, [star_level])
            hotel_list = [h for h in hotel_list if h.get('star_level_name', '') in allowed_stars]
        
        if not hotel_list:
            return f"🔍 未找到符合条件（{star_level or '不限'}、预算{budget or '不限'}元）的酒店，建议调整筛选条件"
        
        lines = []
        date_str = f"（{check_in_date}入住）" if check_in_date else ""
        budget_str = f"、预算≤¥{int(budget)}" if budget and budget > 0 else ""
        star_str = f"、{star_level}" if star_level else ""
        lines.append(f"## 🏨 酜店列表 {date_str}{star_str}{budget_str}\n")
        lines.append(f"找到 **{len(hotel_list[:5])}** 家酒店（分贝通实时数据，按价格排序）\n")
        
        for i, h in enumerate(hotel_list[:5], 1):
            name = h.get('name', '-')
            star = h.get('star_level_name', '-')
            district = h.get('district_name', '-')
            price = h.get('min_price', 0)
            score = h.get('score', '-')
            main_logo = h.get('main_logo', '')
            
            # 图片内嵌展示
            if main_logo:
                lines.append(f"![]({main_logo})")
            
            # 酒店信息行
            price_str = f"¥{int(price)}" if price and price > 0 else "暂无报价"
            score_str = f"**{score}分（分贝通真实评分）**" if score and score != '-' else ""
            star_str_display = f"**{star}（分贝通星级）**" if star and star != '-' else ""
            
            # 预算符合标记
            budget_mark = ""
            if budget and price and price <= budget:
                budget_mark = "✅符合预算"
            
            lines.append(f"**{i}. {name}**")
            if star_str_display:
                lines.append(f"   🏷️ {star_str_display} | 📍 {district}")
            if score_str:
                lines.append(f"   ⭐ {score_str}")
            lines.append(f"   💰 {price_str}起 {budget_mark}")
            
            # 推荐理由（根据酒店特征自动生成）
            reasons = []
            
            # 预算符合
            if budget and price and price <= budget:
                reasons.append("✅预算范围内")
            
            # 高评分
            if score and float(score) >= 4.7:
                reasons.append("⭐评分优秀")
            
            # 连锁品牌（亚朵、全季、秋果等）
            chain_brands = ['亚朵', '全季', '秋果', '如家', '汉庭', '希尔顿', '万豪', '洲际']
            if any(brand in name for brand in chain_brands):
                reasons.append("🏷️知名连锁品牌")
            
            # 地铁附近（关键词包含地铁）
            if '地铁' in name or (keywords and '地铁' in keywords):
                reasons.append("🚇临近地铁")
            
            # 价格优势
            if price and price <= 200:
                reasons.append("💰性价比超高")
            elif price and price <= 500:
                reasons.append("💰价格适中")
            
            # 新装修（关键词或名称包含新）
            if '新' in name or keywords and '新' in keywords:
                reasons.append("🆕装修较新")
            
            # 显示推荐理由
            if reasons:
                lines.append(f"   📌 推荐理由：{' | '.join(reasons[:3])}")
            
            lines.append("")
        
        lines.append("---")
        lines.append("💡 回复 **序号** 查看房型价格，如 **1**")
        lines.append("💡 回复 **序号-详情** 查看酒店信息和评论，如 **1-详情**")
        
        return "\n".join(lines)
    
    def format_hotel_price(self, data: Dict, check_in: str, check_out: str) -> str:
        """格式化酒店价格详情 - 支持图片内嵌展示"""
        hotel = data.get("data", {}).get("hotel", {})
        rooms = data.get("data", {}).get("rooms", [])
        
        if not rooms:
            return "🔍 暂无可用房型，建议调整入住日期"
        
        lines = []
        
        # 酒店图片
        main_logo = hotel.get('main_logo', '')
        if main_logo:
            lines.append(f"![]({main_logo})")
        
        # 酒店基本信息
        name = hotel.get('name', '-')
        address = hotel.get('address', '-')
        score = hotel.get('score', '-')
        star = hotel.get('star_level_name', '-')
        phone = hotel.get('phone', '')
        
        lines.append(f"## 🏨 {name}\n")
        
        # 数据真实性标注
        score_str = f"**{score}分（分贝通真实评分）**" if score and score != '-' else ""
        star_str = f"**{star}（分贝通星级）**" if star and star != '-' else ""
        
        lines.append(f"📍 {address}")
        if star_str:
            lines.append(f"🏷️ {star_str}")
        if score_str:
            lines.append(f"⭐ {score_str}")
        if phone:
            lines.append(f"📞 {phone}")
        
        lines.append(f"\n📅 入住：{check_in} → 退房：{check_out}\n")
        lines.append("---\n")
        
        # 过滤有效房型
        valid_rooms = []
        for room in rooms:
            if not room.get('status', False):
                continue
            plan_list = room.get('plan_list', [])
            valid_plans = [p for p in plan_list if p.get('status', False)]
            if valid_plans:
                valid_plans.sort(key=lambda x: float(x.get('total_price', 999999)))
                room['_valid_plans'] = valid_plans
                room['_min_price'] = float(valid_plans[0].get('total_price', 0))
                valid_rooms.append(room)
        
        valid_rooms.sort(key=lambda x: x.get('_min_price', 999999))
        
        for i, room in enumerate(valid_rooms[:5], 1):
            room_name = room.get('room_name', '-')
            bed_type = room.get('bed_type', '-')
            window_type = room.get('window_type', '-')
            area = room.get('area', '-')
            
            lines.append(f"### 房型 {i}：{room_name}\n")
            lines.append(f"- 🛏️ 床型：{bed_type}")
            lines.append(f"- 🪟 窗户：{window_type}")
            lines.append(f"- 📐 面积：{area}")
            lines.append("")
            
            lines.append("| 序号 | 价格 | 早餐 | 取消政策 |")
            lines.append("|:---:|---:|:---:|:---:|")
            
            for j, p in enumerate(room.get('_valid_plans', [])[:5], 1):
                price = float(p.get('total_price', 0))
                breakfast = p.get('breakfast', {}).get('value', '无早')
                cancel_type = p.get('cancel_type', {}).get('value', '-')
                cancel_rule = p.get('cancel_rule', '')
                
                # 取消政策简化展示
                cancel_display = cancel_type
                if '限时' in cancel_type or '免费' in cancel_type:
                    cancel_display = f"✅ {cancel_type}"
                elif '不可' in cancel_type:
                    cancel_display = f"❌ {cancel_type}"
                
                lines.append(f"| **{i}-{j}** | ¥{int(price)}（实时价格） | {breakfast} | {cancel_display} |")
            
            lines.append("")
        
        lines.append("---")
        lines.append("💡 回复 **房型序号-产品序号 + 入住人信息** 预订")
        lines.append("   示例：**1-1 郜文彬 13800138000**")
        
        # 预订链接提示
        lines.append("\n👉 选择房型后可直接预订，支付链接将在订单创建后提供")
        
        return "\n".join(lines)
    
    def format_order_result(self, data: Dict, check_in: str, check_out: str, room_name: str, total_price: float) -> str:
        """格式化订单创建结果"""
        order_data = data.get("data", {})
        order_id = order_data.get("order_id", "")
        last_cancel_time = order_data.get("last_cancel_time", "")
        
        lines = []
        lines.append("## ✅ 订单创建成功！\n")
        
        # 订单信息表格
        lines.append("| 项目 | 详情 |")
        lines.append("|:---:|:---:|")
        lines.append(f"| **订单号** | {order_id} |")
        lines.append(f"| **入住** | {check_in} → {check_out} |")
        lines.append(f"| **房型** | {room_name} |")
        lines.append(f"| **价格** | ¥{int(total_price)}（分贝通实时价格） |")
        
        if last_cancel_time:
            lines.append(f"| **最晚取消** | {last_cancel_time} |")
        
        lines.append("")
        
        # 支付链接（标准格式）
        pay_url = f"{self.base_url}/business/hotel/open/push/redirect?orderId={order_id}&type=0&token={self.access_token}"
        detail_url = f"{self.base_url}/business/hotel/open/push/redirect?orderId={order_id}&type=1&token={self.access_token}"
        
        lines.append(f"👉 [立即支付]({pay_url})")
        lines.append(f"🔗 [查看订单详情]({detail_url})")
        
        lines.append("")
        lines.append("---")
        lines.append("⚠️ 请尽快完成支付，超时订单将自动取消！")
        
        return "\n".join(lines)


# ==================== 认证辅助函数 ====================

def send_verification_code(mobile: str) -> Dict:
    """
    发送验证码（独立函数，不需要token）
    
    Args:
        mobile: 手机号
    
    Returns:
        发送结果
    """
    api = FbHotelApi()
    return api.send_captcha(mobile)


def verify_and_get_token(mobile: str, captcha: str) -> tuple:
    """
    验证验证码并获取token，成功后自动保存到 ~/.fbt-auth.json
    
    Args:
        mobile: 手机号
        captcha: 验证码
    
    Returns:
        (success, identity_code or error_message)
    """
    api = FbHotelApi()
    try:
        result = api.verify_captcha(mobile, captcha)
        identity_code = result.get("data", {}).get("identity_code", "")
        if identity_code:
            # 自动保存到文件
            if save_auth_token(identity_code, mobile):
                return True, identity_code
            else:
                return True, identity_code  # 返回成功但提示保存失败
        return False, "获取身份编码失败"
    except FbHotelApiError as e:
        return False, str(e)


# ==================== 测试代码 ====================

def print_usage():
    """打印使用说明"""
    print("""
================================================================================
分贝通酒店助手
================================================================================
用法: python3 hotel_api.py <命令> [参数]

命令:
  search <城市> <关键词> [入住日期] [退房日期] [预算] [等级]
                                                搜索酒店（支持预算过滤、等级筛选、价格排序）
  price <酒店ID> <入住日期> <退房日期>          查询房型价格
  detail <酒店ID>                               查询酒店详情
  comment <酒店ID>                              查询酒店评论
  query <订单ID>                                查询订单
  cancel <订单ID> [原因]                        取消订单
  book <酒店ID> <房型> <入住人> <手机号>         快速预订（从缓存读取）

示例:
  python3 hotel_api.py search 北京市 三元桥附近 2026-03-26 2026-03-27 500 舒适型
  python3 hotel_api.py price 5a39df2fbbfdc4732360e860 2026-03-26 2026-03-27
================================================================================
""")


if __name__ == "__main__":
    # 导入缓存模块
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from scripts.cache_price import load_price_cache, get_room_plan
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(0)
    
    api = FbHotelApi()
    command = sys.argv[1].lower()
    
    try:
        if command == "search":
            if len(sys.argv) < 4:
                print("用法: hotel_api.py search <城市> <关键词> [入住日期] [退房日期] [预算] [等级]")
                sys.exit(1)
            city_name = sys.argv[2]
            keywords = sys.argv[3]
            check_in = sys.argv[4] if len(sys.argv) > 4 else None
            check_out = sys.argv[5] if len(sys.argv) > 5 else None
            budget = float(sys.argv[6]) if len(sys.argv) > 6 else None
            star_level = sys.argv[7] if len(sys.argv) > 7 else None
            
            result = api.search_hotel_list(city_name=city_name, keywords=keywords)
            print(api.format_hotel_list(result, check_in, budget, star_level, keywords))
            
        elif command == "price":
            if len(sys.argv) < 5:
                print("用法: hotel_api.py price <酒店ID> <入住日期> <退房日期>")
                sys.exit(1)
            hotel_id = sys.argv[2]
            check_in = sys.argv[3]
            check_out = sys.argv[4]
            
            result = api.query_hotel_price(hotel_id, check_in, check_out)
            print(api.format_hotel_price(result, check_in, check_out))
            
        elif command == "detail":
            if len(sys.argv) < 3:
                print("用法: hotel_api.py detail <酒店ID>")
                sys.exit(1)
            result = api.query_hotel_detail(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "comment":
            if len(sys.argv) < 3:
                print("用法: hotel_api.py comment <酒店ID>")
                sys.exit(1)
            result = api.query_hotel_comment(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "query":
            if len(sys.argv) < 3:
                print("用法: hotel_api.py query <订单ID>")
                sys.exit(1)
            result = api.query_order(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "cancel":
            if len(sys.argv) < 3:
                print("用法: hotel_api.py cancel <订单ID> [原因]")
                sys.exit(1)
            order_id = sys.argv[2]
            reason = sys.argv[3] if len(sys.argv) > 3 else "用户主动取消"
            result = api.cancel_order(order_id, reason)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif command == "book":
            # 快速预订 - 从缓存读取room_id和plan_id
            if len(sys.argv) < 6:
                print("用法: hotel_api.py book <酒店ID> <房型名称> <入住人> <手机号>")
                sys.exit(1)
            
            hotel_id = sys.argv[2]
            room_name = sys.argv[3]
            guest_name = sys.argv[4]
            guest_phone = sys.argv[5]
            
            cache = load_price_cache()
            if not cache or cache.get("hotel_id") != hotel_id:
                print("错误: 无价格缓存，请先查询价格")
                sys.exit(1)
            
            check_in = cache.get("check_in")
            check_out = cache.get("check_out")
            
            # 从缓存获取room_id和plan_id
            room_id, plan_id, total_price = get_room_plan(hotel_id, room_name)
            
            if not room_id:
                print(f"错误: 未找到房型 '{room_name}'")
                sys.exit(1)
            
            # 快速创建订单
            result = api.create_order(
                hotel_id=hotel_id,
                room_id=room_id,
                plan_id=plan_id,
                check_in_date=check_in,
                check_out_date=check_out,
                total_price=total_price,
                contact={'name': guest_name, 'phone': guest_phone},
                guest_list=[[guest_name]]
            )
            
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            if result.get("success"):
                order_id = result['data']['order_id']
                token = load_auth_token()
                print(f"订单号: {order_id}")
                print(f"[点击支付](https://app-gate.fenbeitong.com/business/hotel/open/push/redirect?orderId={order_id}&type=0&token={token})")
            
        else:
            print(f"未知命令: {command}")
            print_usage()
            
    except FbHotelApiError as e:
        print(f"错误: {e}")
        sys.exit(1)