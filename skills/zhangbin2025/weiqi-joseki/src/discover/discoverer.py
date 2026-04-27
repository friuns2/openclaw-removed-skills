#!/usr/bin/env python3
"""
定式发现模块 (discover)
替代原match/identify接口，简化设计
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from ..extraction import extract_moves_all_corners, get_move_sequence
from ..core.coords import convert_to_top_right
from ..matching import TrieMatcher, PrefixMatchResult
from ..builder import convert_to_rudl


@dataclass
class DiscoverResult:
    """定式发现结果"""
    joseki_id: str      # 定式ID
    moves: str          # 完整着法串
    prefix: str         # 匹配的前缀着法串
    prefix_len: int     # 匹配的前缀长度
    total_moves: int    # 着法串长度
    source_corner: str  # 棋谱来源角 "tl"/"tr"/"bl"/"br"


class JosekiDiscoverer:
    """定式发现器"""
    
    def __init__(self, joseki_list: List[dict]):
        """
        初始化发现器
        
        Args:
            joseki_list: 定式列表，每个定式包含 id, name, moves
        """
        self.matcher = TrieMatcher()
        self.matcher.build(joseki_list)
    
    def discover_corner(self, moves: List[str], corner: str) -> Optional[DiscoverResult]:
        """
        发现单个角的定式
        
        Args:
            moves: 着法坐标列表（原始SGF坐标）
            corner: 来源角 "tl"/"tr"/"bl"/"br"
        
        Returns:
            最佳匹配的DiscoverResult，无匹配返回None
        """
        if not moves or len(moves) < 2:
            return None
        
        tr_moves = convert_to_top_right(moves, corner)
        
        # 尝试ruld方向
        ruld_match = self.matcher.match(tr_moves, top_k=1)
        ruld_len = ruld_match[0].prefix_len if ruld_match else 0
        
        # 尝试rudl方向
        rudl_moves = convert_to_rudl(tr_moves)
        rudl_match = self.matcher.match(rudl_moves, top_k=1)
        rudl_len = rudl_match[0].prefix_len if rudl_match else 0
        
        # 取匹配最长的返回
        if ruld_len >= rudl_len and ruld_len > 0:
            return DiscoverResult(
                joseki_id=ruld_match[0].id,
                moves=" ".join(tr_moves),
                prefix=" ".join(tr_moves[:ruld_len]),
                prefix_len=ruld_len,
                total_moves=len(tr_moves),
                source_corner=corner,
            )
        elif rudl_len > 0:
            return DiscoverResult(
                joseki_id=rudl_match[0].id,
                moves=" ".join(rudl_moves),
                prefix=" ".join(rudl_moves[:rudl_len]),
                prefix_len=rudl_len,
                total_moves=len(rudl_moves),
                source_corner=corner,
            )
        
        return None
    
    def discover(self, sgf_data: str, first_n: int = 80,
                 distance_threshold: int = 4) -> Dict[str, DiscoverResult]:
        """
        从SGF发现定式
        
        Args:
            sgf_data: SGF棋谱内容
            first_n: 提取前N手
            distance_threshold: 连通块距离阈值
        
        Returns:
            {corner: DiscoverResult, ...}
            corner: "tl"/"tr"/"bl"/"br"
        """
        # 使用新提取接口提取四角着法
        corner_moves_dict = extract_moves_all_corners(
            sgf_data, 
            first_n=first_n, 
            distance_threshold=distance_threshold
        )
        
        results = {}
        
        for corner in ['tl', 'tr', 'bl', 'br']:
            moves = corner_moves_dict.get(corner)
            if not moves:
                continue
            
            coords = get_move_sequence(moves)
            match = self.discover_corner(coords, corner)
            if match:
                results[corner] = match
        
        return results


def discover_joseki(
    sgf_data: str,
    joseki_list: List[dict],
    first_n: int = 80,
    distance_threshold: int = 4
) -> Dict[str, DiscoverResult]:
    """
    便捷函数：从SGF发现定式
    
    Args:
        sgf_data: SGF棋谱内容
        joseki_list: 定式列表
        first_n: 提取前N手
        distance_threshold: 连通块距离阈值
    
    Returns:
        {corner: DiscoverResult, ...}
    """
    discoverer = JosekiDiscoverer(joseki_list)
    return discoverer.discover(sgf_data, first_n, distance_threshold)
