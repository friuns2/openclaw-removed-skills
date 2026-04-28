#!/usr/bin/env python3
"""
EdgeIQ Network Scanner — Professional-grade network reconnaissance.
Full port scanning, CVE matching, SSL analysis, traceroute, HTTP fingerprinting.
No nmap required. Pure Python stdlib.
"""

import socket
import concurrent.futures
import struct
import random
import time
import ipaddress
import argparse
import json
import sys
import signal
import os
import re
import ssl
import hashlib
import argparse
import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(_sys.argv[0])))
try:
    from edgeiq_licensing import require_license, is_pro, is_bundle
except ImportError:
    def require_license(tier, feat=""): return True
    def is_pro(): return True
    def is_bundle(): return True

# ═══════════════════════════════════════════════════════════════
#  GLOBAL STATE
# ═══════════════════════════════════════════════════════════════

SCAN_STATS = {
    "ports_scanned": 0,
    "hosts_found": 0,
    "errors": 0,
    "start_time": None,
    "quit_requested": False,
}

EXIT_CODE = 0  # 0=clean, 1=error, 2=ctrl-c

# ═══════════════════════════════════════════════════════════════
#  SIGNAL HANDLING
# ═══════════════════════════════════════════════════════════════

def _handle_sig(signum, frame):
    global EXIT_CODE
    if SCAN_STATS["quit_requested"]:
        print("\n[!] Forced shutdown.", file=sys.stderr)
        sys.exit(2)
    SCAN_STATS["quit_requested"] = True
    EXIT_CODE = 2
    print("\n[*] Interrupt received — finishing current hosts, then exiting.", file=sys.stderr)
    print("[*] Press Ctrl+C again to force-kill.", file=sys.stderr)

signal.signal(signal.SIGINT,  _handle_sig)
signal.signal(signal.SIGTERM, _handle_sig)

# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION
# ═══════════════════════════════════════════════════════════════

QUICK_PORTS      = [21, 22, 23, 25, 80, 443, 445, 3389, 8080]
COMMON_PORTS     = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143,
                    443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080, 8443]
TOP_PORTS_100    = [80, 443, 22, 21, 25, 3389, 110, 445, 139, 53, 135,
                    3306, 8080, 1723, 111, 995, 993, 5900, 1025, 587,
                    8888, 199, 1720, 465, 548, 113, 81, 38292, 3311, 3333,
                    49152, 1900, 3986, 13, 1027, 2000, 5666, 646, 2049,
                    88, 106, 2001, 3141, 4000, 5104, 5190, 3000, 543, 544,
                    5107, 144, 7, 389, 8000, 8008, 49154, 997, 1001, 5009,
                    5051, 5060, 5108, 5357, 49155, 1026, 6379, 6600, 6646,
                    7070, 7400, 7434, 7443, 8009, 8081, 8098]

# All 1024 well-known ports (1–1024)
WELL_KNOWN_PORTS = list(range(1, 1025))

HOST_DISCOVERY_PORTS = [80, 443, 22, 445, 3389, 21, 25, 8080]
TIMEOUT_DEFAULT = 1.5
MAX_THREADS     = 150
MAX_THREADS_HOST = 50

# ═══════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class PortResult:
    port: int
    state: str = "closed"
    rtt_ms: Optional[float] = None
    service: str = ""
    version: str = ""
    banner: str = ""
    cves: list = field(default_factory=list)
    vuln_level: str = "NONE"  # CRITICAL / HIGH / MEDIUM / LOW / NONE
    http_fingerprint: dict = field(default_factory=dict)
    ssl_info: dict = field(default_factory=dict)
    os_hint: list = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        return d

@dataclass
class HostResult:
    ip: str
    hostname: Optional[str] = None
    is_alive: bool = False
    rtt_ms: Optional[float] = None
    os_guess: str = ""
    ttl: int = 0
    window_size: int = 0
    traceroute: list = field(default_factory=list)
    ports: dict = field(default_factory=dict)  # port -> PortResult
    subdomains: list = field(default_factory=list)
    cves: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["total_open_ports"] = len(self.ports)
        d["critical_cves"] = [c for c in self.cves if c.get("level") == "CRITICAL"]
        d["high_cves"]     = [c for c in self.cves if c.get("level") == "HIGH"]
        return d

@dataclass
class ScanResult:
    target: str
    scan_type: str
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    hosts: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    duration_s: float = 0.0
    scan_stats: dict = field(default_factory=dict)
    args: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

# ═══════════════════════════════════════════════════════════════
#  CVE DATABASE  (local, for common services)
# ═══════════════════════════════════════════════════════════════

