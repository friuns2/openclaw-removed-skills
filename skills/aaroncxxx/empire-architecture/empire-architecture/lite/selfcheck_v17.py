"""
帝国架构 V1.7 - 并行自检框架
目标：21节点系统自检从 133s → 58s
核心优化：
  1. ThreadPoolExecutor 并行执行（max_workers=6）
  2. 差异化超时（DB 3s / API 2s / Network 5s）
  3. 结果缓存 + 增量检查
"""
import concurrent.futures
import time
import json
import os
import socket
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


class CheckStatus(Enum):
    PASS = "✅ 正常"
    FAIL = "❌ 异常"
    TIMEOUT = "⏱️ 超时"
    SKIP = "⏭️ 跳过"


@dataclass
class CheckResult:
    name: str
    category: str
    status: CheckStatus
    elapsed_ms: float
    detail: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================
# 差异化超时配置
# ============================================================
TIMEOUTS = {
    "database": 3,      # 数据库检查 3s
    "api": 2,           # API 检查 2s
    "network": 5,       # 网络检查 5s
    "certificate": 3,   # 证书检查 3s
    "config": 2,        # 配置检查 2s
    "filesystem": 3,    # 文件系统 3s
}


# ============================================================
# 检查函数（模拟 + 可替换为真实检查）
# ============================================================

def check_database(db_name: str, host: str = "localhost", port: int = 5432) -> CheckResult:
    """数据库连接检查"""
    start = time.time()
    timeout = TIMEOUTS["database"]
    try:
        # 替换为真实数据库连接检查
        # import psycopg2; conn = psycopg2.connect(...)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        elapsed = (time.time() - start) * 1000
        if result == 0:
            return CheckResult(db_name, "database", CheckStatus.PASS, elapsed, f"{host}:{port} 连通")
        else:
            return CheckResult(db_name, "database", CheckStatus.FAIL, elapsed, f"{host}:{port} 不可达")
    except socket.timeout:
        elapsed = (time.time() - start) * 1000
        return CheckResult(db_name, "database", CheckStatus.TIMEOUT, elapsed, f"超过{timeout}s")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(db_name, "database", CheckStatus.FAIL, elapsed, str(e))


def check_api(api_name: str, url: str = "http://localhost:8080/health") -> CheckResult:
    """API 健康检查"""
    start = time.time()
    timeout = TIMEOUTS["api"]
    try:
        import urllib.request
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = (time.time() - start) * 1000
            code = resp.getcode()
            if code == 200:
                return CheckResult(api_name, "api", CheckStatus.PASS, elapsed, f"HTTP {code}")
            else:
                return CheckResult(api_name, "api", CheckStatus.FAIL, elapsed, f"HTTP {code}")
    except urllib.error.URLError as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(api_name, "api", CheckStatus.FAIL, elapsed, str(e.reason))
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(api_name, "api", CheckStatus.FAIL, elapsed, str(e))


def check_network(node_name: str, host: str, port: int = 22) -> CheckResult:
    """网络连通性检查"""
    start = time.time()
    timeout = TIMEOUTS["network"]
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        elapsed = (time.time() - start) * 1000
        if result == 0:
            return CheckResult(node_name, "network", CheckStatus.PASS, elapsed, f"{host}:{port} 连通")
        else:
            return CheckResult(node_name, "network", CheckStatus.FAIL, elapsed, f"{host}:{port} 不可达")
    except socket.timeout:
        elapsed = (time.time() - start) * 1000
        return CheckResult(node_name, "network", CheckStatus.TIMEOUT, elapsed, f"超过{timeout}s")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(node_name, "network", CheckStatus.FAIL, elapsed, str(e))


def check_certificate(cert_name: str, cert_path: str = "/etc/ssl/certs") -> CheckResult:
    """证书有效性检查"""
    start = time.time()
    timeout = TIMEOUTS["certificate"]
    try:
        # 替换为真实证书检查
        # from cryptography import x509; ...
        if os.path.exists(cert_path):
            elapsed = (time.time() - start) * 1000
            return CheckResult(cert_name, "certificate", CheckStatus.PASS, elapsed, f"证书路径存在")
        else:
            elapsed = (time.time() - start) * 1000
            return CheckResult(cert_name, "certificate", CheckStatus.FAIL, elapsed, f"证书路径不存在")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(cert_name, "certificate", CheckStatus.FAIL, elapsed, str(e))


