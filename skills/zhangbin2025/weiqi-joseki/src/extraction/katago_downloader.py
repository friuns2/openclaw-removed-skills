#!/usr/bin/env python3
"""
KataGo 棋谱下载模块
支持断点续传、404检测、内存监控
"""

import gc
import time
import signal
import tarfile
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Iterator, Callable
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed


# KataGo 配置
KATAGO_BASE_URL = "https://katagoarchive.org/kata1/ratinggames/"


class MemoryMonitor:
    """内存监控器"""
    def __init__(self, max_memory_mb: int):
        self.max_memory_mb = max_memory_mb
        self.warning_threshold = max_memory_mb * 0.9
        self.critical_threshold = max_memory_mb
        self._check_import()
    
    def _check_import(self):
        try:
            import psutil
            self.psutil = psutil
            self.has_psutil = True
        except ImportError:
            self.has_psutil = False
    
    def get_memory_mb(self) -> float:
        """获取当前内存使用（MB）"""
        if self.has_psutil:
            process = self.psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        else:
            # 使用简单的对象计数估算
            return 0
    
    def check(self) -> Tuple[str, float]:
        """检查内存状态，返回 (status, memory_mb)
        status: 'ok', 'warning', 'critical'
        """
        mem = self.get_memory_mb()
        if mem >= self.critical_threshold:
            return 'critical', mem
        elif mem >= self.warning_threshold:
            return 'warning', mem
        return 'ok', mem
    
    def force_gc(self):
        """强制垃圾回收"""
        gc.collect()


class ProgressManager:
    """进度管理器（断点续传）"""
    def __init__(self, progress_file: Path):
        self.progress_file = progress_file
        self.data = self._load()
    
    def _load(self) -> dict:
        import json
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"ProgressManager load error: {e}")
                pass
        return {
            'completed_dates': [],
            'count_map': {},
            'total_sgfs': 0,
            'start_time': None
        }
    
    def save(self):
        """保存进度"""
        import json
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def is_completed(self, date_str: str) -> bool:
        return date_str in self.data.get('completed_dates', [])
    
    def mark_completed(self, date_str: str, stats: dict):
        if date_str not in self.data.get('completed_dates', []):
            self.data.setdefault('completed_dates', []).append(date_str)
        # 更新统计
        self.data['total_sgfs'] = self.data.get('total_sgfs', 0) + stats.get('sgf_count', 0)
        self.save()
    
    def update_count_map(self, count_map: dict):
        """更新计数映射"""
        for k, v in count_map.items():
            self.data.setdefault('count_map', {})[k] = self.data.get('count_map', {}).get(k, 0) + v
    
    def get_count_map(self) -> dict:
        return self.data.get('count_map', {})
    
    def clear(self):
        """清除进度"""
        if self.progress_file.exists():
            self.progress_file.unlink()
        self.data = {
            'completed_dates': [],
            'count_map': {},
            'total_sgfs': 0,
            'start_time': None
        }


