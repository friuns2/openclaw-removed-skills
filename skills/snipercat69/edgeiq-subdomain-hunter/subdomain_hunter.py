#!/usr/bin/env python3
"""
EdgeIQ Labs — Subdomain Hunter
Passive subdomain enumeration via Certificate Transparency, DNS, and takeover detection.
"""

import argparse
import csv
import json
import os
import socket
import sys
import time
import urllib.request
import urllib.parse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ─────────────────────────────────────────────
# ANSI helpers
# ─────────────────────────────────────────────
_GRN = '\033[92m'; _YLW = '\033[93m'; _RED = '\033[91m'; _CYA = '\033[96m'
_BLD = '\033[1m'; _RST = '\033[0m'; _MAG = '\033[35m'

def ok(t):    return f"{_GRN}{t}{_RST}"
def warn(t):  return f"{_YLW}{t}{_RST}"
def fail(t):  return f"{_RED}{t}{_RST}"
def info(t):  return f"{_CYA}{t}{_RST}"
def bold(t):  return f"{_BLD}{t}{_RST}"
def dim(t):   return f"{_RST}{t}"

# ─────────────────────────────────────────────
# Licensing
# ─────────────────────────────────────────────
LICENSE_FILE = Path.home() / ".edgeiq" / "license.key"
VALID_LICENSES = {}

def load_licenses():
    """Load VALID_LICENSES from license file."""
    global VALID_LICENSES
    p = LICENSE_FILE
    if p.exists():
        key = p.read().strip()
        VALID_LICENSES[key] = "bundle"

def is_pro():
    load_licenses()
    env_key = os.environ.get("EDGEIQ_LICENSE_KEY", "").strip()
    if env_key in VALID_LICENSES:
        return True
    email = os.environ.get("EDGEIQ_EMAIL", "").strip().lower()
    if email in ("gpalmieri21@gmail.com",):
        return True
    return False

def require_pro():
    if is_pro():
        return True
    print()
    print(f"{_RED}╔{'═' * 56}╗")
    print(f"{_RED}║  🔒 Pro Feature                              ║".ljust(63) + "║")
    print(f"{_RED}╠{'═' * 56}╣")
    print(f"{_RED}║  This feature requires Pro or Bundle license.║".ljust(63) + "║")
    print(f"{_RED}║  Your current tier: FREE                       ║".ljust(63) + "║")
    print(f"{_RED}║                                                    ║".ljust(63) + "║")
    print(f"{_RED}║  Upgrade options:                                 ║".ljust(63) + "║")
    print(f"{_RED}║    Pro ($19/mo):   https://buy.stripe.com/7sYaEZeCn5934nW8AE7wA01  ║".ljust(63) + "║")
    print(f"{_RED}║    Bundle ($39/mo): https://buy.stripe.com/aFabJ3am79pjg6E18c7wA02  ║".ljust(63) + "║")
    print(f"{_RED}╚{'─' * 56}╝")
    print()
    return False

# ─────────────────────────────────────────────
# Wordlists
# ─────────────────────────────────────────────
COMMON_SUBDOMAINS = [
    "www","api","blog","dev","test","stage","staging","admin","shop",
    "store","app","mail","ftp","ssh","vpn","cdn","static","assets",
    "images","img","video","media","Files","dashboard","portal","crm",
    "erp","support","help","status","monitor","analytics","stats",
    "billing","pay","checkout","orders","inventory","hr","recruit",
    "jobs","careers","forum","chat","social","connect","auth","login",
    "signin","signup","register","account","profile","settings","wp",
    "wordpress","joomla","drupal","moodle","gitlab","github","jenkins",
    "ci","cd","build","deploy","prod","demo","sandbox","backup",
    "db","database","mysql","postgres","mongo","redis","elastic","kibana",
    "grafana","prometheus","splunk","jira","confluence","wiki","docs",
    "documentation","api","rest","soap","graphql","v1","v2","v3",
    "old","legacy","archive","beta","alpha","pre","mx","ns","dns",
    "smtp","pop","imap","webmail","owa","exchange","sip","voip",
    "proxy","gateway","router","fw","firewall","vpc","aws","azure","gcp",
    "cloud","cluster","kube","kubernetes","docker","container","registry",
    "nexus","artifactory","pypi","npm","maven","gradle","rust","go",
    "internal","extranet","partner","vendor","customer","client",
]

