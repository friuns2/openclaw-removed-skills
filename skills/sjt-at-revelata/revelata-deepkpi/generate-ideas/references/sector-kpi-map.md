# Sector → Diagnostic KPI Map

Use this to decide what "going deep" means for a given business. These are
the operating KPIs that are *diagnostic* — i.e., the ones where a trend
actually tells you something about how the business is working, not just
the size of the P&L.

For every lookup, use the deepKPI `list_kpis` / `search_kpis` tools to find
the actual KPI names available for that company — names below are the
*concepts* to hunt for, not literal column names.

---

## Consumer — dining & food

### Full-service / casual dining (Darden, Texas Roadhouse, Brinker, Bloomin')
- Same-store sales (comps) — comps are the single most-watched number
- Traffic vs. ticket decomposition — is growth from more visits or higher
  average check?
- Unit count (restaurants open)
- Off-premises / to-go mix %
- Average unit volume (AUV) — per-restaurant revenue

### Fast casual (Chipotle, Sweetgreen, Cava, Shake Shack, Wingstop)
- Comps (same store sales growth)
- Digital sales mix %
- Unit count and new-unit opening pace
- AUV — how much each restaurant does annually
- Restaurant-level margin (if disclosed)

### QSR / fast food (McDonald's, Starbucks, Yum Brands, Restaurant Brands)
- Comps by segment / geography
- Digital / loyalty member count
- Store count — company vs. franchised split
- Mobile order / drive-thru / delivery mix

### Coffee specifically (Starbucks, Dutch Bros)
- Comps + traffic decomposition (Starbucks traffic has been a huge story)
- Rewards member count + % of transactions
- Unit count and pace

---

## Consumer — retail

### Discount / dollar stores (Dollar General, Dollar Tree, Five Below)
- Comps
- Traffic vs. ticket
- Store count and new opening pace
- Shrink (if disclosed) — has become a big story
- Consumables mix %

### Warehouse clubs (Costco, BJ's, Sam's via Walmart)
- Comps (often ex-gas, ex-FX)
- Membership fee income — this is most of the profit
- Member count + renewal rate
- Traffic + ticket decomposition

### Specialty retail (Lululemon, Ulta, Best Buy, Dick's, TJX)
- Comps
- Digital / e-commerce mix %
- Store count
- Category breakdowns where disclosed

### Off-price (Ross, TJX, Burlington)
- Comps — especially vs. mall-based retail as a spread
- New store opening pace
- Inventory turns (if disclosed)

### Department stores (Nordstrom, Macy's, Kohl's)
- Comps (store + digital)
- Digital mix %
- Gross margin — promotions vs. full-price mix
- Store count (are they closing?)

### Home improvement (Home Depot, Lowe's)
- Comps, pro vs. DIY mix
- Ticket size — big project activity
- Transaction count

---

## Consumer — e-commerce / marketplaces

### Marketplaces (Amazon, eBay, Etsy, Mercari)
- GMV (gross merchandise volume)
- Active buyer count
- Take rate (revenue / GMV)
- Ads revenue % (increasingly important)

### Rideshare / delivery (Uber, DoorDash, Lyft, Instacart)
- Orders / trips (volume)
- Gross bookings / GOV
- Take rate
- Monthly active users / consumers
- Contribution margin per order (where disclosed)
- Adjusted EBITDA per order / trip

### Food delivery specifically — same as above plus
- Restaurant supply / merchant count
- Subscription / loyalty member count (DashPass, Uber One)

---

## Consumer — streaming / media

### Streaming (Netflix, Disney, Warner, Paramount, Spotify)
- Subscribers — net adds per quarter, total base
- ARPU by region
- Churn rate (rarely disclosed cleanly but worth hunting for)
- Ad-tier penetration (newer)
- Content spend

### Gaming (Take-Two, EA, Roblox)
- MAU / DAU / bookings
- ARPDAU / bookings per user
- Content release cadence

### Traditional media (Comcast, Charter, Paramount cable)
- Video subscribers (declining story)
- Broadband subscribers
- Wireless subscribers (for cable operators)
- ARPU by segment

---

## Business — SaaS / software

### Horizontal SaaS (Salesforce, ServiceNow, Workday, HubSpot)
- ARR or subscription revenue growth
- Net revenue retention (NRR) — the single most important health metric
- Customer count by cohort (>$1M customers, etc.)
- RPO (remaining performance obligations) — forward-looking

### Vertical / SMB SaaS (Shopify, Toast, Monday, Asana)
- GMV (for transactional businesses like Shopify, Toast)
- Active merchant count
- ARR
- Take rate if applicable