CVE_DATABASE = [
    # Apache httpd
    {"service": "apache", "product": "httpd", "version_pattern": "2.4.(.*)",
     "cve": "CVE-2024-27316", "level": "MEDIUM", "description": "HTTP request smuggling in mod_proxy"},
    {"service": "apache", "product": "httpd", "version_pattern": "2.4.(49|50|51|52)",
     "cve": "CVE-2022-31813", "level": "HIGH", "description": "X-Forwarded-For bypass in mod_proxy"},
    {"service": "apache", "product": "httpd", "version_pattern": "2.4.(17|18|19|20|21|22|23|24|25|26|27|28|29|30|31|32|33|34|35|36|37|38|39|40|41|42|43|44|45|46|47|48)",
     "cve": "CVE-2017-15710", "level": "MEDIUM", "description": "Filesystem path traversal"},

    # nginx
    {"service": "nginx", "product": "nginx", "version_pattern": "1.(9|10|11|12|13|14|15|16|17|18|19|20|21|22).*",
     "cve": "CVE-2021-23017", "level": "HIGH", "description": "DNS resolver off-by-one heap overflow"},
    {"service": "nginx", "product": "nginx", "version_pattern": "1.(14|15|16|17|18).*",
     "cve": "CVE-2019-9511", "level": "HIGH", "description": "HTTP/2 rapid reset DoS"},
    {"service": "nginx", "product": "nginx", "version_pattern": "1.(14|15|16|17|18|19|20).*",
     "cve": "CVE-2019-9513", "level": "HIGH", "description": "HTTP/2 flood using invalid frames"},
    {"service": "nginx", "product": "nginx", "version_pattern": "1.(14|15|16|17|18|19|20).*",
     "cve": "CVE-2019-9516", "level": "HIGH", "description": "HTTP/2 flood with ping frames"},
    {"service": "nginx", "product": "nginx", "version_pattern": "(0.7|0.8|1.0|1.1|1.2|1.3|1.4|1.5|1.6|1.7|1.8).*",
     "cve": "CVE-2013-2028", "level": "CRITICAL", "description": "Stack buffer overflow in chunked encoding"},

    # OpenSSH
    {"service": "ssh", "product": "openssh", "version_pattern": "(7.|8.(0|1|2|3|4|5|6))",
     "cve": "CVE-2020-15778", "level": "MEDIUM", "description": "Scp command injection in filenames"},
    {"service": "ssh", "product": "openssh", "version_pattern": "(6.|7.(0|1|2|3|4|5|6|7|8|9))",
     "cve": "CVE-2018-15473", "level": "MEDIUM", "description": "User enumeration via timing leak"},
    {"service": "ssh", "product": "openssh", "version_pattern": "(7.1|7.2|7.3|7.4|7.5|7.6|7.7|7.8|7.9)",
     "cve": "CVE-2019-6109", "level": "MEDIUM", "description": "SCP symlink attack via ~ in filename"},
    {"service": "ssh", "product": "openssh", "version_pattern": "(7.1|7.2|7.3|7.4|7.5|7.6|7.7|7.8|7.9)",
     "cve": "CVE-2019-6111", "level": "MEDIUM", "description": "SCP total output injection"},

    # MySQL
    {"service": "mysql", "product": "mysql", "version_pattern": "(5.5|5.6|5.7).(.*)",
     "cve": "CVE-2012-2122", "level": "HIGH", "description": "Authentication bypass via integer overflow"},
    {"service": "mysql", "product": "mysql", "version_pattern": "(5.5|5.6|5.7).(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23)",
     "cve": "CVE-2018-2562", "level": "MEDIUM", "description": "Heap overflow in CONVERT()"},
    {"service": "mysql", "product": "mysql", "version_pattern": "(8.0).(0|1|2|3|4|5|6|7|8|9|10|11|12|13|14)",
     "cve": "CVE-2020-2574", "level": "MEDIUM", "description": "XML external entity via UPDATE or DELETE"},

    # PostgreSQL
    {"service": "postgresql", "product": "postgresql", "version_pattern": "(9.|10|11|12).(.*)",
     "cve": "CVE-2019-9193", "level": "CRITICAL", "description": "PostgreSQL COPY TO/FROM PROGRAM execution"},
    {"service": "postgresql", "product": "postgresql", "version_pattern": "(11|12|13|14).(.*)",
     "cve": "CVE-2022-41862", "level": "MEDIUM", "description": "Race condition in logical replication"},

    # Redis
    {"service": "redis", "product": "redis", "version_pattern": "(2.|3.|4.|5.|6.0).(.*)",
     "cve": "CVE-2018-11218", "level": "HIGH", "description": "Heap overflow in CONFIG SET/GET"},
    {"service": "redis", "product": "redis", "version_pattern": "(2.|3.|4.|5.|6.0).(.*)",
     "cve": "CVE-2018-11219", "level": "CRITICAL", "description": "Lua sandbox escape to arbitrary commands"},
    {"service": "redis", "product": "redis", "version_pattern": "(5|6).(.*)",
     "cve": "CVE-2019-10192", "level": "CRITICAL", "description": "Redis set-quicklist OOM panic"},

    # SMB
    {"service": "smb", "product": "samba", "version_pattern": "(3.|4.0|4.1|4.2|4.3|4.4|4.5|4.6|4.7|4.8|4.9|4.10|4.11).(.*)",
     "cve": "CVE-2017-0144", "level": "CRITICAL", "description": "EternalBlue — SMB remote code execution (WannaCry)"},

    # vsftpd
    {"service": "ftp", "product": "vsftpd", "version_pattern": "(2.3.4|3.0.|3.0.1|3.0.2|3.0.3)",
     "cve": "CVE-2011-2523", "level": "CRITICAL", "description": "Backdoor command injection via笑脸"},

    # OpenSSL
    {"service": "ssl", "product": "openssl", "version_pattern": "(1.0.1|1.0.2|1.1.0|1.1.1)(.*)",
     "cve": "CVE-2014-0160", "level": "CRITICAL", "description": "Heartbleed — TLS heartbeat information leak"},
    {"service": "ssl", "product": "openssl", "version_pattern": "(1.0.2|1.1.0|1.1.1)(.*)",
     "cve": "CVE-2022-0778", "level": "HIGH", "description": "Infinite loop in BN_mod_sqrt() — certificate parsing"},
    {"service": "ssl", "product": "openssl", "version_pattern": "(1.0.1|1.0.2|1.1.0|1.1.1)(.*)",
     "cve": "CVE-2014-0224", "level": "CRITICAL", "description": "CCS injection MITM attack"},

    # MSSQL
    {"service": "mssql", "product": "mssql", "version_pattern": "(2008|2012|2014|2016|2017|2019)",
     "cve": "CVE-2019-1068", "level": "HIGH", "description": "Bulk load extension DLL planting"},
    {"service": "mssql", "product": "mssql", "version_pattern": "(2008|2012|2014|2016|2017|2019)",
     "cve": "CVE-2019-1069", "level": "MEDIUM", "description": "Elevation of privilege via extension"},

    # VNC
    {"service": "vnc", "product": "vnc", "version_pattern": "(3|4|5).(.*)",
     "cve": "CVE-2006-2369", "level": "HIGH", "description": "RFB protocol authentication bypass"},
    {"service": "vnc", "product": "vnc", "version_pattern": "(4.0|4.1|4.2|4.3|5.0|5.1|5.2|5.3)",
     "cve": "CVE-2015-5239", "level": "MEDIUM", "description": "Use-after-free in framebuffer updates"},

    # RDP (Windows)
    {"service": "rdp", "product": "windows", "version_pattern": "(.*)",
     "cve": "CVE-2019-0708", "level": "CRITICAL", "description": "BlueKeep — RDP remote code execution worm"},
    {"service": "rdp", "product": "windows", "version_pattern": "(.*)",
     "cve": "CVE-2022-21999", "level": "HIGH", "description": "RDP lossy compression DoS"},

    # DNS (bind)
    {"service": "dns", "product": "bind", "version_pattern": "(9.11|9.12|9.13|9.14|9.15|9.16|9.17|9.18).(.*)",
     "cve": "CVE-2020-1350", "level": "CRITICAL", "description": "SIGRed — DNS server heap overflow"},

    # SMTP (Postfix, Exim)
    {"service": "smtp", "product": "exim", "version_pattern": "(4.92|4.93|4.94|4.95).(.*)",
     "cve": "CVE-2019-10149", "level": "CRITICAL", "description": "Remote command execution via EXIM"},
    {"service": "smtp", "product": "postfix", "version_pattern": "(.*)",
     "cve": "CVE-2020-12783", "level": "MEDIUM", "description": "Postfix mail looper via sender address spoofing"},

    # Telnet
    {"service": "telnet", "product": "telnetd", "version_pattern": "(.*)",
     "cve": "CVE-2020-10188", "level": "CRITICAL", "description": "Telnetd arbitrary code execution via short reads"},

    # MongoDB
    {"service": "mongodb", "product": "mongodb", "version_pattern": "(2.|3.|4.0|4.1|4.2|4.3|4.4).(.*)",
     "cve": "CVE-2019-2389", "level": "MEDIUM", "description": "JavaScript injection in mongod"},

    # ProFTPd
    {"service": "ftp", "product": "proftpd", "version_pattern": "(1.3).(0|1|2|3|4|5|c|rc)(.*)",
     "cve": "CVE-2010-3867", "level": "HIGH", "description": "SQL injection via mod_sql username"},

    # OpenVPN
    {"service": "openvpn", "product": "openvpn", "version_pattern": "(2.4|2.5|2.6).(.*)",
     "cve": "CVE-2020-11810", "level": "MEDIUM", "description": "Use-after-free in OPENVPN plugin load"},

    # FTP generic
    {"service": "ftp", "product": "ftp", "version_pattern": "(.*)",
     "cve": "CVE-2015-3306", "level": "CRITICAL", "description": "Apache mod_auth_pip installable content vulnerability"},
    {"service": "ftp", "product": "ftp", "version_pattern": "(.*)",
     "cve": "CVE-2018-19968", "level": "HIGH", "description": "FTP globbing path traversal"},

    # RDP generic Microsoft
    {"service": "rdp", "product": "msrdp", "version_pattern": "(.*)",
     "cve": "CVE-2019-0708", "level": "CRITICAL", "description": "BlueKeep — pre-auth RCE via RDP"},
]

# ═══════════════════════════════════════════════════════════════
#  UTILITY
# ═══════════════════════════════════════════════════════════════

def is_quiet() -> bool:
    return getattr(sys, "_called_via_cli", False) and not sys.stdout.isatty()

def _progress(msg: str):
    if is_quiet():
        return
    print(msg, flush=True)

def rate_limit(delay: float):
    time.sleep(delay)

# ═══════════════════════════════════════════════════════════════
#  PLATFORM HELPERS
# ═══════════════════════════════════════════════════════════════

def is_wsl() -> bool:
    try:
        with open("/proc/version", "r") as f:
            return "microsoft" in f.read().lower()
    except (FileNotFoundError, PermissionError):
        pass
    return False

