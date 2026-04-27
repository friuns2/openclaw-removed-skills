#!/usr/bin/env python3
"""
KataGo定式库构建器
基于KataGo Archive棋谱构建定式库

核心算法（与原代码保持一致）：
1. Phase 1: CMS统计频率 + 临时文件存储
2. Phase 2: 逆向遍历 + 单链检测 + 小顶堆选top-k
3. Phase 3: 统一转ruld方向去重
4. Phase 4: 入库
"""

import gzip
import heapq
import tempfile
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import Counter
from datetime import datetime

from ..extraction import extract_moves_all_corners, get_move_sequence
from ..extraction.katago_downloader import iter_sgf_from_tar
from ..core.coords import convert_to_top_right
from ..storage.json_storage import JsonStorage, DEFAULT_DB_PATH
from ..utils import CountMinSketch


# 四角配置
CORNERS = ['tl', 'tr', 'bl', 'br']


def convert_to_rudl(moves: List[str]) -> List[str]:
    """
    将ruld方向的着法序列转换为rudl方向
    
    ruld: 右上(左→下) - 原点是sa(18,0)
    rudl: 右上(下→左) - 原点是ss(18,18)
    """
    rudl_moves = []
    for sgf in moves:
        if not sgf or sgf == 'pass' or sgf == 'tt':
            rudl_moves.append(sgf)
        else:
            c = ord(sgf[0]) - ord('a')
            r = ord(sgf[1]) - ord('a')
            x = 18 - c
            y = r
            new_col = 18 - y
            new_row = 18 - x
            new_sgf = chr(ord('a') + new_col) + chr(ord('a') + new_row)
            rudl_moves.append(new_sgf)
    return rudl_moves


def convert_to_ruld(moves: List[str]) -> List[str]:
    """
    将rudl方向的着法序列转换回ruld方向
    （convert_to_rudl的逆操作）
    """
    ruld_moves = []
    for sgf in moves:
        if not sgf or sgf == 'pass' or sgf == 'tt':
            ruld_moves.append(sgf)
        else:
            # rudl SGF坐标 → 局部坐标
            c = ord(sgf[0]) - ord('a')
            r = ord(sgf[1]) - ord('a')
            # rudl局部坐标: x = 18-c, y = 18-r
            x = 18 - c
            y = 18 - r
            # ruld局部坐标: x' = y, y' = x
            # ruld SGF: col = 18-y', row = x'
            new_col = 18 - y
            new_row = x
            new_sgf = chr(ord('a') + new_col) + chr(ord('a') + new_row)
            ruld_moves.append(new_sgf)
    return ruld_moves


class HeapItem:
    """堆项 - 用于小顶堆选top-k"""
    __slots__ = ['count', 'prefix', 'direction', 'prefix_hash']
    
    def __init__(self, count, prefix, direction, prefix_hash):
        self.count = count
        self.prefix = prefix
        self.direction = direction
        self.prefix_hash = prefix_hash
    
    def __lt__(self, other):
        return self.count < other.count


