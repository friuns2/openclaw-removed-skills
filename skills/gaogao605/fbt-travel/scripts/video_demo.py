#!/usr/bin/env python3
"""
酒店视频展示Demo模块 - v2.6.0
展示酒店地图、视频、竞对价格对比
"""

import json
from typing import Dict, List, Optional


class HotelVideoDemo:
    """酒店视频展示Demo"""
    
    # 柏曼酒店示例数据
    DEMO_HOTEL = {
        "name": "柏曼酒店(北京三元桥燕莎使馆区店)",
        "rating": 4.5,
        "level": "舒适型",
        "price_fbt": 299,
        "address": "朝阳区东三环北路乙2号",
        "transport": "三元桥地铁站步行5分钟",
        "video_url": "https://www.toutiao.com/video/7387363262121116194/",
        "map_url": "https://map.360.cn/?pid=2e9fa871d74e5996&src=seo",
        "recommend_reasons": [
            "评分优秀4.5分",
            "临近三元桥地铁站",
            "燕莎使馆区核心位置",
            "性价比高"
        ],
        "competitors": [
            {
                "platform": "携程",
                "price": 328,
                "url": "http://hotels.ctrip.com/hotel/117473236.html?allianceid=12710&sid=353961&ouid="
            },
            {
                "platform": "同程",
                "price": 315,
                "url": "https://hotel.qunar.com/cn/beijing/d_baiman_hotel_san_yuan_qiao_yan_sha_embassy_area_branch?cityId=1"
            },
            {
                "platform": "飞猪",
                "price": 308,
                "url": "https://www.fliggy.com/hotel/detail?id=117473236"
            }
        ]
    }
    
    def format_demo_output(self, hotel_data: Optional[Dict] = None) -> str:
        """
        格式化Demo输出
        
        Args:
            hotel_data: 酒店数据，默认使用DEMO_HOTEL
            
        Returns:
            格式化的Markdown输出
        """
        data = hotel_data or self.DEMO_HOTEL
        
        output = []
        
        # 标题
        output.append(f"---\n**📦 Demo展示：{data['name']}（地图+视频+竞对价格对比）**\n---")
        
        # 酒店名称
        output.append(f"\n**🏨 {data['name']}**\n")
        
        # 地图链接
        output.append("**📍 酒店地图**\n")
        output.append(f"\n[点击查看地图]({data['map_url']})\n")
        
        # 视频链接
        output.append("\n**🎬 宣传视频**\n")
        output.append(f"\n[点击观看视频]({data['video_url']})\n")
        
        # 竞对价格对比
        output.append("\n**💰 竞对价格对比**\n")
        output.append("\n| 平台 | 价格 | 预订链接 |")
        output.append("|:---:|---:|:---:|")
        
        # 先显示OTA平台
        for comp in data['competitors']:
            output.append(f"| {comp['platform']} | ¥{comp['price']}起 | [点击预订]({comp['url']}) |")
        
        # 最后显示分贝通（最低价）
        output.append(f"| 分贝通 | ¥{data['price_fbt']}起 ⭐ | [点击预订](https://www.fenbeitong.com/hotel/detail?id=117473236) |")
        
        output.append("\n\n💡 分贝通企业价通常比OTA平台优惠5-15%\n")
        
        # 酒店详情
        output.append("**项目 | 详情**\n")
        output.append("|:---:|:---:|")
        output.append(f"| 🏷️ 酒店等级 | {data['level']} |")
        output.append(f"| ⭐ 用户评分 | {data['rating']}分 |")
        output.append(f"| 💰 价格 | ¥{data['price_fbt']}起 |")
        output.append(f"| 📍 地址 | {data['address']} |")
        output.append(f"| 🚇 交通 | {data['transport']} |")
        
        # 推荐理由
        output.append("\n**📌 推荐理由**\n")
        for reason in data['recommend_reasons']:
            output.append(f"- ✅ {reason}")
        
        # 价格对比优势表
        output.append("\n**💡 价格对比优势**\n")
        output.append("\n| 平台 | 价格 | 与分贝通对比 |")
        output.append("|:---:|---:|:---:|")
        
        fbt_price = data['price_fbt']
        for comp in data['competitors']:
            diff = comp['price'] - fbt_price
            pct = (diff / fbt_price) * 100
            output.append(f"| {comp['platform']} | ¥{comp['price']} | 高¥{diff}（+{pct:.1f}%） |")
        
        output.append(f"| 分贝通 | ¥{fbt_price} ⭐ | 最低价 |")
        
        return "\n".join(output)
    
    def run_demo(self):
        """运行Demo"""
        print(self.format_demo_output())


def main():
    """主函数"""
    demo = HotelVideoDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()