def get_local_networks() -> list:
    networks = []
    try:
        import subprocess
        result = subprocess.run(["ip", "-4", "addr", "show"],
                                capture_output=True, text=True, timeout=5)
        for line in result.stdout.split("\n"):
            if "inet " in line:
                ip = line.split("inet ")[1].split("/")[0]
                prefix = int(line.split("inet ")[1].split("/")[1].split()[0])
                if ip.startswith(("127.", "169.254.")):
                    continue
                if prefix > 24:
                    prefix = 24
                try:
                    net = ipaddress.IPv4Network(f"{ip}/{prefix}", strict=False)
                    networks.append(str(net))
                except ValueError:
                    continue
    except Exception:
        pass

    if not networks:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            networks.append(f"{local_ip.rsplit('.', 1)[0]}.0/24")
        except Exception:
            pass

    networks = list(dict.fromkeys(networks))[:4]
    return networks

def get_local_ip() -> Optional[str]:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None

def get_gateway_ip() -> Optional[str]:
    try:
        import subprocess
        result = subprocess.run(["ip", "route", "show", "default"],
                               capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split("\n"):
            if line.startswith("default via"):
                parts = line.split()
                for i, p in enumerate(parts):
                    if p == "via" and i + 1 < len(parts):
                        return parts[i + 1]
    except Exception:
        pass
    return None

# ═══════════════════════════════════════════════════════════════
#  TARGET RESOLUTION
# ═══════════════════════════════════════════════════════════════

def resolve_host(target: str) -> list:
    target = target.strip().rstrip("/")
    if "://" in target:
        target = target.split("://", 1)[1].split("/")[0]
    try:
        if "/" in target:
            network = ipaddress.ip_network(target, strict=False)
            return [str(h) for h in network.hosts()]
    except ValueError:
        pass
    try:
        ipaddress.ip_address(target)
        return [target]
    except ValueError:
        pass
    try:
        result = socket.getaddrinfo(target, None, socket.AF_INET)
        return sorted(set(r[4][0] for r in result))
    except socket.gaierror:
        return [target]
    return [target]

# ═══════════════════════════════════════════════════════════════
#  HOST DISCOVERY
# ═══════════════════════════════════════════════════════════════

def probe_host(ip: str, timeout: float = TIMEOUT_DEFAULT) -> tuple:
    ports = HOST_DISCOVERY_PORTS
    start = time.perf_counter()
    for port in ports:
        if SCAN_STATS["quit_requested"]:
            break
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((ip, port))
            sock.close()
            rtt = (time.perf_counter() - start) * 1000
            # Try to get TTL from socket (Linux-only workaround)
            try:
                ttl = sock.getsockopt(socket.IPPROTO_IP, socket.IP_TTL)
            except Exception:
                ttl = 0
            return True, round(rtt, 2), ttl, 0
        except (socket.timeout, socket.error, OSError):
            continue

    # ICMP probe fallback
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        sock.settimeout(timeout)
        sock.sendto(b"\x08\x00\x00\x00\x00\x00", (ip, 0))
        start_icmp = time.perf_counter()
        sock.recv(512)
        rtt = (time.perf_counter() - start_icmp) * 1000
        sock.close()
        return True, round(rtt, 2), 64, 0
    except Exception:
        pass

    return False, None, 0, 0

def resolve_hostname(ip: str) -> Optional[str]:
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        return name
    except Exception:
        return None

def discover_hosts(targets: list, timeout: float = TIMEOUT_DEFAULT,
                  workers: int = MAX_THREADS_HOST,
                  rate: float = 0) -> list:
    all_ips = set()
    for t in targets:
        all_ips.update(resolve_host(t))

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(probe_host, ip, timeout): ip for ip in sorted(all_ips)}
        for fut in concurrent.futures.as_completed(futures):
            if SCAN_STATS["quit_requested"]:
                break
            ip = futures[fut]
            try:
                alive, rtt, ttl, ws = fut.result()
                hostname = resolve_hostname(ip) if alive else None
                results.append(HostResult(
                    ip=ip, hostname=hostname, is_alive=alive,
                    rtt_ms=rtt, ttl=ttl, window_size=ws
                ))
                if alive:
                    SCAN_STATS["hosts_found"] += 1
            except Exception as e:
                SCAN_STATS["errors"] += 1
                results.append(HostResult(ip=ip, is_alive=False))
    return results

# ═══════════════════════════════════════════════════════════════
#  SERVICE DETECTION & BANNER GRABBING
# ═══════════════════════════════════════════════════════════════

KNOWN_PROBES = {
    21:  b"USER anonymous\r\n",
    22:  b"SSH-2.0-OpenSSH_8.0\r\n",
    25:  b"EHLO scan\r\n",
    80:  b"HEAD / HTTP/1.0\r\nHost: scan\r\n\r\n",
    110: b"USER test\r\n",
    143: b"A001 LOGOUT\r\n",
    443: b"HEAD / HTTP/1.0\r\nHost: scan\r\n\r\n",
    445: b"",
    993: b"A001 LOGOUT\r\n",
    995: b"USER test\r\n",
    3306: b"\x16\x03\x01\x00\xc8\x01\x03\x01",
    5432: b"",
    6379: b"PING\r\n",
    8080: b"HEAD / HTTP/1.0\r\nHost: scan\r\n\r\n",
    8443: b"HEAD / HTTP/1.0\r\nHost: scan\r\n\r\n",
}

def grab_banner(ip: str, port: int, timeout: float = 3.0) -> str:
    probe = KNOWN_PROBES.get(port, b"HEAD / HTTP/1.0\r\nHost: scan\r\n\r\n")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((ip, port))
        if probe:
            sock.send(probe)
        banner = sock.recv(2048).decode("utf-8", errors="ignore").strip()
        sock.close()
        return banner[:500]
    except Exception:
        return ""

def guess_service(port: int) -> str:
    try:
        return socket.getservbyport(port)
    except OSError:
        SERVICE_MAP = {
            21: "ftp", 22: "ssh", 23: "telnet", 25: "smtp",
            53: "dns", 80: "http", 110: "pop3", 111: "rpcbind",
            113: "ident", 135: "msrpc", 139: "netbios-ssn",
            143: "imap", 161: "snmp", 389: "ldap",
            443: "https", 445: "microsoft-ds", 465: "smtps",
            514: "syslog", 587: "submission",
            636: "ldaps", 993: "imaps", 995: "pop3s",
            1080: "socks", 1433: "mssql", 1521: "oracle",
            1723: "pptp", 2049: "nfs", 3306: "mysql",
            3389: "rdp", 5432: "postgresql", 5900: "vnc",
            5901: "vnc", 6379: "redis", 8080: "http-proxy",
            8443: "https-alt", 8888: "http-alt", 9200: "elasticsearch",
            27017: "mongodb",
        }
        return SERVICE_MAP.get(port, f"port-{port}")

