# Subdomain Hunter — CLI Setup

A standalone subdomain enumeration and takeover detection tool. No Discord required.

## Prerequisites

- Python 3.8+
- `python-whois` (optional, for WHOIS lookups)

## Installation

```bash
# Clone the tool
git clone https://github.com/snipercat69/edgeiq-subdomain-hunter.git
cd edgeiq-subdomain-hunter

# Install dependencies (optional — only needed for WHOIS)
pip install python-whois
```

## Quick Start

```bash
# Free scan (50 CT results, no bruteforce, no takeover)
python3 subdomain_hunter.py --domain example.com

# Pro scan (unlimited CT, takeover detection)
EDGEIQ_EMAIL=your_email@gmail.com python3 subdomain_hunter.py --domain example.com --pro

# Bundle scan (bruteforce, more threads, full wordlist)
EDGEIQ_EMAIL=your_email@gmail.com python3 subdomain_hunter.py --domain example.com --bundle --bruteforce

# Export to JSON
python3 subdomain_hunter.py --domain example.com --pro --output report.json
```

## Features

- Certificate Transparency enumeration (crt.sh)
- DNS zone transfer check (AXFR attempt)
- Subdomain takeover detection (CNAME scanning)
- Common subdomain bruteforce
- JSON export for integrations
- Threaded resolution for speed

## Licensing

Free tier: limited CT results, no bruteforce, no takeover detection.

Pro ($19/mo) or Bundle ($39/mo): [buy.stripe.com/7sYaEZeCn5934nW8AE7wA01](https://buy.stripe.com/7sYaEZeCn5934nW8AE7wA01)

After purchase, save your license key to `~/.edgeiq/license.key` or set your email:
```bash
export EDGEIQ_EMAIL=your@email.com
```