TAKEOVER_SIGNATURES = {
    "heroku": ["herokuapp.com", "heroku.com"],
    "github": ["github.io", "github.com"],
    "gitlab": ["gitlab.io"],
    "bitbucket": ["bitbucket.org"],
    "aws-s3": ["s3.amazonaws.com", "amazonaws.com"],
    "cloudfront": ["cloudfront.net"],
    "azure": ["azurewebsites.net", "cloudapp.net"],
    "netlify": ["netlify.app", "netlify.com"],
    "vercel": ["vercel.app", "now.sh"],
    "wordpress": ["wordpress.com"],
    "shopify": ["myshopify.com"],
    "tumblr": ["tumblr.com"],
    "tumblr": ["blogspot.com"],
    "ghost": ["ghost.io"],
    "medium": ["medium.com"],
    "strikingly": ["strikingly.com"],
    "surge": ["surge.sh"],
    "firebase": ["firebaseapp.com"],
    "digitalocean": ["digitalocean.com"],
    "render": ["onrender.com"],
    "fly": ["fly.dev"],
}

# ─────────────────────────────────────────────
# Certificate Transparency via crt.sh
# ─────────────────────────────────────────────
def get_ssl_sans(domain):
    """Get SANs directly from the domain's SSL certificate (current active cert only)."""
    subdomains = set()
    try:
        ctx = __import__("ssl").create_default_context()
        with __import__("urllib.request").urlopen(f"https://{domain}", context=ctx, timeout=10) as resp:
            cert = resp.connection.getpeercert()
        san_list = cert.get("subjectAltName", [])
        for san_type, san_val in san_list:
            if san_type == "DNS":
                if san_val.endswith(f".{domain}") or san_val == domain:
                    subdomains.add(san_val)
    except Exception:
        pass
    return list(subdomains)

def query_crtsh(domain, limit=50):
    """Query Certificate Transparency logs. Tries crt.sh first, then SSL cert fallback."""
    # Try crt.sh with multiple retry attempts
    urls_to_try = [
        f"https://crt.sh/?q=%.{domain}&output=json&limit={limit}",
        f"https://crt.sh/?q={domain}&output=json&limit={limit}",
    ]
    for url in urls_to_try:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; SubdomainHunter/1.0)"
                })
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = json.loads(resp.read().decode())
                subdomains = set()
                for entry in data:
                    names = entry.get("name_value", "")
                    for name in names.split("\n"):
                        name = name.strip().lower()
                        if name.endswith(f".{domain}") or name == domain:
                            subdomains.add(name)
                if subdomains:
                    return list(subdomains), None
            except Exception:
                if attempt < 2:
                    time.sleep(1.5 ** attempt)
                    continue
    # Fallback: get SANs directly from SSL cert
    ssl_subs = get_ssl_sans(domain)
    if ssl_subs:
        return ssl_subs, "ct_failed_using_ssl_cert"
    return [], "all CT sources failed"

# ─────────────────────────────────────────────
# DNS resolution
# ─────────────────────────────────────────────
def resolve_host(host):
    """Resolve a hostname to IP. Returns (host, ip, is_dead)."""
    try:
        ip = socket.gethostbyname(host)
        return host, ip, False
    except socket.gaierror:
        return host, None, True

def resolve_all(hosts, threads=20):
    """Resolve multiple hosts concurrently."""
    results = []
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(resolve_host, h): h for h in hosts}
        for future in as_completed(futures):
            results.append(future.result())
    return results

# ─────────────────────────────────────────────
# Zone transfer check
# ─────────────────────────────────────────────
def try_zone_transfer(domain):
    """Attempt DNS zone transfer via common NS records."""
    try:
        ns_records = []
        try:
            ns_resolver = socket.getaddrinfo(domain, 53, socket.AF_INET)
            ns_records = [ni[4][0] for ni in ns_resolver]
        except:
            pass

        if not ns_records:
            return "no_ns", None

        for ns_ip in ns_records[:2]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((ns_ip, 53))
                query = f"\x00\x01\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
                for label in domain.split("."):
                    query += bytes([len(label)]) + label.encode()
                query += b"\x00\x00\x0f\x00\x01"
                sock.send(query)
                resp = sock.recv(4096)
                sock.close()
                if b"\x00\x0f" in resp:
                    return "OPEN", None
            except:
                pass
        return "BLOCKED", None
    except Exception as e:
        return "ERROR", str(e)