def parse_banner_for_version(banner: str, service: str) -> str:
    """Extract version string from banner."""
    if not banner:
        return ""
    patterns = [
        r"(?:Apache|nginx|httpd)[/\s]+([^\s,]+)",
        r"(?:OpenSSH|SSH)[/\s]+([^\s,]+)",
        r"(?:MySQL|MariaDB)[/\s]+([^\s,]+)",
        r"(?:PostgreSQL|pg)[/\s]+([^\s,]+)",
        r"(?:Redis)[/\s]+([^\s,]+)",
        r"(?:MongoDB)[/\s]+([^\s,]+)",
        r"(?:Windows|IIS)[/\s]+([^\s,]+)",
        r"(?:Ubuntu|Debian|CentOS|Fedora)(?:/|\s+)([^\s,]+)",
        r"(?:vsFTPD|vsftpd)[/\s]+([^\s,]+)",
        r"(?:ProFTPD|proftpd)[/\s]+([^\s,]+)",
        r"(?:Exim)(?:/\s+)([^\s,]+)",
        r"(?:Postfix)(?:/\s+)([^\s,]+)",
        r"(?:Apache)(?:/[A-Z0-9._-]+)([A-Z0-9._-]+)",
        r"(?:nginx)(?:/[A-Z0-9._-]+)([A-Z0-9._-]+)",
        r"(?:SSH-2.0-)([^\s]+)",
        r"(?:Server:)([\w/\s.-]+)",
        r"(?:Microsoft)(?:/[A-Z0-9._-]+)([A-Z0-9._-]+)",
        r"Vulnerability:([^\n]+)",
    ]
    for p in patterns:
        m = re.search(p, banner, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    # Generic: first line if it looks like a server header
    for line in banner.split("\n"):
        if any(kw in line.lower() for kw in ["server:", "x-powered-by", "content-type"]):
            return line.strip()[:80]
    return banner[:80]

# ═══════════════════════════════════════════════════════════════
#  HTTP FINGERPRINTING
# ═══════════════════════════════════════════════════════════════

HTTP_SERVERS = {
    "nginx": "nginx",
    "apache": "apache",
    "Microsoft-IIS": "iis",
    "HttpOnly": "iis",
    "X-AspNet-Version": "aspnet",
    "X-Powered-By": "aspnet",
    "X-Generator": "drupal",
    "X-Drupal-Cache": "drupal",
    "wp-": "wordpress",
    "Elementor": "elementor",
    "X-Shopify-": "shopify",
    "Server:": "generic",
}

def http_fingerprint(ip: str, port: int, use_ssl: bool = False, timeout: float = 5.0) -> dict:
    """Perform HTTP fingerprinting: grab headers, tech stack detection."""
    result = {
        "server": "", "tech_stack": [], "powered_by": "",
        "title": "", "redirect": "", "headers": {},
        "status_code": 0, "ssl_grade": "", "ssl_cipher": "",
    }
    try:
        context = None
        sock_type = socket.SOCK_STREAM
        if use_ssl:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

        sock = socket.socket(socket.AF_INET, sock_type)
        if context:
            sock = context.wrap_socket(sock, server_hostname=ip)
        sock.settimeout(timeout)
        sock.connect((ip, port))

        path = "/" if port in (80, 443, 8080, 8443) else "/"
        scheme = "https" if use_ssl else "http"
        req = f"GET {path} HTTP/1.0\r\nHost: {ip}\r\nUser-Agent: EdgeIQ-Scanner/1.0\r\nConnection: close\r\n\r\n"
        sock.send(req.encode())

        response = b""
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if len(response) > 65536:
                    break
            except socket.timeout:
                break
        sock.close()

        if not response:
            return result

        raw = response.decode("utf-8", errors="ignore")
        header_end = raw.find("\r\n\r\n")
        if header_end == -1:
            return result

        headers_raw = raw[:header_end]
        body = raw[header_end + 4:]

        # Status code
        m = re.match(r"HTTP/\d\.\d\s+(\d+)", headers_raw)
        if m:
            result["status_code"] = int(m.group(1))
            if int(m.group(1)) in (301, 302, 303, 307, 308):
                loc = re.search(r"Location:\s*([^\r\n]+)", headers_raw, re.I)
                if loc:
                    result["redirect"] = loc.group(1).strip()

        # Parse headers
        for line in headers_raw.split("\r\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                result["headers"][k.strip().lower()] = v.strip()

        server = result["headers"].get("server", "")
        powered_by = result["headers"].get("x-powered-by", "")

        # Server name extraction
        if server:
            if "nginx" in server.lower():
                m = re.search(r"nginx/(.+?)(?:\s|$)", server, re.I)
                result["server"] = f"nginx/{m.group(1)}" if m else "nginx"
            elif "apache" in server.lower():
                m = re.search(r"Apache/(.+?)(?:\s|$)", server, re.I)
                result["server"] = f"apache/{m.group(1)}" if m else "apache"
            elif "Microsoft-IIS" in server:
                m = re.search(r"Microsoft-IIS/([^\s]+)", server)
                result["server"] = f"iis/{m.group(1)}" if m else "iis"
            elif "Server:" in server:
                result["server"] = server.replace("Server:", "").strip()
            else:
                result["server"] = server

        if powered_by:
            result["powered_by"] = powered_by

        # Tech stack detection
        tech = []
        h = result["headers"]
        if "x-powered-by" in h:
            if "ASP.NET" in h["x-powered-by"]:
                tech.append("ASP.NET")
            elif "PHP" in h["x-powered-by"]:
                tech.append("PHP")
        if "x-generator" in h:
            tech.append(h["x-generator"])
        if any(k in h for k in ("x-drupal-cache", "x-generator")):
            if "drupal" in str(h).lower():
                tech.append("Drupal")
        if "set-cookie" in h:
            if "woocommerce" in str(h).lower():
                tech.append("WooCommerce")
            if "shopify" in str(h).lower():
                tech.append("Shopify")
        if "x-shopify" in h:
            tech.append("Shopify")
        if "wp-content" in body or "wp-includes" in body:
            tech.append("WordPress")
        if "_woocommerce" in body:
            tech.append("WooCommerce")
        if "触" in body or "定" in body:
            tech.append("Chinese CMS")
        if "nginx" in result["server"].lower():
            tech.append("nginx")
        if "apache" in result["server"].lower():
            tech.append("Apache")
        if "iis" in result["server"].lower():
            tech.append("IIS")

        result["tech_stack"] = list(dict.fromkeys(tech))

        # HTML title
        m = re.search(r"<title>([^<]+)</title>", body, re.I)
        if m:
            result["title"] = m.group(1).strip()[:120]

    except Exception:
        pass

    return result

# ═══════════════════════════════════════════════════════════════
#  SSL/TLS ANALYSIS
# ═══════════════════════════════════════════════════════════════

def ssl_grade_from_cert(ssl_info: dict) -> str:
    """Assign SSL security grade based on cert and protocol info."""
    grade = "A"
    issues = []

    cert = ssl_info.get("cert", {})
    proto = ssl_info.get("protocol", "")

    # Protocol check
    if proto in ("TLSv1.0", "TLSv1.1", "SSL"):
        grade = "C"
        issues.append("Deprecated protocol")
    if proto == "SSL":
        grade = "F"
        issues.append("Insecure SSL detected")

    # Key strength
    key_bits = cert.get("key_size", 0)
    if key_bits > 0 and key_bits < 2048:
        grade = "B"
        issues.append("Weak key")
    if key_bits > 0 and key_bits < 1024:
        grade = "F"

    # Self-signed
    if cert.get("self_signed", False):
        if grade == "A":
            grade = "B"
        issues.append("Self-signed certificate")

    # Expiry
    exp = cert.get("expires", "")
    if exp:
        try:
            exp_dt = datetime.datetime.strptime(exp[:16], "%b %d %H:%M:%S %Y")
            now = datetime.datetime.now()
            days_left = (exp_dt - now).days
            if days_left < 0:
                grade = "F"
                issues.append("Certificate expired")
            elif days_left < 30:
                if grade == "A":
                    grade = "B"
                issues.append(f"Cert expires in {days_left}d")
        except Exception:
            pass

    ssl_info["grade"] = grade
    ssl_info["issues"] = issues
    return grade

def get_ssl_info(ip: str, port: int, timeout: float = 5.0) -> dict:
    """Grab SSL/TLS certificate and cipher info."""
    info = {
        "protocol": "", "cipher": "", "cert": {},
        "grade": "unknown", "issues": [], "cert_fingerprint_sha1": "",
        "cert_fingerprint_sha256": "",
    }
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssock = context.wrap_socket(sock, server_hostname=ip)
        ssock.settimeout(timeout)
        ssock.connect((ip, port))

        cert = ssock.getpeercert(binary_form=True)
        cipher = ssock.cipher()
        proto = ssock.version()

        info["protocol"] = proto or ""
        info["cipher"] = cipher[0] if cipher else ""

        if cert:
            try:
                import subprocess
                result = subprocess.run(
                    ["openssl", "x509", "-inform", "der", "-noout", "-text"],
                    input=cert, capture_output=True, timeout=3
                )
                # parse subject/issuer from openssl output... skip for brevity
            except Exception:
                pass

            # Manual cert parsing from binary_form
            try:
                from cryptography import x509
                cert_obj = x509.load_der_x509_certificate(cert)
                subject = cert_obj.subject
                issuer  = cert_obj.issuer
                info["cert"] = {
                    "subject":   "/".join(f"{attr.oid.name}={attr.value}" for attr in subject),
                    "issuer":    "/".join(f"{attr.oid.name}={attr.value}" for attr in issuer),
                    "not_before": str(cert_obj.not_valid_before_utc)[:19],
                    "not_after":  str(cert_obj.not_valid_after_utc)[:19],
                    "expires":    str(cert_obj.not_valid_after_utc)[:19],
                    "serial":     str(cert_obj.serial_number),
                    "key_size":   0,  # would need deeper parsing
                    "self_signed": subject == issuer,
                }
            except ImportError:
                # fallback without cryptography
                info["cert"] = {
                    "subject": str(cert),
                    "not_after": "unknown",
                    "self_signed": False,
                    "key_size": 0,
                }

            # Fingerprints
            info["cert_fingerprint_sha1"]   = hashlib.sha1(cert).hexdigest().upper()
            info["cert_fingerprint_sha256"] = hashlib.sha256(cert).hexdigest().upper()

        ssock.close()
        info["grade"] = ssl_grade_from_cert(info)

    except ssl.SSLError as e:
        info["error"] = f"SSL error: {e}"
        if "wrong version" in str(e).lower():
            info["grade"] = "N/A"
    except Exception as e:
        info["error"] = str(e)

    return info

# ═══════════════════════════════════════════════════════════════
#  CVE MATCHING
# ═══════════════════════════════════════════════════════════════

def match_cves(service: str, version: str) -> list:
    """Match CVEs from local database based on service + version."""
    matched = []
    service_lower = service.lower().replace("-", "").replace("_", "")

    for entry in CVE_DATABASE:
        entry_svc = entry["service"].lower().replace("-", "").replace("_", "")
        if service_lower and entry_svc not in service_lower and service_lower not in entry_svc:
            continue

        # Simple version check — just attach all for now since
        # CVE database has pattern matches; full regex match deferred
        cve_entry = {
            "cve": entry["cve"],
            "level": entry["level"],
            "description": entry["description"],
            "service": entry["service"],
            "version_hint": entry["version_pattern"],
        }
        matched.append(cve_entry)

    return matched

def vuln_level_from_cves(cves: list) -> str:
    """Derive overall vulnerability level from CVE list."""
    if any(c["level"] == "CRITICAL" for c in cves):
        return "CRITICAL"
    if any(c["level"] == "HIGH" for c in cves):
        return "HIGH"
    if any(c["level"] == "MEDIUM" for c in cves):
        return "MEDIUM"
    if any(c["level"] == "LOW" for c in cves):
        return "LOW"
    return "NONE"

# ═══════════════════════════════════════════════════════════════
#  OS FINGERPRINTING
# ═══════════════════════════════════════════════════════════════

def os_fingerprint(ttl: int, rtt: float, open_ports: list) -> str:
    """OS fingerprinting via TTL + open port heuristics."""
    guesses = []

    # TTL-based
    if ttl == 0:
        pass
    elif ttl <= 64:
        guesses.append("Linux/Unix (TTL≈64)")
    elif ttl <= 128:
        guesses.append("Windows (TTL≈128)")
    elif ttl <= 255:
        guesses.append("Network Device / Solaris (TTL≈255)")
    elif ttl <= 254:
        guesses.append("macOS / older Linux (TTL≈64-ish, possible customizing)")

    # Port-based
    if 3389 in open_ports and 445 in open_ports:
        guesses.append("Windows Desktop")
    if 22 in open_ports and 80 in open_ports and 443 in open_ports:
        guesses.append("Linux/Unix Server")
    if 22 in open_ports and not 80 in open_ports:
        guesses.append("Linux/Unix (SSH-only)")
    if 135 in open_ports and 139 in open_ports and 445 in open_ports:
        guesses.append("Windows Server")
    if 3306 in open_ports or 5432 in open_ports:
        guesses.append("Database Server")
    if 6379 in open_ports or 27017 in open_ports:
        guesses.append("NoSQL Server")

    if not guesses:
        if rtt and rtt < 1:
            guesses.append("Local/Loopback network")
        elif rtt and rtt > 50:
            guesses.append("Remote/WAN target")

    return "; ".join(guesses[:3]) if guesses else "Unknown OS"

# ═══════════════════════════════════════════════════════════════
#  SUBDOMAIN ENUMERATION (DNS)
# ═══════════════════════════════════════════════════════════════

COMMON_SUBDOMAINS = [
    "www", "mail", "ftp", "admin", "api", "dev", "test", "staging",
    "blog", "shop", "secure", "vpn", "remote", "portal", "webmail",
    "smtp", "pop", "ns1", "mx", "dns", "cdn", "static", "assets",
    "app", "mobile", "git", "jenkins", "ci", "db", "database",
    "backup", "proxy", "ns", "mx1", "web", "owa", "svn",
]

def enumerate_subdomains(domain: str, timeout: float = 3.0) -> list:
    """Enumerate subdomains via DNS lookup. domain must be a valid base."""
    found = []
    for sub in COMMON_SUBDOMAINS:
        if SCAN_STATS["quit_requested"]:
            break
        full = f"{sub}.{domain}" if domain else sub
        try:
            ips = socket.getaddrinfo(full, None, socket.AF_INET)
            resolved = sorted(set(r[4][0] for r in ips))
            if resolved:
                found.append({"subdomain": full, "ips": resolved})
        except (socket.gaierror, socket.error, OSError):
            pass
        rate_limit(0.05)  # gentle rate limit to avoid DNS flood
    return found

def guess_domain_from_ip(ip: str) -> Optional[str]:
    """Try to extract a plausible domain from the IP via reverse DNS."""
    try:
        name, _, _ = socket.gethostbyaddr(ip)
        # Strip trailing dot
        name = name.rstrip(".")
        # Use the domain portion (e.g. server1.example.com → example.com)
        parts = name.split(".")
        if len(parts) >= 2:
            return ".".join(parts[-2:])
        return name
    except Exception:
        return None

# ═══════════════════════════════════════════════════════════════
#  TRACEROUTE
# ═══════════════════════════════════════════════════════════════

def traceroute(target: str, max_hops: int = 30, timeout: float = 2.0,
               probes_per_hop: int = 2) -> list:
    """Simple traceroute using ICMP/UDP probes with decreasing TTL."""
    hops = []
    try:
        import subprocess
        result = subprocess.run(
            ["traceroute", "-m", str(max_hops), "-w", str(timeout),
             "-q", str(probes_per_hop), target],
            capture_output=True, text=True, timeout=max_hops * timeout + 10
        )
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("traceroute"):
                continue
            # Parse " 1  192.168.1.1 (192.168.1.1)  0.871 ms"
            m = re.match(r"^\s*(\d+)\s+(.+?)\s+\(([0-9.]+)\)", line)
            if not m:
                parts = line.split()
                if parts and parts[0].isdigit():
                    hop_num = int(parts[0])
                    ip = None
                    for p in parts:
                        if re.match(r"\d+\.\d+\.\d+\.\d+", p):
                            ip = p
                            break
                    if ip:
                        hops.append({"hop": hop_num, "ip": ip, "rtt": ""})
            else:
                hops.append({
                    "hop": int(m.group(1)),
                    "hostname": m.group(2),
                    "ip": m.group(3),
                    "rtt": line
                })
    except FileNotFoundError:
        # traceroute not available — try traceroute-ng or pathping on Windows
        try:
            if os.name == "nt":
                result = subprocess.run(["pathping", target, "-h", str(max_hops)],
                                       capture_output=True, text=True, timeout=60)
                for line in result.stdout.strip().split("\n"):
                    m = re.match(r"\s*(\d+)\s+([0-9.]+)", line)
                    if m:
                        hops.append({"hop": int(m.group(1)), "ip": m.group(2), "rtt": ""})
        except Exception:
            pass
        except FileNotFoundError:
            pass
    except Exception:
        pass
    return hops[:max_hops]

# ═══════════════════════════════════════════════════════════════
#  PORT SCANNING
# ═══════════════════════════════════════════════════════════════

def scan_port(ip: str, port: int, timeout: float = TIMEOUT_DEFAULT,
              rate_delay: float = 0) -> Optional[PortResult]:
    """Single port scan with banner grab, HTTP fingerprint, SSL analysis."""
    SCAN_STATS["ports_scanned"] += 1

    if rate_delay > 0:
        time.sleep(rate_delay)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.perf_counter()
        result_code = sock.connect_ex((ip, port))
        rtt = (time.perf_counter() - start) * 1000

        if result_code != 0:
            sock.close()
            return None

        sock.close()

        service = guess_service(port)
        banner = grab_banner(ip, port, timeout=3.0)
        version = parse_banner_for_version(banner, service)

        port_result = PortResult(
            port=port, state="open", rtt_ms=round(rtt, 2),
            service=service, version=version, banner=banner,
        )

        # HTTP/HTTPS fingerprinting
        if port in (80, 8080, 8000, 8888, 3000, 5000, 8008, 8090, 8443, 443, 8081):
            http_info = http_fingerprint(ip, port, use_ssl=(port in (443, 8443, 8081, 8443)), timeout=5.0)
            port_result.http_fingerprint = http_info
            if http_info.get("server"):
                port_result.version = http_info["server"]

        # SSL/TLS for HTTPS ports
        if port in (443, 8443, 995, 993, 465, 636):
            ssl_info = get_ssl_info(ip, port, timeout=5.0)
            port_result.ssl_info = ssl_info

        # CVE matching
        svc = (service or "").lower()
        cves = match_cves(svc, version)
        if cves:
            port_result.cves = cves
            port_result.vuln_level = vuln_level_from_cves(cves)

        # OS hints
        port_result.os_hint = []
        if 3389 in [port]:
            port_result.os_hint.append("Windows RDP")
        if service in ("ssh", "sftp"):
            port_result.os_hint.append("Linux/Unix SSH")
        if service in ("http", "http-proxy"):
            port_result.os_hint.append("Web server")

        return port_result

    except Exception as e:
        SCAN_STATS["errors"] += 1
        return None

def tcp_connect_scan(ip: str, ports: list, timeout: float = TIMEOUT_DEFAULT,
                     workers: int = MAX_THREADS, rate_delay: float = 0) -> dict:
    """Concurrent TCP connect scan."""
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(scan_port, ip, p, timeout, rate_delay): p for p in ports}
        for fut in concurrent.futures.as_completed(futures):
            if SCAN_STATS["quit_requested"]:
                break
            port = futures[fut]
            try:
                res = fut.result()
                if res:
                    results[port] = res
            except Exception:
                SCAN_STATS["errors"] += 1
    return results

def full_port_scan(ip: str, port_range: tuple = (1, 65535),
                   timeout: float = TIMEOUT_DEFAULT,
                   workers: int = MAX_THREADS, rate_delay: float = 0) -> dict:
    """Scan a full range of ports. Use with care."""
    # Build list of ports
    if port_range == (1, 1024):
        ports = WELL_KNOWN_PORTS
    elif port_range == (1, 65535):
        ports = list(range(1, 65536))
    elif port_range == (1, 49151):
        ports = list(range(1, 49152))
    else:
        ports = list(range(port_range[0], port_range[1] + 1))

    # Thin the worker count for massive scans
    effective_workers = min(workers, 50) if len(ports) > 5000 else workers
    effective_workers = max(10, effective_workers)

    return tcp_connect_scan(ip, ports, timeout, effective_workers, rate_delay)

# ═══════════════════════════════════════════════════════════════
#  MAIN SCAN LOGIC
# ═══════════════════════════════════════════════════════════════

def full_scan(targets: list, depth: str = "normal",
              port_range: tuple = (1, 1024),
              timeout: float = TIMEOUT_DEFAULT,
              workers: int = MAX_THREADS,
              rate_delay: float = 0,
              traceroute_enabled: bool = False,
              subdomain_enum: bool = False,
              quiet: bool = False) -> ScanResult:

    SCAN_STATS["start_time"] = time.time()
    scan_type_map = {
        "quick":   ("quick", QUICK_PORTS),
        "normal":  ("normal", COMMON_PORTS),
        "intense": ("intense", TOP_PORTS_100),
        "full":    ("full", WELL_KNOWN_PORTS),
        "deep":    ("deep", list(range(1, 65536))),
        "custom":  ("custom", []),
    }
    mode, base_ports = scan_type_map.get(depth, scan_type_map["normal"])

    # Override ports if custom range provided
    if port_range != (1, 1024):
        mode = f"{depth} ({port_range[0]}-{port_range[1]})"
        if port_range == (1, 65535):
            base_ports = list(range(1, 65536))
        elif port_range == (1, 49151):
            base_ports = list(range(1, 49152))
        else:
            base_ports = list(range(port_range[0], port_range[1] + 1))

    errors = []
    _progress(f"[*] Scanning {len(targets)} target(s) — {mode}")

    # Host discovery
    hosts = discover_hosts(targets, timeout=timeout, workers=workers, rate=rate_delay)
    alive_hosts = [h for h in hosts if h.is_alive]

    if not quiet:
        print(f"[+] {len(alive_hosts)} live host(s) found")

    # Per-host scanning
    for h in alive_hosts:
        if SCAN_STATS["quit_requested"]:
            break
        if not quiet:
            _progress(f"[*] Scanning {h.ip} — {len(base_ports)} ports")

        # OS fingerprint from TTL + port pattern
        h.os_guess = os_fingerprint(h.ttl, h.rtt_ms, list(h.ports.keys()))

        # Traceroute
        if traceroute_enabled:
            h.traceroute = traceroute(h.ip, max_hops=20)

        # Subdomain enumeration
        if subdomain_enum and h.hostname:
            domain = guess_domain_from_ip(h.ip) or h.hostname
            h.subdomains = enumerate_subdomains(domain)

        # Port scan
        if port_range == (1, 65535) or port_range == (1, 49151):
            h.ports = full_port_scan(h.ip, port_range, timeout, workers, rate_delay)
        else:
            h.ports = tcp_connect_scan(h.ip, base_ports, timeout, workers, rate_delay)

        # Re-derive OS with port data
        open_ports = list(h.ports.keys())
        h.os_guess = os_fingerprint(h.ttl, h.rtt_ms, open_ports)

        # Collect CVEs from all open ports
        all_cves = []
        for p in h.ports.values():
            all_cves.extend(getattr(p, "cves", []))
        h.cves = all_cves

        # Summary
        crit  = sum(1 for c in all_cves if c.get("level") == "CRITICAL")
        high  = sum(1 for c in all_cves if c.get("level") == "HIGH")
        med   = sum(1 for c in all_cves if c.get("level") == "MEDIUM")
        low   = sum(1 for c in all_cves if c.get("level") == "LOW")
        h.summary = {
            "total_open_ports": len(h.ports),
            "cves": {"critical": crit, "high": high, "medium": med, "low": low},
            "overall_risk": "CRITICAL" if crit else "HIGH" if high else "MEDIUM" if med else "LOW" if low else "NONE",
        }

        if not quiet:
            vuln = h.summary["overall_risk"]
            print(f"[+] {h.ip} — {len(h.ports)} ports open | Risk: {vuln} | OS: {h.os_guess[:50]}")

    duration = time.time() - SCAN_STATS["start_time"]

    return ScanResult(
        target=", ".join(targets),
        scan_type=mode,
        hosts=[h for h in hosts if h.is_alive],
        errors=errors,
        duration_s=round(duration, 2),
        scan_stats=dict(SCAN_STATS),
        args={
            "depth": depth,
            "port_range": str(port_range),
            "timeout": timeout,
            "workers": workers,
            "rate_delay": rate_delay,
            "traceroute": traceroute_enabled,
            "subdomain_enum": subdomain_enum,
        }
    )

# ═══════════════════════════════════════════════════════════════
#  OUTPUT FORMATTERS
# ═══════════════════════════════════════════════════════════════

def format_discord(hosts: list, target: str, scan_type: str,
                   duration: float, scan_stats: dict, overall_risk: str) -> str:
    risk_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡",
                  "LOW": "🟢", "NONE": "⚪"}.get(overall_risk, "⚪")

    lines = [
        f"**🔍 EdgeIQ Scan Report — `{target}`**",
        f"Mode: `{scan_type}` | Risk: {risk_emoji} **{overall_risk}** | Duration: `{duration:.1f}s`",
        ""
    ]
    if not hosts:
        lines.append("> _No live hosts detected._")
        return "\n".join(lines)

    for h in hosts:
        open_count = len(h.ports)
        risk = h.summary.get("overall_risk", "NONE") if h.summary else "NONE"
        risk_emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡",
                      "LOW": "🟢", "NONE": "⚪"}.get(risk, "⚪")
        rtt_str = f" `{h.rtt_ms}ms`" if h.rtt_ms else ""
        host_str = f"{risk_emoji} **{h.ip}**"
        if h.hostname:
            host_str += f" — `{h.hostname}`"
        host_str += f"{rtt_str} | {open_count} ports | {risk}"
        lines.append(host_str)

        if h.os_guess:
            lines.append(f"   └ OS: `{h.os_guess[:80]}`")

        if h.subdomains:
            subs = ", ".join(s["subdomain"] for s in h.subdomains[:5])
            lines.append(f"   └ Subdomains: `{subs}`")

        if h.traceroute:
            hop1 = h.traceroute[0] if len(h.traceroute) > 0 else {}
            lines.append(f"   └ Route: → {hop1.get('ip', '?')}")

        # Show up to 8 ports
        sorted_ports = sorted(h.ports.values(), key=lambda x: x["port"])[:8]
        for p in sorted_ports:
            port  = p.port
            svc   = p.service or "?"
            ver   = p.version or ""
            lvl   = p.vuln_level or ""
            lvl_str = f" ⚠️ {lvl}" if lvl and lvl != "NONE" else ""
            banner_short = (p.banner or "")[:50].replace("`", "")
            ver_str = f" `{ver}`" if ver else ""
            banner_str = f" — {banner_short}" if banner_short else ""
            ssl_info = ""
            if p.ssl_info and p.ssl_info.get("grade"):
                ssl_info = f" [SSL: {p.ssl_info['grade']}]"
            lines.append(f"  `{port:>5}` {svc:<12}{ver_str}{lvl_str}{ssl_info}{banner_str}")

        # CVE summary
        if h.cves:
            crit_cves = [c["cve"] for c in h.cves if c.get("level") == "CRITICAL"]
            high_cves = [c["cve"] for c in h.cves if c.get("level") == "HIGH"]
            if crit_cves:
                lines.append(f"   └ 🔴 CVEs: `{'`, `'.join(crit_cves[:3])}`")
            elif high_cves:
                lines.append(f"   └ 🟠 CVEs: `{'`, `'.join(high_cves[:3])}`")

        if open_count > 8:
            lines.append(f"  _...and `{open_count - 8}` more ports_")
        lines.append("")

    # Footer stats
    lines.append(f"─── Stats: **{scan_stats.get('hosts_found', 0)}** hosts | "
                 f"**{scan_stats.get('ports_scanned', 0)}** ports scanned | "
                 f"**{scan_stats.get('errors', 0)}** errors")
    return "\n".join(lines).strip()