### Cybersecurity (CrowdStrike, Palo Alto, Zscaler, SentinelOne)
- ARR and net new ARR per quarter
- Large customer count ($100K+, $1M+ ARR)
- NRR / DBNR
- Module attach rates (if disclosed)

### Cloud infra (Snowflake, MongoDB, Datadog)
- Revenue growth by customer segment
- NRR (esp. at Snowflake — huge)
- Customer count by size
- Consumption / usage KPIs

---

## Business — fintech & payments

### Payments (Visa, Mastercard, PayPal, Block, Adyen)
- Payment volume (TPV / GPV)
- Transaction count
- Take rate
- Active user count

### Digital banks / neobanks (SoFi, Nu Holdings)
- Member / customer count
- Deposits / AUC
- Net interest margin
- Products per customer

### BNPL (Affirm)
- GMV
- Active consumers + repeat rate
- Loss rate on loans

---

## Business — insurance & traditional finance

### P&C / auto insurance (Progressive, Allstate)
- Policies in force (PIF)
- Premium per policy
- Combined ratio
- Retention rate

### Health insurance (UnitedHealth, Humana, Elevance)
- Membership by segment (commercial, Medicare Advantage, Medicaid)
- Medical loss ratio (MLR)
- MA enrollment growth

---

## Industrials — autos & parts

### OEMs (Ford, GM, Tesla, Rivian)
- Units produced / delivered
- ASP (average selling price)
- Gross margin by segment
- EV mix %

### Dealers (AutoNation, Lithia, CarMax)
- Units sold (new + used)
- Gross profit per unit (GPU)
- Store count
- F&I attach rates

### Auto parts aftermarket (O'Reilly, AutoZone, Advance)
- Comps
- Commercial (DIFM) mix %
- Store count

---

## Industrials — travel & transport

### Airlines (Delta, United, Southwest, American)
- Available seat miles (ASMs) — capacity
- Load factor
- RASM (revenue per ASM)
- CASM ex-fuel (cost per ASM)
- Premium revenue mix

### Hotels (Marriott, Hilton, Hyatt)
- RevPAR (revenue per available room)
- Occupancy + ADR decomposition
- Pipeline / unit growth
- Owned vs. franchised mix

### Cruises (Royal Caribbean, Carnival, Norwegian)
- Occupancy
- Net yield / per-diem
- Capacity (available lower berth days)
- Bookings visibility

---

## Healthcare services

### Hospital systems (HCA, Tenet, UHS)
- Admissions + adjusted admissions
- Same-facility revenue growth
- Payer mix (commercial vs. Medicare vs. Medicaid vs. uninsured)

### Retail clinics / services (CVS, Walgreens)
- Prescription volume (scripts)
- Front-store comps (for pharmacy-chain retail side)
- Health services revenue (for CVS, the Aetna + Caremark piece)

---

## Telecom

### Wireless (Verizon, AT&T, T-Mobile)
- Postpaid phone net adds
- Postpaid phone churn
- Postpaid ARPU
- Fixed wireless net adds (newer story)

---

## Energy — upstream, midstream, downstream

### E&P (upstream — Exxon, Chevron, EOG, Devon)
- Production (boe/d), oil vs. gas mix
- Realized prices (often vs. benchmark)
- Capex
- Free cash flow

### Refiners / downstream (Marathon, Valero, Phillips 66)
- Throughput
- Crack spreads / refining margins
- Utilization

---

## Consumer staples

### Packaged food (PepsiCo, Coca-Cola, Kraft Heinz, General Mills)
- Organic revenue growth — volume vs. price decomposition (big story
  since 2022)
- Segment-level margins
- Productivity / cost savings program progress

### Tobacco / alcohol (Altria, Philip Morris, Constellation)
- Volume trends by category
- Price/mix
- Smokeless / reduced-risk product share (for tobacco)

---

## Fitness / wellness / consumer services

### Gyms (Planet Fitness, Life Time)
- Member count
- Same-club revenue
- Net new clubs
- Average dues per member

### Beauty (Ulta, Estée Lauder, e.l.f.)
- Comps
- Prestige vs. mass mix
- Digital / international mix

---

## How to use this map

1. Identify the business the user's observation is about.
2. Look up the diagnostic KPIs here.
3. Use `search_kpis` with those concepts to find the actual KPI names in
   deepKPI for that specific company.
4. Pull 8-12 quarters.
5. When presenting, organize the numbers around *what each KPI tells you
   about the business*, not just a data table.

If the company spans multiple segments (e.g., Amazon = retail + AWS + ads),
pull diagnostic KPIs for each segment that matters to the user's thesis.