class KatagoJosekiBuilder:
    """
    KataGo定式库构建器
    
    保留原代码核心算法：
    - CMS频率估算
    - 临时文件存储
    - 逆向遍历
    - 单链检测
    - 小顶堆选top-k
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.storage = JsonStorage(db_path)
        # CMS配置（与原代码一致）
        self._cms_width = 200000
        self._cms_depth = 5
    
    def set_cms_config(self, width: int = 200000, depth: int = 5):
        """设置CMS配置（与原代码一致）"""
        self._cms_width = width
        self._cms_depth = depth
    

    
    def process_sgf(self, sgf_data: str, first_n: int = 80, 
                    distance_threshold: int = 4) -> Dict[str, List[str]]:
        """
        处理单个SGF，提取四角着法
        
        Returns:
            {corner: [coord, ...], ...} 原始SGF坐标
        """
        corner_moves = extract_moves_all_corners(
            sgf_data, 
            first_n=first_n, 
            distance_threshold=distance_threshold
        )
        
        # 转换为纯坐标序列
        return {corner: get_move_sequence(moves) 
                for corner, moves in corner_moves.items()}
    
    def build_from_tar(self, 
                       tar_path: str,
                       min_freq: int = 5,
                       top_k: int = 10000,
                       first_n: int = 80,
                       distance_threshold: int = 4,
                       min_moves: int = 4,
                       max_moves: int = 50,
                       verbose: bool = True) -> List[dict]:
        """
        从tar文件构建定式库（完整保留原代码算法）
        
        Args:
            tar_path: tar文件路径
            min_freq: 最小出现频率
            top_k: 入库定式数量上限
            first_n: 提取前N手
            distance_threshold: 连通块距离阈值
            min_moves: 最少手数（前缀从此手数开始提取）
            max_moves: 最多手数
            verbose: 详细输出
        
        Returns:
            入库的定式列表
        """
        # ===== Phase 1: CMS统计 + 临时文件存储 =====
        # 使用高精度CMS配置（width=4194304, depth=4, ~64MB, 误差~0.024%）
        cms = CountMinSketch(width=4194304, depth=4)
        temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.gz', delete=False)
        temp_path = Path(temp_file.name)
        
        if verbose:
            print(f"📊 Phase 1: CMS统计前缀频率（CMS: 4194304x4）")
            print(f"   内存占用: ~64MB, 误差~0.024%")
        
        processed = 0
        joseki_count = 0
        prefix_count = 0
        total_unique_sequences = 0
        
        with gzip.open(temp_path, 'wt', encoding='utf-8') as f_out:
            for sgf_data in iter_sgf_from_tar(tar_path):
                try:
                    # 提取四角着法
                    corner_moves_dict = extract_moves_all_corners(
                        sgf_data, first_n=first_n, distance_threshold=distance_threshold
                    )
                    
                    # 每谱的着法串去重集合
                    seen_sequences = set()
                    
                    # 生成8个方向（四角 × 2方向）
                    for corner in CORNERS:
                        moves = corner_moves_dict.get(corner)
                        if not moves or len(moves) < min_moves:
                            continue
                        
                        # 转换为纯坐标序列
                        coords = get_move_sequence(moves)
                        if len(coords) < min_moves:
                            continue
                        
                        # 转换到右上角视角
                        tr_coords = convert_to_top_right(coords, corner)
                        
                        # 生成ruld和rudl两个方向
                        ruld = " ".join(tr_coords)
                        rudl = " ".join(convert_to_rudl(tr_coords))
                        
                        for direction, seq in [('ruld', ruld), ('rudl', rudl)]:
                            if seq in seen_sequences:
                                continue
                            seen_sequences.add(seq)
                            
                            # 写入临时文件
                            f_out.write(f"{direction}|{seq}\n")
                            joseki_count += 1
                            
                            # 展开所有前缀并更新CMS
                            seq_parts = seq.split()
                            for end in range(min_moves, len(seq_parts) + 1):
                                prefix = " ".join(seq_parts[:end])
                                cms.update(prefix)
                                prefix_count += 1
                    
                    total_unique_sequences += len(seen_sequences)
                    processed += 1
                    
                    if verbose and processed % 1000 == 0:
                        print(f"\r  已处理: {processed}谱, {joseki_count}定式串, {prefix_count}前缀", 
                              end='', flush=True)
                
                except Exception as e:
                    continue
        
        if verbose:
            print(f"\n✅ Phase 1完成: {processed}谱, {joseki_count}定式串, {prefix_count}前缀")
            print(f"   去重后着法串总数: {total_unique_sequences}")
        
        # ===== Phase 2: 逆向遍历 + 单链检测 + 小顶堆选top-k =====
        if verbose:
            print(f"🔄 Phase 2: 逆向遍历+单链检测，选取top-{top_k}...")
        
        heap = []  # 小顶堆
        seen_hashes = {}  # 记录已处理的hash
        
        def _get_hash(prefix_parts):
            return tuple(prefix_parts)
        
        def _get_child_hash(prefix_parts, seq_parts):
            """获取子串hash（当前前缀+下一手）"""
            if len(prefix_parts) >= len(seq_parts):
                return None
            child_parts = prefix_parts + [seq_parts[len(prefix_parts)]]
            return tuple(child_parts)
        
        SINGLE_CHAIN_THRESHOLD = 0.05  # 单链检测阈值：5%
        
        processed_seq = 0
        prefix_processed = 0
        skipped_single_chain = 0
        
        with gzip.open(temp_path, 'rt', encoding='utf-8') as f_in:
            for line in f_in:
                line = line.strip()
                if not line or '|' not in line:
                    continue
                
                direction, joseki_str = line.split('|', 1)
                seq_parts = joseki_str.split()
                
                if len(seq_parts) < min_moves:
                    continue
                
                # 逆向遍历：从最长前缀到min_moves
                last_count = float('inf')
                
                for end in range(len(seq_parts), min_moves - 1, -1):
                    prefix_parts = seq_parts[:end]
                    prefix = " ".join(prefix_parts)
                    
                    # CMS估算频率
                    est_count = cms.estimate(prefix)
                    
                    # 过滤低频
                    if est_count < min_freq:
                        last_count = est_count
                        continue
                    
                    prefix_hash = _get_hash(prefix_parts)
                    
                    # 单链检测：count和last_count相差<5%，说明是单链，跳过
                    if last_count != float('inf'):
                        count_diff_ratio = abs(est_count - last_count) / max(est_count, last_count, 1)
                        if count_diff_ratio < SINGLE_CHAIN_THRESHOLD:
                            # 子串已处理（last_count来自子串），当前前缀被代表，跳过
                            skipped_single_chain += 1
                            last_count = est_count
                            continue
                    
                    last_count = est_count
                    
                    # 已在堆中或被跳过
                    if prefix_hash in seen_hashes:
                        break
                    
                    # 尝试入堆
                    if len(heap) < top_k:
                        item = HeapItem(est_count, prefix, direction, prefix_hash)
                        heapq.heappush(heap, item)
                        seen_hashes[prefix_hash] = True
                        prefix_processed += 1
                    elif est_count > heap[0].count:
                        old_item = heapq.heapreplace(heap, HeapItem(est_count, prefix, direction, prefix_hash))
                        del seen_hashes[old_item.prefix_hash]
                        seen_hashes[prefix_hash] = True
                        prefix_processed += 1
                
                processed_seq += 1
                if verbose and processed_seq % 10000 == 0:
                    print(f"\r  处理: {processed_seq}定式/{prefix_processed}前缀, "
                          f"堆大小: {len(heap)}, 单链跳过: {skipped_single_chain}", 
                          end='', flush=True)
        
        if verbose:
            print(f"\n  堆中候选: {len(heap)} 个")
            print(f"  单链跳过: {skipped_single_chain} 个")
        
        # ===== Phase 3: 统一转ruld方向去重 =====
        if verbose:
            print("🔄 Phase 3: 统一转ruld方向去重...")
        
        seen_ruld = {}  # ruld_key -> (count, direction)
        
        for item in heap:
            parts = item.prefix.split()
            
            # 统一转换为ruld方向
            if item.direction == 'ruld':
                ruld_parts = parts
            else:
                ruld_parts = convert_to_ruld(parts)
            
            ruld_key = tuple(ruld_parts)
            if ruld_key in seen_ruld:
                # 保留count更大的
                if item.count > seen_ruld[ruld_key][0]:
                    seen_ruld[ruld_key] = (item.count, item.direction)
            else:
                seen_ruld[ruld_key] = (item.count, item.direction)
        
        candidates = []
        for moves_tuple, (count, direction) in seen_ruld.items():
            # 过滤超长定式
            if len(moves_tuple) > max_moves:
                continue
            candidates.append({
                'moves': list(moves_tuple),
                'count': count,
                'direction': direction,
            })
        
        # 按字符串排序
        candidates.sort(key=lambda x: " ".join(x['moves']))
        
        if verbose:
            print(f"  去重后候选: {len(candidates)} 个")
        
        # 清理临时文件
        temp_path.unlink()
        
        # 计算概率（频率 / 总定式串数）
        total_sequences = max(total_unique_sequences, 1)
        
        # ===== Phase 4: 转换为定式格式 =====
        joseki_list = []
        for i, cand in enumerate(candidates):
            joseki = {
                "id": f"kj_{i+1:05d}",
                "source": "katago",
                "moves": cand['moves'],
                "frequency": cand['count'],
                "probability": round(cand['count'] / total_sequences, 6),
                "direction": cand['direction'],
                "created_at": datetime.now().isoformat()
            }
            joseki_list.append(joseki)
        
        if verbose:
            print(f"✅ 构建完成: {len(joseki_list)} 条定式")
        
        return joseki_list
    
    def _process_temp_file(self, temp_path: Path, cms, min_freq: int, top_k: int, min_moves: int, max_moves: int = 50) -> List[dict]:
        """处理临时文件，执行逆向遍历+单链检测+去重"""
        import heapq
        from datetime import datetime
        
        heap = []
        seen_hashes = {}
        
        def _get_hash(prefix_parts):
            return tuple(prefix_parts)
        
        def _get_child_hash(prefix_parts, seq_parts):
            if len(prefix_parts) >= len(seq_parts):
                return None
            child_parts = prefix_parts + [seq_parts[len(prefix_parts)]]
            return tuple(child_parts)
        
        SINGLE_CHAIN_THRESHOLD = 0.05
        
        with gzip.open(temp_path, 'rt', encoding='utf-8') as f_in:
            for line in f_in:
                line = line.strip()
                if not line or '|' not in line:
                    continue
                
                direction, joseki_str = line.split('|', 1)
                seq_parts = joseki_str.split()
                
                if len(seq_parts) < min_moves:
                    continue
                
                last_count = float('inf')
                
                for end in range(len(seq_parts), min_moves - 1, -1):
                    prefix_parts = seq_parts[:end]
                    prefix = " ".join(prefix_parts)
                    
                    est_count = cms.estimate(prefix)
                    
                    if est_count < min_freq:
                        last_count = est_count
                        continue
                    
                    prefix_hash = _get_hash(prefix_parts)
                    
                    if last_count != float('inf'):
                        count_diff_ratio = abs(est_count - last_count) / max(est_count, last_count, 1)
                        if count_diff_ratio < SINGLE_CHAIN_THRESHOLD:
                            # 子串已处理（last_count来自子串），当前前缀被代表，跳过
                            last_count = est_count
                            continue
                    
                    last_count = est_count
                    
                    if prefix_hash in seen_hashes:
                        break
                    
                    if len(heap) < top_k:
                        item = HeapItem(est_count, prefix, direction, prefix_hash)
                        heapq.heappush(heap, item)
                        seen_hashes[prefix_hash] = True
                    elif est_count > heap[0].count:
                        old_item = heapq.heapreplace(heap, HeapItem(est_count, prefix, direction, prefix_hash))
                        del seen_hashes[old_item.prefix_hash]
                        seen_hashes[prefix_hash] = True
        
        # 去重
        seen_ruld = {}
        for item in heap:
            parts = item.prefix.split()
            
            if item.direction == 'ruld':
                ruld_parts = parts
            else:
                ruld_parts = convert_to_ruld(parts)
            
            ruld_key = tuple(ruld_parts)
            if ruld_key in seen_ruld:
                if item.count > seen_ruld[ruld_key][0]:
                    seen_ruld[ruld_key] = (item.count, item.direction)
            else:
                seen_ruld[ruld_key] = (item.count, item.direction)
        
        candidates = []
        for moves_tuple, (count, direction) in seen_ruld.items():
            # 过滤超长定式
            if len(moves_tuple) > max_moves:
                continue
            candidates.append({
                'moves': list(moves_tuple),
                'count': count,
                'direction': direction,
            })
        
        candidates.sort(key=lambda x: " ".join(x['moves']))
        
        # 转换为定式格式（概率暂时为0，需要外部传入total_sequences计算）
        joseki_list = []
        for i, cand in enumerate(candidates):
            joseki = {
                "id": f"kj_{i+1:05d}",
                "source": "katago",
                "moves": cand['moves'],
                "frequency": cand['count'],
                "probability": 0.0,  # 需要外部计算
                "direction": cand['direction'],
                "created_at": datetime.now().isoformat()
            }
            joseki_list.append(joseki)
        
        return joseki_list
    
    def save_to_db(self, joseki_list: List[dict], append: bool = False):
        """批量保存定式列表到数据库（优化版）"""
        if not append:
            self.storage._data["joseki_list"] = []
        
        # 批量添加到内存，最后统一写入
        self.storage._data["joseki_list"].extend(joseki_list)
        self.storage._save()
        
        print(f"已保存 {len(joseki_list)} 条定式到 {self.storage.db_path}")


def build_katago_joseki_db(
    tar_path: str,
    db_path: Optional[str] = None,
    min_freq: int = 5,
    top_k: int = 10000,
    first_n: int = 80,
    distance_threshold: int = 4,
    min_moves: int = 4,
    max_moves: int = 50
) -> int:
    """便捷函数：从KataGo棋谱构建定式库"""
    builder = KatagoJosekiBuilder(db_path)
    
    joseki_list = builder.build_from_tar(
        tar_path=tar_path,
        min_freq=min_freq,
        top_k=top_k,
        first_n=first_n,
        distance_threshold=distance_threshold,
        min_moves=min_moves,
        max_moves=max_moves
    )
    
    builder.save_to_db(joseki_list, append=False)
    return len(joseki_list)