def check_config(config_name: str, config_path: str) -> CheckResult:
    """配置文件检查"""
    start = time.time()
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                json.load(f)
            elapsed = (time.time() - start) * 1000
            return CheckResult(config_name, "config", CheckStatus.PASS, elapsed, "配置有效")
        else:
            elapsed = (time.time() - start) * 1000
            return CheckResult(config_name, "config", CheckStatus.FAIL, elapsed, "文件不存在")
    except json.JSONDecodeError as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(config_name, "config", CheckStatus.FAIL, elapsed, f"JSON错误: {e.msg}")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(config_name, "config", CheckStatus.FAIL, elapsed, str(e))


def check_filesystem(fs_name: str, path: str = "/tmp") -> CheckResult:
    """文件系统检查"""
    start = time.time()
    try:
        stat = os.statvfs(path)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
        usage_pct = (1 - free_gb / total_gb) * 100 if total_gb > 0 else 0
        elapsed = (time.time() - start) * 1000
        if usage_pct > 90:
            return CheckResult(fs_name, "filesystem", CheckStatus.FAIL, elapsed,
                               f"磁盘使用率 {usage_pct:.1f}% (剩余 {free_gb:.1f}GB)")
        elif usage_pct > 75:
            return CheckResult(fs_name, "filesystem", CheckStatus.PASS, elapsed,
                               f"⚠️ 磁盘使用率 {usage_pct:.1f}% (剩余 {free_gb:.1f}GB)")
        else:
            return CheckResult(fs_name, "filesystem", CheckStatus.PASS, elapsed,
                               f"磁盘使用率 {usage_pct:.1f}% (剩余 {free_gb:.1f}GB)")
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return CheckResult(fs_name, "filesystem", CheckStatus.FAIL, elapsed, str(e))


# ============================================================
# 并行自检主类
# ============================================================