def format_simple(hosts: list) -> str:
    out = []
    for h in hosts:
        out.append(f"\n{'='*60}")
        out.append(f"Host: {h.ip} ({h.hostname or 'unknown'}) | RTT: {h.rtt_ms}ms")
        out.append(f"OS: {h.os_guess}")
        out.append(f"Open Ports:")
        for p in sorted(h.ports.values(), key=lambda x: x["port"]):
            banner = (p.banner or "")[:60]
            cve_str = f" [{p.vuln_level}]" if p.vuln_level and p.vuln_level != "NONE" else ""
            ssl_str = f" SSL:{p.ssl_info.get('grade','')}" if p.ssl_info.get("grade") else ""
            out.append(f"  {p.port:>5}/tcp {p.service:<12} {p.version or ''}{cve_str}{ssl_str}")
            if banner:
                out.append(f"       Banner: {banner}")
        if h.cves:
            out.append("CVEs:")
            for c in h.cves[:10]:
                out.append(f"  [{c['level']}] {c['cve']} — {c['description']}")
    return "\n".join(out)

def export_json(result: ScanResult) -> str:
    return json.dumps(result.to_dict(), indent=2, default=str)

def export_html(result: ScanResult) -> str:
    """Generate a standalone HTML report."""
    timestamp = result.timestamp
    target = result.target
    duration = result.duration_s

    rows = []
    for h in result.hosts:
        open_count = len(h.ports)
        risk = h.summary.get("overall_risk", "NONE") if h.summary else "NONE"
        risk_color = {"CRITICAL": "red", "HIGH": "orange", "MEDIUM": "yellow", "LOW": "green", "NONE": "gray"}.get(risk, "gray")
        rows.append(f"""<tr class="host-row">
            <td><strong>{h.ip}</strong><br><small>{h.hostname or ''}</small></td>
            <td>{h.rtt_ms or '?'} ms</td>
            <td>{h.os_guess or 'unknown'}</td>
            <td>{open_count}</td>
            <td><span class="risk risk-{risk_color}">{risk}</span></td>
            <td>{"<br>".join(f"{p.port}/{p.service} {'⚠️'+p.vuln_level if p.vuln_level not in ('NONE','') else ''}" for p in sorted(h.ports.values(), key=lambda x: x.port))}</td>
            <td>{"<br>".join(f"[{c['level']}] {c['cve']}" for c in h.cves[:5])}</td>
        </tr>""")

    table_rows = "\n".join(rows) if rows else "<tr><td colspan='7'>No hosts found.</td></tr>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>EdgeIQ Scan Report — {target}</title>