class DownloadManager:
    """下载管理器（支持重试、进度显示、404检测）"""
    def __init__(self, cache_dir: Path, max_retries: int = 3, workers: int = 3, keep_cache: bool = True):
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.workers = workers
        self.keep_cache = keep_cache
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._completed = 0
        self._total = 0
        self._current_file = ""
        self._start_time = time.time()
    
    def set_keep_cache(self, keep: bool):
        """设置是否保留缓存"""
        self.keep_cache = keep
    
    def stop(self):
        self._stop_event.set()
    
    def is_stopped(self) -> bool:
        return self._stop_event.is_set()
    
    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f}{unit}"
            size /= 1024
        return f"{size:.1f}TB"
    
    def _format_time(self, seconds: float) -> str:
        """格式化时间"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m{int(seconds%60)}s"
        else:
            return f"{int(seconds/3600)}h{int((seconds%3600)/60)}m"
    
    def check_file_exists(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        检查远程文件是否存在
        
        返回:
            (exists, error)
            exists: True表示存在，False表示404或其他错误
        """
        try:
            req = urllib.request.Request(url, method='HEAD', headers={
                'User-Agent': 'Mozilla/5.0 (compatible; WeiqiJoseki/1.0)'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                return True, None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return False, None  # 文件不存在，不算错误
            return False, str(e)
        except Exception as e:
            return False, str(e)
    
    def download_single(self, date_str: str) -> Tuple[str, Optional[Path], Optional[str]]:
        """
        下载单个日期文件
        
        返回:
            (date_str, file_path, error)
            error为None表示成功，为"404"表示文件不存在（也算成功但不下载），其他为错误信息
        """
        url = f"{KATAGO_BASE_URL}{date_str}rating.tar.bz2"
        output_path = self.cache_dir / f"{date_str}rating.tar.bz2"
        
        # 如果文件已存在且有效，跳过
        if output_path.exists() and output_path.stat().st_size > 1000:
            with self._lock:
                self._completed += 1
            return date_str, output_path, None
        
        # 先检查文件是否存在
        exists, error = self.check_file_exists(url)
        if not exists:
            if error is None:
                # 404，文件不存在，算成功但不下载
                return date_str, None, "404"
            else:
                return date_str, None, error
        
        # 文件存在，执行下载
        for attempt in range(self.max_retries):
            if self._stop_event.is_set():
                return date_str, None, "stopped"
            
            try:
                self._current_file = f"{date_str}.tar.bz2"
                # 下载
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; WeiqiJoseki/1.0)'
                })
                
                with urllib.request.urlopen(req, timeout=60) as response:
                    with open(output_path, 'wb') as f:
                        while True:
                            if self._stop_event.is_set():
                                return date_str, None, "stopped"
                            chunk = response.read(8192)
                            if not chunk:
                                break
                            f.write(chunk)
                
                with self._lock:
                    self._completed += 1
                # 下载成功后延迟，避免触发服务器频率限制
                time.sleep(10)
                return date_str, output_path, None
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    with self._lock:
                        self._completed += 1
                    return date_str, None, str(e)
        
        return date_str, None, "max retries exceeded"
    
    def download(self, dates: List[str], on_progress: Optional[Callable[[str, int, int], None]] = None) -> Dict[str, Path]:
        """
        批量下载，返回成功下载的文件映射
        
        Args:
            dates: 日期列表
            on_progress: 进度回调函数(date_str, current, total)
        
        返回:
            {date_str: file_path, ...}
        """
        self._total = len(dates)
        self._completed = 0
        self._start_time = time.time()
        
        results = {}
        completed_count = 0
        
        def download_single_wrapped(date_str: str) -> Tuple[str, Optional[Path], Optional[str]]:
            return self.download_single(date_str)
        
        # 使用线程池并行下载
        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {executor.submit(download_single_wrapped, d): d for d in dates}
            
            for future in as_completed(futures):
                if self._stop_event.is_set():
                    break
                date_str, path, error = future.result()
                completed_count += 1
                if on_progress:
                    on_progress(date_str, completed_count, self._total)
                if path:
                    results[date_str] = path
        
        return results
    
    def print_progress(self):
        """打印当前进度"""
        elapsed = time.time() - self._start_time
        if self._completed > 0:
            avg_time = elapsed / self._completed
            remaining = (self._total - self._completed) * avg_time
        else:
            remaining = 0
        
        percent = (self._completed / self._total * 100) if self._total > 0 else 0
        
        print(f"\r📥 下载进度: {self._completed}/{self._total} ({percent:.1f}%) "
              f"| 当前: {self._current_file:<20} "
              f"| 剩余时间: {self._format_time(remaining)}", end='', flush=True)


def iter_sgf_from_tar(tar_path: Path) -> Iterator[str]:
    """
    从tar.bz2文件中迭代读取SGF内容
    
    Yields:
        SGF字符串
    """
    tar_path = Path(tar_path) if isinstance(tar_path, str) else tar_path
    if not tar_path.exists():
        return
    
    try:
        with tarfile.open(tar_path, 'r:bz2') as tar:
            for member in tar.getmembers():
                if not member.isfile() or not member.name.endswith('.sgf'):
                    continue
                
                try:
                    f = tar.extractfile(member)
                    if f is None:
                        continue
                    
                    sgf_data = f.read().decode('utf-8', errors='ignore')
                    yield sgf_data
                except:
                    continue
    except Exception:
        return


def download_katago_games(
    start_date: str,
    end_date: str,
    cache_dir: Optional[Path] = None,
    max_retries: int = 3,
    workers: int = 3,
    keep_cache: bool = True,
    resume: bool = False,
    on_progress: Optional[Callable[[str, int, int], None]] = None
) -> Tuple[List[Path], List[str]]:
    """
    下载KataGo棋谱文件
    
    Args:
        start_date: 起始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
        cache_dir: 缓存目录，默认 ~/.weiqi-joseki/katago-cache
        max_retries: 最大重试次数
        workers: 并行下载线程数
        keep_cache: 是否保留缓存文件
        resume: 是否断点续传
        on_progress: 进度回调函数(date_str, current, total)
    
    返回:
        (downloaded_files, missing_dates)
        downloaded_files: 成功下载的文件路径列表
        missing_dates: 文件不存在的日期列表（404）
    """
    from pathlib import Path
    
    # 解析日期
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # 生成日期列表
    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)
    
    # 设置默认缓存目录
    if cache_dir is None:
        cache_dir = Path.home() / ".weiqi-joseki" / "katago-cache"
    
    # 创建下载管理器
    manager = DownloadManager(
        cache_dir=cache_dir,
        max_retries=max_retries,
        workers=workers,
        keep_cache=keep_cache
    )
    
    # 断点续传：加载进度文件
    progress_file = cache_dir.parent / "katago-progress.json"
    if resume and progress_file.exists():
        import json
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            completed = progress_data.get('completed_dates', [])
            dates = [d for d in dates if d not in completed]
        except:
            pass
    
    # 下载
    downloaded_map = manager.download(dates, on_progress=on_progress)
    
    # 分类结果
    downloaded_files = list(downloaded_map.values())
    missing_dates = [d for d in dates if d not in downloaded_map]
    
    return downloaded_files, missing_dates