class ParallelSelfCheck:
    """
    并行自检框架
    - ThreadPoolExecutor(max_workers=6) 并行执行
    - 差异化超时策略
    - 结果汇总 + 耗时统计
    """

    def __init__(self, max_workers: int = 6):
        self.max_workers = max_workers
        self.results: List[CheckResult] = []
        self._cache: Dict[str, CheckResult] = {}
        self._cache_ttl = 30  # 缓存有效期（秒）

    def _build_checklist(self) -> List[tuple]:
        """
        构建检查清单
        返回 [(func, args), ...] 列表
        根据实际环境替换为真实检查项
        """
        checklist = []

        # === 数据库检查（3s 超时）===
        checklist.append((check_database, ("主数据库", "localhost", 5432)))
        checklist.append((check_database, ("缓存Redis", "localhost", 6379)))
        checklist.append((check_database, ("消息队列", "localhost", 5672)))

        # === API 检查（2s 超时）===
        checklist.append((check_api, ("丞相API", "http://localhost:8080/health")))
        checklist.append((check_api, ("知识库API", "http://localhost:8081/health")))
        checklist.append((check_api, ("安全模块API", "http://localhost:8082/health")))

        # === 网络检查（5s 超时）===
        checklist.append((check_network, ("节点-参谋部", "localhost", 9001)))
        checklist.append((check_network, ("节点-执行部", "localhost", 9002)))
        checklist.append((check_network, ("节点-六部", "localhost", 9003)))
        checklist.append((check_network, ("节点-翰林院", "localhost", 9004)))
        checklist.append((check_network, ("节点-锦衣卫", "localhost", 9005)))

        # === 证书检查（3s 超时）===
        checklist.append((check_certificate, ("TLS证书", "/etc/ssl/certs")))

        # === 配置检查（2s 超时）===
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
        checklist.append((check_config, ("帝国配置", config_path)))

        # === 文件系统检查（3s 超时）===
        checklist.append((check_filesystem, ("根分区", "/")))
        checklist.append((check_filesystem, ("工作目录", os.path.dirname(__file__))))

        return checklist

    def _run_single_check(self, func, args) -> CheckResult:
        """执行单个检查（带缓存）"""
        cache_key = f"{func.__name__}:{args}"

        # 检查缓存
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = time.time() - datetime.fromisoformat(cached.timestamp).timestamp()
            if age < self._cache_ttl:
                return cached

        result = func(*args)
        self._cache[cache_key] = result
        return result

    def run_selfcheck(self) -> Dict[str, Any]:
        """
        执行并行自检
        返回完整检查报告
        """
        start = time.time()
        checklist = self._build_checklist()
        self.results = []

        print(f"⚡ 开始并行自检 ({len(checklist)} 项检查, {self.max_workers} 线程)")
        print("─" * 50)

        # 并行执行所有检查
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_map = {}
            for func, args in checklist:
                future = executor.submit(self._run_single_check, func, args)
                future_map[future] = f"{func.__name__}({args[0]})"

            for future in concurrent.futures.as_completed(future_map):
                name = future_map[future]
                try:
                    result = future.result(timeout=10)  # 兜底超时
                    self.results.append(result)
                    icon = result.status.value
                    print(f"  {icon} {result.name} ({result.elapsed_ms:.0f}ms) - {result.detail}")
                except concurrent.futures.TimeoutError:
                    self.results.append(CheckResult(
                        name, "unknown", CheckStatus.TIMEOUT, 10000, "兜底超时"
                    ))
                    print(f"  ⏱️ {name} - 兜底超时")
                except Exception as e:
                    self.results.append(CheckResult(
                        name, "unknown", CheckStatus.FAIL, 0, str(e)
                    ))
                    print(f"  ❌ {name} - {e}")

        total_elapsed = time.time() - start

        # 汇总
        print("─" * 50)
        report = self._generate_report(total_elapsed)
        return report

    def _generate_report(self, total_elapsed: float) -> Dict[str, Any]:
        """生成检查报告"""
        passed = sum(1 for r in self.results if r.status == CheckStatus.PASS)
        failed = sum(1 for r in self.results if r.status == CheckStatus.FAIL)
        timeout = sum(1 for r in self.results if r.status == CheckStatus.TIMEOUT)
        total = len(self.results)

        # 按类别统计
        by_category = {}
        for r in self.results:
            cat = r.category
            if cat not in by_category:
                by_category[cat] = {"pass": 0, "fail": 0, "timeout": 0, "total": 0, "avg_ms": 0}
            by_category[cat]["total"] += 1
            by_category[cat]["avg_ms"] += r.elapsed_ms
            if r.status == CheckStatus.PASS:
                by_category[cat]["pass"] += 1
            elif r.status == CheckStatus.FAIL:
                by_category[cat]["fail"] += 1
            elif r.status == CheckStatus.TIMEOUT:
                by_category[cat]["timeout"] += 1

        for cat in by_category:
            n = by_category[cat]["total"]
            by_category[cat]["avg_ms"] = round(by_category[cat]["avg_ms"] / n, 1) if n > 0 else 0

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_elapsed_s": round(total_elapsed, 2),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "timeout": timeout,
                "health_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A",
            },
            "by_category": by_category,
            "details": [
                {
                    "name": r.name,
                    "category": r.category,
                    "status": r.status.name,
                    "elapsed_ms": round(r.elapsed_ms, 1),
                    "detail": r.detail,
                }
                for r in sorted(self.results, key=lambda x: x.elapsed_ms, reverse=True)
            ],
        }

        print(f"\n📊 自检完成: {passed}/{total} 通过 | {failed} 异常 | {timeout} 超时")
        print(f"⏱  总耗时: {total_elapsed:.2f}s")
        print(f"🏥 健康率: {report['summary']['health_rate']}")

        return report


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    checker = ParallelSelfCheck(max_workers=6)
    report = checker.run_selfcheck()

    # 输出 JSON 报告
    print("\n" + "=" * 50)
    print("📋 完整报告 (JSON):")
    print(json.dumps(report, ensure_ascii=False, indent=2))
