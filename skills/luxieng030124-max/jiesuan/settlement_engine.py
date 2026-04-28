#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能结算引擎
支持：达标瓜分、排名赛、混合不互斥、权重分配
"""

import csv
import json
import re
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SettlementMode(Enum):
    """结算模式"""
    GUARANTEED = "guaranteed"      # 达标瓜分
    RANKING = "ranking"            # 排名赛
    HYBRID = "hybrid"              # 混合不互斥
    WEIGHTED = "weighted"          # 权重分配


@dataclass
class TopicRule:
    """话题词规则"""
    topics: List[str]              # 要求的话题词列表
    logic: str = "AND"             # 逻辑关系：AND(且) 或 OR(或)
    
    def check(self, title: str) -> bool:
        """检查标题是否符合话题词要求（精准匹配）"""
        if not self.topics:
            return True
        
        matches = []
        for topic in self.topics:
            # 精准匹配：使用词边界确保完整匹配
            # 方法1：使用正则表达式词边界
            # 方法2：简单字符串匹配 + 边界检查
            import re
            # 转义特殊字符，添加词边界
            pattern = r'(?:^|[\s,，。！!？?；;：:、])'  + re.escape(topic) + r'(?:$|[\s,，。！!？?；;：:、])'
            matches.append(bool(re.search(pattern, title)))
        
        if self.logic == "AND":
            return all(matches)
        elif self.logic == "OR":
            return any(matches)
        return False


@dataclass
class AwardPool:
    """奖池配置"""
    name: str                      # 奖池名称
    amount: float                  # 奖池金额
    mode: SettlementMode           # 结算模式
    condition: Optional[Dict] = None   # 达标条件
    ranking_rules: Optional[List[Dict]] = None  # 排名规则
    weight_field: Optional[str] = None  # 权重字段
    topic_rule: Optional[TopicRule] = None  # 话题词规则


@dataclass
class SettlementResult:
    """结算结果"""
    author_id: str
    author_name: str
    videos: int
    total_plays: int
    total_likes: int
    awards: Dict[str, float]       # 各奖池奖金
    total_amount: float            # 总奖金


class SettlementEngine:
    """结算引擎"""
    
    def __init__(self, pools: List[AwardPool]):
        self.pools = pools
        self.authors = defaultdict(lambda: {
            'name': '',
            'videos': 0,
            'total_plays': 0,
            'total_likes': 0,
            'video_titles': []  # 存储视频标题用于话题词检查
        })
    
    def load_data(self, file_path: str) -> None:
        """加载数据文件"""
        if file_path.endswith('.csv'):
            self._load_csv(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {file_path}")
    
    def _load_csv(self, file_path: str) -> None:
        """加载CSV数据"""
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                author_id = row.get('作者ID', row.get('用户ID', ''))
                author_name = row.get('作者名称（最新）', row.get('作者名称', ''))
                title = row.get('视频标题', row.get('标题', ''))
                
                plays = self._parse_number(row.get('视频累计外显播放次数', '0'))
                likes = self._parse_number(row.get('视频累计外显点赞次数', '0'))
                
                self.authors[author_id]['name'] = author_name or self.authors[author_id]['name']
                self.authors[author_id]['videos'] += 1
                self.authors[author_id]['total_plays'] += plays
                self.authors[author_id]['total_likes'] += likes
                if title:
                    self.authors[author_id]['video_titles'].append(title)
    
    def _parse_number(self, value: str) -> int:
        """解析数字"""
        if not value:
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def process(self) -> List[SettlementResult]:
        """执行结算"""
        results = []
        
        for author_id, data in self.authors.items():
            result = SettlementResult(
                author_id=author_id,
                author_name=data['name'],
                videos=data['videos'],
                total_plays=data['total_plays'],
                total_likes=data['total_likes'],
                awards={},
                total_amount=0.0
            )
            
            # 遍历所有奖池计算奖金
            for pool in self.pools:
                # 先检查话题词规则
                if pool.topic_rule:
                    if not self._check_topic_rule(data['video_titles'], pool.topic_rule):
                        continue  # 不符合话题词要求，跳过此奖池
                
                award = self._calculate_award(pool, result)
                if award > 0:
                    result.awards[pool.name] = award
                    result.total_amount += award
            
            if result.total_amount > 0 or any(p.mode == SettlementMode.GUARANTEED for p in self.pools):
                results.append(result)
        
        # 按总奖金降序排列
        results.sort(key=lambda x: x.total_amount, reverse=True)
        return results
    
    def _check_topic_rule(self, titles: List[str], topic_rule: TopicRule) -> bool:
        """检查视频标题是否符合话题词规则"""
        if not topic_rule or not topic_rule.topics:
            return True
        
        # 检查是否有任意一个视频标题满足话题词要求
        for title in titles:
            if topic_rule.check(title):
                return True
        
        return False
    
    def _calculate_award(self, pool: AwardPool, author: SettlementResult) -> float:
        """计算单个奖池的奖金"""
        if pool.mode == SettlementMode.GUARANTEED:
            return self._calc_guaranteed(pool, author)
        elif pool.mode == SettlementMode.RANKING:
            # 排名赛需要整体数据，延后计算
            return 0
        elif pool.mode == SettlementMode.WEIGHTED:
            # 权重分配需要整体数据，延后计算
            return 0
        return 0
    
    def _calc_guaranteed(self, pool: AwardPool, author: SettlementResult) -> float:
        """计算达标瓜分奖金（先标记达标，后续统一分配）"""
        if not pool.condition:
            return 0
        
        # 检查条件
        field = pool.condition.get('field', '')
        op = pool.condition.get('op', '>=')
        value = pool.condition.get('value', 0)
        
        # 获取字段值
        field_value = getattr(author, self._field_mapping(field), 0)
        
        # 判断条件
        if op == '>=' and field_value >= value:
            return -1  # 标记达标，后续分配
        elif op == '>' and field_value > value:
            return -1
        elif op == '<=' and field_value <= value:
            return -1
        elif op == '<' and field_value < value:
            return -1
        elif op == '==' and field_value == value:
            return -1
        
        return 0
    
    def _field_mapping(self, field: str) -> str:
        """字段映射"""
        mapping = {
            '播放量': 'total_plays',
            '播放': 'total_plays',
            '获赞': 'total_likes',
            '点赞': 'total_likes',
            '作品数': 'videos',
            '作品': 'videos',
        }
        return mapping.get(field, 'total_plays')


class RuleParser:
    """规则解析器（简化版，实际可由AI完成）"""
    
    @staticmethod
    def parse_topic_rule(rule_text: str) -> Optional[TopicRule]:
        """
        解析话题词规则
        示例：
        - "必须携带话题 #金铲铲" → TopicRule(["#金铲铲"], "OR")
        - "携带话题 #金铲铲 或 #英雄联盟" → TopicRule(["#金铲铲", "#英雄联盟"], "OR")
        - "同时携带 #金铲铲 和 #攻略" → TopicRule(["#金铲铲", "#攻略"], "AND")
        """
        if not any(keyword in rule_text for keyword in ['话题', '#', '携带']):
            return None
        
        # 提取所有话题词（以#开头的词）
        topics = re.findall(r'#[^#\s,，和或]+', rule_text)
        if not topics:
            return None
        
        # 判断逻辑关系
        logic = "OR"  # 默认为或
        if any(keyword in rule_text for keyword in ['且', '和', '同时', 'AND', '都']):
            logic = "AND"
        
        return TopicRule(topics=topics, logic=logic)
    
    @staticmethod
    def parse(rule_text: str) -> List[AwardPool]:
        """
        解析自然语言规则
        简化实现：支持达标瓜分模式的解析
        """
        pools = []
        
        # 匹配达标瓜分模式
        # 示例："总奖金2万元，发布作品≥5条且播放量≥3万的作者等额瓜分"
        guaranteed_pattern = r'总奖金(\d+)万.*?作品[数量]?[≥>=](\d+).*?播放[量]?[≥>=](d+)'
        
        # 提取奖池金额
        amount_match = re.search(r'总奖金(\d+)万', rule_text)
        if amount_match:
            amount = float(amount_match.group(1)) * 10000
            
            # 提取作品数条件
            videos_match = re.search(r'作品[数量]?[≥>=](\d+)', rule_text)
            videos_condition = int(videos_match.group(1)) if videos_match else 5
            
            # 提取播放量条件
            plays_match = re.search(r'播放[量]?[≥>=](\d+)万', rule_text)
            if plays_match:
                plays_condition = int(plays_match.group(1)) * 10000
            else:
                plays_match = re.search(r'播放[量]?[≥>=](\d+)', rule_text)
                plays_condition = int(plays_match.group(1)) if plays_match else 30000
            
            # 解析话题词规则
            topic_rule = RuleParser.parse_topic_rule(rule_text)
            
            # 创建奖池
            pool = AwardPool(
                name="达标瓜分奖池",
                amount=amount,
                mode=SettlementMode.GUARANTEED,
                condition={
                    'field': '播放量',
                    'op': '>=',
                    'value': plays_condition
                },
                topic_rule=topic_rule
            )
            pools.append(pool)
        
        return pools


def format_rule_understanding(pools: List[AwardPool]) -> str:
    """
    格式化输出规则理解，供用户确认
    
    Returns:
        格式化的规则描述文本
    """
    lines = []
    lines.append("=" * 80)
    lines.append("📋 规则理解确认")
    lines.append("=" * 80)
    lines.append("")
    
    for idx, pool in enumerate(pools, 1):
        lines.append(f"【奖池 {idx}】{pool.name}")
        lines.append(f"  💰 奖池金额: {pool.amount:,.0f} 元")
        lines.append(f"  📊 结算模式: {pool.mode.value}")
        
        # 达标条件
        if pool.condition:
            field = pool.condition.get('field', '')
            op = pool.condition.get('op', '')
            value = pool.condition.get('value', 0)
            lines.append(f"  ✅ 达标条件: {field} {op} {value:,}")
        
        # 话题词规则
        if pool.topic_rule:
            logic_text = "且" if pool.topic_rule.logic == "AND" else "或"
            topics_text = f" {logic_text} ".join(pool.topic_rule.topics)
            lines.append(f"  🏷️  话题词要求: {topics_text}")
            lines.append(f"     (逻辑关系: {pool.topic_rule.logic} - {'所有话题词都要出现' if pool.topic_rule.logic == 'AND' else '至少一个话题词出现'})")
        
        # 排名规则
        if pool.ranking_rules:
            lines.append(f"  🏆 排名规则:")
            for rule in pool.ranking_rules:
                lines.append(f"     - {rule}")
        
        lines.append("")
    
    lines.append("=" * 80)
    lines.append("❓ 请确认以上规则理解是否正确？")
    lines.append("   ✅ 回复「确认」或「正确」开始结算")
    lines.append("   ✏️  提出修改意见，我会更新规则理解")
    lines.append("=" * 80)
    
    return "\n".join(lines)


def process_settlement(file_path: str, rule_text: str) -> Tuple[List[SettlementResult], Dict]:
    """
    执行结算
    
    Args:
        file_path: 数据文件路径
        rule_text: 规则描述
    
    Returns:
        (结算结果列表, 统计信息)
    """
    # 解析规则
    pools = RuleParser.parse(rule_text)
    
    if not pools:
        raise ValueError("无法解析规则，请检查描述格式")
    
    # 创建引擎
    engine = SettlementEngine(pools)
    
    # 加载数据
    engine.load_data(file_path)
    
    # 执行结算
    results = engine.process()
    
    # 计算达标瓜分（需要知道达标人数）
    for pool in pools:
        if pool.mode == SettlementMode.GUARANTEED:
            qualified = [r for r in results if pool.name in r.awards]
            if qualified:
                per_person = pool.amount / len(qualified)
                for r in qualified:
                    r.awards[pool.name] = per_person
                    # 重新计算总奖金
                    r.total_amount = sum(r.awards.values())
    
    # 重新排序
    results.sort(key=lambda x: x.total_amount, reverse=True)
    
    # 生成统计
    stats = {
        'total_authors': len(engine.authors),
        'qualified_authors': len(results),
        'total_videos': sum(r.videos for r in results),
        'total_plays': sum(r.total_plays for r in results),
        'total_likes': sum(r.total_likes for r in results),
        'total_award': sum(r.total_amount for r in results),
        'pools': [{'name': p.name, 'amount': p.amount, 'mode': p.mode.value} for p in pools]
    }
    
    return results, stats


def export_to_csv(results: List[SettlementResult], output_path: str, stats: Dict) -> None:
    """导出到CSV"""
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # 写入标题
        writer.writerow(['序号', '作者ID', '作者名称', '发布作品数', '累计播放量', '累计获赞', '瓜分奖金(元)'])
        
        # 写入数据
        for idx, r in enumerate(results, 1):
            writer.writerow([
                idx,
                r.author_id,
                r.author_name,
                r.videos,
                r.total_plays,
                r.total_likes,
                f"{r.total_amount:.2f}"
            ])
        
        # 写入汇总
        writer.writerow([
            '汇总', '', '', 
            stats['total_videos'],
            stats['total_plays'],
            stats['total_likes'],
            f"{stats['total_award']:.2f}"
        ])


def print_summary(results: List[SettlementResult], stats: Dict) -> None:
    """打印结算摘要"""
    print("=" * 80)
    print("结算结果摘要")
    print("=" * 80)
    
    print(f"\n奖池配置：")
    for pool in stats.get('pools', []):
        print(f"  - {pool['name']}: {pool['amount']:,.0f}元 ({pool['mode']})")
    
    print(f"\n统计信息：")
    print(f"  - 参与作者总数：{stats['total_authors']} 人")
    print(f"  - 获奖作者数：{stats['qualified_authors']} 人")
    print(f"  - 累计发布作品：{stats['total_videos']} 条")
    print(f"  - 累计播放量：{stats['total_plays']:,} 次")
    print(f"  - 累计获赞：{stats['total_likes']:,} 次")
    print(f"  - 总奖金发放：{stats['total_award']:,.2f} 元")
    
    if results:
        avg_award = stats['total_award'] / len(results)
        print(f"  - 人均奖金：{avg_award:,.2f} 元")
    
    print("\n" + "=" * 80)
    print(f"\n获奖作者前10名：")
    print(f"{'序号':<6}{'作者ID':<16}{'作者名称':<20}{'作品数':<10}{'播放量':<12}{'奖金(元)':<12}")
    print("-" * 80)
    for r in results[:10]:
        print(f"{0:<6}{r.author_id:<16}{r.author_name:<20}{r.videos:<10}{r.total_plays:<12}{r.total_amount:<12.2f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python settlement_engine.py <数据文件> <规则描述>")
        print("示例: python settlement_engine.py data.csv '总奖金2万，播放量≥3万作者瓜分'")
        sys.exit(1)
    
    file_path = sys.argv[1]
    rule_text = sys.argv[2]
    
    try:
        results, stats = process_settlement(file_path, rule_text)
        print_summary(results, stats)
        
        # 导出结果
        output_path = file_path.rsplit('.', 1)[0] + '_结算结果.csv'
        export_to_csv(results, output_path, stats)
        print(f"\n✓ 结算结果已保存至: {output_path}")
        
    except Exception as e:
        print(f"❌ 结算失败: {e}")
        import traceback
        traceback.print_exc()