# ─────────────────────────────────────────────
# Takeover detection
# ─────────────────────────────────────────────
def check_takeover(host):
    """Check if a dead subdomain is vulnerable to takeover."""
    for service, domains in TAKEOVER_SIGNATURES.items():
        for d in domains:
            if d in host:
                return "cname_match", service
    try:
        cname = socket.gethostbyname_ex(host)[0]
        for service, domains in TAKEOVER_SIGNATURES.items():
            for d in domains:
                if d in cname:
                    return "cname_match", service
        return "dead", None
    except:
        return "dead", None

# ─────────────────────────────────────────────
# Subdomain bruteforce (Pro)
# ─────────────────────────────────────────────
def bruteforce_subdomains(domain, wordlist, threads=20):
    """Bruteforce common subdomains."""
    candidates = [f"{name}.{domain}" for name in wordlist]
    results = resolve_all(candidates, threads=threads)
    found = [(h, ip) for h, ip, dead in results if not dead]
    return found

# ─────────────────────────────────────────────
# Main scan
# ─────────────────────────────────────────────
def scan(domain, pro=False, bundle=False, bruteforce=False, takeover=False,
         takeover_only=False, output=None, threads=20):
    """Run the full subdomain hunt."""
    print()
    print(f"{_CYA}{_BLD}╔{'═' * 50}╗{_RST}")
    print(f"{_CYA}{_BLD}║   Subdomain Hunter — {domain[:22]:<22}║{_RST}")
    print(f"{_CYA}{_BLD}╚{'═' * 50}╝{_RST}")
    print()

    tier = "BUNDLE" if bundle else "PRO" if pro else "FREE"
    print(f"  {_MAG}▶{_RST} Scanning {bold(domain)} [{tier}]")
    print()

    all_subdomains = set()
    takeover_candidates = []
    resolved = []
    dead = []
    takeover_found = []

    # 1. Certificate Transparency
    print(f"  {dim('── ' * 20)}")
    ct_limit = 500 if (pro or bundle) else 50
    ct_subs, ct_err = query_crtsh(domain, limit=ct_limit)
    if ct_err:
        print(f"  {fail('✘')} CT scan failed: {ct_err}")
    else:
        all_subdomains.update(ct_subs)
        print(f"  {ok('✔')} CT entries: {len(ct_subs)} (limit: {ct_limit})")

    # 2. Zone transfer
    print(f"  {dim('── ' * 20)}")
    zt_status, zt_err = try_zone_transfer(domain)
    if zt_status == "OPEN":
        print(f"  {fail('🔓')} Zone Transfer: {bold('OPEN')} — AXFR succeeded!")
    elif zt_status == "BLOCKED":
        print(f"  {ok('✔')} Zone Transfer: BLOCKED (refused)")
    else:
        print(f"  {warn('⚠')} Zone Transfer: {zt_status} — {zt_err or 'error'}")

    if takeover_only:
        print()
        return

    # 3. Resolve all discovered
    print(f"  {dim('── ' * 20)}")
    print(f"  {info('⏳')} Resolving {len(all_subdomains)} subdomains...")
    resolve_threads = 50 if bundle else (20 if pro else 5)
    resolved_raw = resolve_all(list(all_subdomains), threads=resolve_threads)
    for host, ip, is_dead in resolved_raw:
        if is_dead:
            dead.append(host)
        else:
            resolved.append((host, ip))

    # 4. Bruteforce (Pro/Bundle)
    if (pro or bundle) and bruteforce:
        print(f"  {dim('── ' * 20)}")
        wordlist = COMMON_SUBDOMAINS[:500] if pro else COMMON_SUBDOMAINS[:2000]
        print(f"  {info('⏳')} Bruteforcing {len(wordlist)} common subdomains...")
        bf_resolved = bruteforce_subdomains(domain, wordlist, threads=resolve_threads)
        for h, ip in bf_resolved:
            if h not in all_subdomains:
                all_subdomains.add(h)
                resolved.append((h, ip))
        print(f"  {ok('✔')} Bruteforce done — +{len(bf_resolved)} new")

    # 5. Takeover detection (Pro/Bundle)
    if (pro or bundle) and takeover:
        print(f"  {dim('── ' * 20)}")
        print(f"  {info('⏳')} Checking {len(dead)} dead subdomains for takeovers...")
        for host in dead:
            status, service = check_takeover(host)
            if status == "cname_match":
                takeover_candidates.append((host, service))
                takeover_found.append(host)
        if takeover_candidates:
            print(f"  {warn('⚠')} {len(takeover_candidates)} subdomain takeover candidates found")
        else:
            print(f"  {ok('✔')} No takeover candidates")

    # 6. Output
    print()
    print(f"  {dim('─' * 55)}")
    print()
    print(f"=== {bold(domain)} — {len(resolved)} resolved | {len(dead)} dead | {len(takeover_found)} takeovers ===")
    print()

    if resolved:
        for host, ip in sorted(resolved):
            print(f"  {ok('✔')} {host:<40} → {ip}")
    if dead and not takeover_found:
        for host in sorted(dead):
            print(f"  {warn('✘')} {host} — DEAD (no CNAME)")
    if takeover_found:
        for host, service in sorted(takeover_found):
            print(f"  {fail('🔴')} {host} — TAKEOVER ({service})")

    print()

    # Threat assessment
    threat = "LOW"
    if takeover_found:
        threat = "CRITICAL"
    elif len(dead) > 10:
        threat = "MEDIUM"
    threat_color = _RED if threat == "CRITICAL" else (_YLW if threat == "MEDIUM" else _GRN)
    print(f"  Threat Level: {threat_color}{bold(threat)}{_RST} | Resolved: {ok(len(resolved))} | Dead: {warn(len(dead))} | Takeovers: {fail(len(takeover_found))}")

    if output:
        report = {
            "domain": domain,
            "scan_time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "tier": tier,
            "resolved": [{"host": h, "ip": ip} for h, ip in resolved],
            "dead": dead,
            "takeovers": [{"host": h, "service": s} for h, s in takeover_found],
            "zone_transfer": zt_status,
            "threat_level": threat,
            "summary": {
                "total_resolved": len(resolved),
                "total_dead": len(dead),
                "total_takeovers": len(takeover_found),
            }
        }
        Path(output).write_text(json.dumps(report, indent=2))
        print(f"  {ok('✔')} JSON report saved: {output}")

    print()
    return len(takeover_found) > 0

# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EdgeIQ Subdomain Hunter")
    parser.add_argument("--domain", required=True, help="Target domain")
    parser.add_argument("--pro", action="store_true", help="Enable Pro features")
    parser.add_argument("--bundle", action="store_true", help="Enable Bundle features")
    parser.add_argument("--bruteforce", action="store_true", help="Run subdomain bruteforce")
    parser.add_argument("--takeover", action="store_true", help="Run takeover detection")
    parser.add_argument("--takeover-only", action="store_true", help="Only run takeover check")
    parser.add_argument("--output", help="Write JSON report to file")
    parser.add_argument("--threads", type=int, default=20, help="Concurrent threads")
    args = parser.parse_args()

    tier = "bundle" if args.bundle else ("pro" if args.pro else "free")
    pro_or_bundle = args.pro or args.bundle

    if not pro_or_bundle and (args.bruteforce or args.takeover or args.takeover_only):
        print(f"\n{_RED}⚠ Bruteforce and takeover detection require Pro/Bundle tier{_RST}\n")
        args.bruteforce = False
        args.takeover = False
        args.takeover_only = False

    result = scan(
        args.domain,
        pro=args.pro,
        bundle=args.bundle,
        bruteforce=args.bruteforce,
        takeover=args.takeover,
        takeover_only=args.takeover_only,
        output=args.output,
        threads=args.threads,
    )
    sys.exit(0 if not result else 1)