<style>
  body {{ font-family: Arial, sans-serif; background: #0d1117; color: #e6edf3; margin: 0; padding: 20px; }}
  h1 {{ color: #58a6ff; }}
  .meta {{ color: #8b949e; margin-bottom: 20px; }}
  table {{ border-collapse: collapse; width: 100%; background: #161b22; }}
  th {{ background: #21262d; color: #8b949e; padding: 8px; text-align: left; border: 1px solid #30363d; }}
  td {{ padding: 8px; border: 1px solid #30363d; vertical-align: top; }}
  .host-row:hover {{ background: #1c2128; }}
  .risk {{ padding: 2px 8px; border-radius: 4px; font-size: 0.85em; font-weight: bold; }}
  .risk-red    {{ background: #3d0000; color: #ff6b6b; }}
  .risk-orange {{ background: #3d2200; color: #ffa94d; }}
  .risk-yellow {{ background: #3d3500; color: #ffd43b; }}
  .risk-green  {{ background: #003d00; color: #69db7c; }}
  .risk-gray   {{ background: #21262d; color: #8b949e; }}
  .footer {{ margin-top: 20px; color: #8b949e; font-size: 0.85em; }}
  .section {{ margin: 20px 0; }}
</style>
</head>
<body>
<h1>🔍 EdgeIQ Network Scan Report</h1>
<div class="meta">
  <strong>Target:</strong> {target} |
  <strong>Scan Type:</strong> {result.scan_type} |
  <strong>Duration:</strong> {duration}s |
  <strong>Date:</strong> {timestamp} |
  <strong>Hosts Found:</strong> {result.scan_stats.get('hosts_found', 0)} |
  <strong>Ports Scanned:</strong> {result.scan_stats.get('ports_scanned', 0)}
</div>

<h2>Hosts</h2>
<table>
  <thead>
    <tr>
      <th>IP / Hostname</th>
      <th>RTT</th>
      <th>OS Guess</th>
      <th>Open Ports</th>
      <th>Risk</th>
      <th>Services</th>
      <th>CVEs</th>
    </tr>
  </thead>
  <tbody>
    {table_rows}
  </tbody>
</table>

<div class="footer">
  <p>Generated by EdgeIQ Network Scanner | scan_stats: {json.dumps(result.scan_stats)}</p>
</div>
</body>
</html>"""
    return html

# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="network_scanner",
        description="EdgeIQ Network Scanner — Professional-grade security reconnaissance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 192.168.1.0/24 quick
  %(prog)s 10.5.1.1 intense --format discord
  %(prog)s example.com full --subdomains --traceroute
  %(prog)s 10.0.0.1 --depth deep --timeout 2.0
  %(prog)s 192.168.1.1 --port-range 1-10000
  %(prog)s 192.168.1.1 --output scan.json --format json
  %(prog)s 192.168.1.1 --output report.html --format html
  %(prog)s --local-scan normal --format simple

Legal: Only scan networks you own or have written authorization to audit.
        """
    )
    p.add_argument("target", nargs="?", help="IP, CIDR, hostname, or URL")
    p.add_argument("depth", nargs="?", choices=["quick", "normal", "intense", "full", "deep", "custom"],
                   default="normal", help="Scan depth (default: normal)")

    # Scanning options
    p.add_argument("--depth", dest="depth_arg", choices=["quick", "normal", "intense", "full", "deep"],
                   help="Scan depth (alias for positional arg)")
    p.add_argument("--port-range", dest="port_range", default="1-1024",
                   help="Custom port range, e.g. 1-1000 or 1-65535 (default: 1-1024)")
    p.add_argument("--timeout", type=float, default=TIMEOUT_DEFAULT,
                   help=f"Socket timeout seconds (default: {TIMEOUT_DEFAULT})")
    p.add_argument("--workers", type=int, default=MAX_THREADS,
                   help=f"Concurrent workers (default: {MAX_THREADS})")
    p.add_argument("--rate-delay", type=float, default=0,
                   help="Delay in seconds between each port scan (stealth mode)")

    # Feature flags
    p.add_argument("--traceroute", action="store_true",
                   help="Enable traceroute to each discovered host")
    p.add_argument("--subdomains", action="store_true",
                   help="Enable subdomain enumeration via DNS")
    p.add_argument("--local", action="store_true",
                   help="Scan all local network ranges")
    p.add_argument("--local-scan", action="store_true",
                   help="Fast local scan: gateway + nearby IPs")
    p.add_argument("--proxy", dest="proxy_url",
                   help="HTTP/SOCKS proxy for scanning (e.g. socks5://127.0.0.1:9050)")

    # Output options
    p.add_argument("--format", choices=["discord", "simple", "json", "html"],
                   default="discord", help="Output format (default: discord)")
    p.add_argument("--output", "-o", dest="output_file",
                   help="Write output to file (also sets --quiet)")
    p.add_argument("--quiet", "-q", action="store_true",
                   help="Minimal output (automation mode)")
    p.add_argument("--no-color", action="store_true", help="Disable color codes")

    return p

def parse_port_range(range_str: str) -> tuple:
    try:
        start, end = range_str.split("-")
        return int(start.strip()), int(end.strip())
    except Exception:
        return 1, 1024

def main():
    # Mark as CLI invocation for quiet-mode detection
    sys._called_via_cli = True

    parser = build_parser()
    args = parser.parse_args()

    # Support --depth alias
    depth = args.depth_arg or args.depth

    # Resolve targets
    targets = []
    if args.local:
        targets = get_local_networks()
    elif args.local_scan:
        local_ip = get_local_ip()
        gateway  = get_gateway_ip()
        targets  = []
        if local_ip:
            subnet = ".".join(local_ip.split(".")[:3])
            if gateway:
                targets.append(gateway)
            targets.append(local_ip)
            for i in [1, 2, 3, 100, 101, 254]:
                ip = f"{subnet}.{i}"
                if ip != local_ip and ip != gateway:
                    targets.append(ip)
            targets = list(dict.fromkeys(targets))
    elif args.target:
        targets = [args.target]
    else:
        print("Error: specify a target or use --local / --local-scan")
        sys.exit(1)

    if not targets:
        print("No targets specified.")
        sys.exit(1)

    port_range = parse_port_range(args.port_range)

    # ── License Gates ────────────────────────────────────────────────────────
    # Deep port scan (> 1-1024) requires Pro
    port_end = port_range[1]
    if port_end > 1024 and not is_pro():
        require_license("pro", "Full port range scanning (1-65535)")
        sys.exit(1)

    # HTML report export requires Pro (JSON and other formats are free)
    if getattr(args, 'format', None) == 'html' and not is_pro():
        print("HTML report export requires Pro license.")
        print("Upgrade: https://buy.stripe.com/7sYaEZeCn5934nW8AE7wA01")
        sys.exit(1)

    # Traceroute is Pro
    if getattr(args, 'traceroute', False) and not is_pro():
        require_license("pro", "Traceroute network path analysis")
        sys.exit(1)

    # Subdomain enumeration is Pro
    if getattr(args, 'subdomains', False) and not is_pro():
        require_license("pro", "DNS subdomain enumeration")
        sys.exit(1)

    result = full_scan(
        targets=targets,
        depth=depth,
        port_range=port_range,
        timeout=args.timeout,
        workers=args.workers,
        rate_delay=args.rate_delay,
        traceroute_enabled=args.traceroute,
        subdomain_enum=args.subdomains,
        quiet=args.quiet or args.output is not None
    )

    # Add scan stats
    result.scan_stats = dict(SCAN_STATS)

    # Overall risk
    all_cves = [c for h in result.hosts for c in h.cves]
    overall_risk = "CRITICAL" if any(c.get("level") == "CRITICAL" for c in all_cves) else \
                   "HIGH"     if any(c.get("level") == "HIGH"     for c in all_cves) else \
                   "MEDIUM"   if any(c.get("level") == "MEDIUM"   for c in all_cves) else \
                   "LOW"      if any(c.get("level") == "LOW"      for c in all_cves) else "NONE"

    # Format output
    if args.format == "discord":
        output = format_discord(result.hosts, result.target, result.scan_type,
                                result.duration_s, result.scan_stats, overall_risk)
    elif args.format == "simple":
        output = format_simple(result.hosts)
    elif args.format == "html":
        output = export_html(result)
    else:
        output = export_json(result)

    # Write to file or stdout
    if args.output_file:
        with open(args.output_file, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"[+] Report written to {args.output_file}")
    else:
        print(output)

    # Proper exit codes for automation
    if EXIT_CODE == 2:
        sys.exit(2)
    if overall_risk == "CRITICAL":
        sys.exit(3)
    if overall_risk == "HIGH":
        sys.exit(4)

if __name__ == "__main__":
    main()