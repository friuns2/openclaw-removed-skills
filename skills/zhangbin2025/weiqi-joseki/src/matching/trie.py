#!/usr/bin/env python3
"""
Trie树实现
用于定式着法串的前缀匹配
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class PrefixMatchResult:
    """前缀匹配结果 - 最长前缀优先，同前缀选总手数最短的"""
    id: str
    name: str
    prefix_len: int      # 匹配的前缀长度（最长优先）
    total_moves: int     # 定式总手数（同前缀时越短越优先）
    matched_direction: str  # "ruld" 或 "rudl"


class TrieMatcher:
    """Trie树匹配器 - 支持ruld和rudl两个方向"""
    
    def __init__(self):
        self._trie: Dict = {}      # ruld方向前缀树
        self._trie_rudl: Dict = {} # rudl方向前缀树
        self._joseki_map: Dict[str, dict] = {}  # id -> 定式数据
    
    def build(self, joseki_list: List[dict]):
        """
        从定式列表构建Trie树
        
        Args:
            joseki_list: 定式列表，每个定式包含 id, name, moves
        """
        self._trie = {}
        self._trie_rudl = {}
        self._joseki_map = {}
        
        for j in joseki_list:
            joseki_id = j.get("id")
            if not joseki_id:
                continue
            
            self._joseki_map[joseki_id] = j
            moves = j.get("moves", [])
            if not moves:
                continue
            
            # ruld方向入树
            self._add_to_trie(self._trie, moves, joseki_id)
            
            # rudl方向入树
            rudl_moves = self._convert_to_rudl(moves)
            self._add_to_trie(self._trie_rudl, rudl_moves, joseki_id)
    
    def _add_to_trie(self, trie: dict, moves: List[str], joseki_id: str):
        """将定式着法序列加入前缀树"""
        node = trie
        for move in moves:
            if move not in node:
                node[move] = {'next': {}, 'ids': []}
            node[move]['ids'].append(joseki_id)
            node = node[move]['next']
    
    def match(self, moves: List[str], top_k: int = 3) -> List[PrefixMatchResult]:
        """
        匹配着法序列，返回最佳匹配的定式
        
        Args:
            moves: 着法序列
            top_k: 返回结果数量上限
        
        Returns:
            匹配结果列表，按 prefix_len 降序，相同按 total_moves 升序
        """
        # 在ruld方向匹配
        ruld_results = self._match_direction(self._trie, moves, "ruld")
        
        # 在rudl方向匹配
        rudl_moves = self._convert_to_rudl(moves)
        rudl_results = self._match_direction(self._trie_rudl, rudl_moves, "rudl")
        
        # 合并结果
        all_results = ruld_results + rudl_results
        
        # 按 id 和 direction 去重，保留 prefix_len 最大的
        seen = {}
        for prefix_len, joseki_id, total_moves, direction in all_results:
            key = (joseki_id, direction)
            if key not in seen or seen[key][0] < prefix_len:
                seen[key] = (prefix_len, total_moves, direction)
        
        # 构建结果对象
        results = []
        for (joseki_id, direction), (prefix_len, total_moves, _) in seen.items():
            joseki = self._joseki_map.get(joseki_id, {})
            results.append(PrefixMatchResult(
                id=joseki_id,
                name=joseki.get("name", joseki_id),
                prefix_len=prefix_len,
                total_moves=total_moves,
                matched_direction=direction
            ))
        
        # 排序：按 prefix_len 降序，相同按 total_moves 升序
        results.sort(key=lambda x: (-x.prefix_len, x.total_moves))
        
        return results[:top_k]
    
    def _match_direction(self, trie: dict, moves: List[str], direction: str) -> List[Tuple[int, str, int, str]]:
        """
        在指定方向的Trie中匹配
        
        Returns:
            [(prefix_len, joseki_id, total_moves, direction), ...]
        """
        node = trie
        matched_ids = {}  # id -> 最深匹配长度
        
        for i, move in enumerate(moves):
            if move not in node:
                break
            
            prefix_len = i + 1
            for joseki_id in node[move]['ids']:
                matched_ids[joseki_id] = prefix_len
            
            node = node[move]['next']
        
        # 获取完整定式手数
        results = []
        for joseki_id, match_len in matched_ids.items():
            joseki = self._joseki_map.get(joseki_id, {})
            total_moves = len(joseki.get("moves", []))
            results.append((match_len, joseki_id, total_moves, direction))
        
        return results
    
    @staticmethod
    def _convert_to_rudl(moves: List[str]) -> List[str]:
        """
        将ruld方向的着法序列转换为rudl方向
        
        转换原理:
        ruld: 右上(左→下) - 原点是sa(18,0)
        rudl: 右上(下→左) - 原点是ss(18,18)
        
        对于19路棋盘:
        - ruld局部坐标(x,y) → SGF: chr(ord('a') + (18-x)) + chr(ord('a') + y)
        - rudl局部坐标(x,y) → SGF: chr(ord('a') + (18-y)) + chr(ord('a') + (18-x))
        
        因此转换: (x,y) → (y,x) 然后取反
        """
        rudl_moves = []
        for sgf in moves:
            if not sgf or sgf == 'pass' or sgf == 'tt':
                rudl_moves.append(sgf)
            else:
                # ruld SGF坐标 → 局部坐标
                c = ord(sgf[0]) - ord('a')  # 0-18, ruld中18是左边界
                r = ord(sgf[1]) - ord('a')  # 0-18, ruld中0是上边界
                # ruld局部坐标: x = 18-c, y = r
                x = 18 - c
                y = r
                # rudl局部坐标: x' = y, y' = x
                # rudl SGF: col = 18-y', row = 18-x'
                new_col = 18 - y
                new_row = 18 - x
                new_sgf = chr(ord('a') + new_col) + chr(ord('a') + new_row)
                rudl_moves.append(new_sgf)
        return rudl_moves
