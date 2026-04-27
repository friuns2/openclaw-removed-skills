---
emoji: 🧾
name: tally-prime
version: 0.1.0
author: Maxxit
description: Interact with TallyPrime running locally to read reports and post accounting entries. 
disableModelInvocation: false
requires:
  env:
    - TALLY_URL
metadata:
  openclaw:
    requiredEnv:
      - TALLY_URL
    bins:
      - curl
    primaryCredential: TALLY_URL
---

# TallyPrime Skill

Connect to a locally running TallyPrime instance and perform read/write operations via its XML-over-HTTP API. All requests are HTTP POST to `$TALLY_URL` (default: `http://localhost:9000`) with XML body.

> **TallyPrime must be open and running** on the user's machine. There is no cloud API — all communication is local.
>
> **Company name:** CAs manage multiple companies. Always get the company name from the user — either they'll mention it in their message, or ask them before proceeding. Never assume.

---

## Hero Use Case: WhatsApp Invoice → Tally Entry (Zero Manual Entry)

**The problem for CAs:** You manage 10+ businesses. A client sends a purchase bill PDF on WhatsApp. You have to open Tally, find the right company, check if the vendor ledger exists, create it if not, then manually type every field. This takes 5–10 minutes per invoice.

**With this skill:** Client sends the PDF to your OpenClaw WhatsApp number. The agent reads the invoice, extracts all fields, checks/creates the vendor ledger, and posts the purchase voucher — in under 30 seconds.

### Step-by-step Flow

```
1. Receive PDF/image of purchase invoice via WhatsApp
2. Extract invoice fields using vision (vendor name, GSTIN, date, line items, amounts, tax)
3. Switch to the correct Tally company (ask user if unclear)
4. Check if vendor ledger exists → create it if not (under Sundry Creditors)
5. Check if expense/purchase ledger exists → create if not
6. Check if GST ledger exists → create if not
7. Post Purchase voucher with all ledger entries
8. Confirm back to user with voucher number and summary
```

---

## When to Use This Skill

- User sends a purchase invoice, bill, or receipt (PDF or image) and wants it entered in Tally
- User asks to create a sales invoice / purchase bill / payment / receipt in Tally
- User wants to check outstanding receivables or payables
- User asks for a ledger statement, day book, or trial balance
- User wants to know their GST liability for a period
- User asks "what did we buy from X vendor last month?"
- User wants to add a new ledger or group in Tally
- User wants to check if Tally is running / connected
- User mentions "book this entry", "add to Tally", "post this bill"
- User wants to reconcile vendor invoices against Tally entries

---

## ⚠️ Critical Rules (Read Before Any Operation)

1. **Never guess ledger names.** Always check if a ledger exists before using it in a voucher. If it doesn't exist, create it first.
2. **Never assume the company name.** If the user mentions it (e.g., "for Reliance Industries" or "in ABC Traders"), use that exact name. If they don't mention it, ask: *"Which company should I post this to?"* before proceeding.
3. **Date format is `YYYYMMDD`** — no dashes or slashes. March 2, 2026 → `20260302`.
4. **Always include a unique `GUID`** when creating vouchers to prevent duplicates on retry.
5. **Amount sign convention:**
   - Party/vendor entry: `AMOUNT` is **negative** (e.g., `-50000`), `ISDEEMEDPOSITIVE` = `No` for creditors
   - Expense/purchase entry: `AMOUNT` is **positive** (e.g., `50000`), `ISDEEMEDPOSITIVE` = `No`
   - See the voucher section for exact signs per voucher type.
6. **`"Voucher date is missing"` error** = date is outside the company's configured financial year. Ask user to check Tally's company period settings.
7. **`"Ledger X does not exist"` error** = create the ledger first, then retry the voucher.
8. **For multi-company CAs:** Always confirm which company the entry belongs to before posting.

---

## Step 0: Check Server Status

Always verify Tally is running before any operation.

```bash
curl -s --max-time 5 "$TALLY_URL"
```

**Expected response:**
```
<RESPONSE>TallyPrime Server is Running</RESPONSE>
```

If connection is refused or times out, tell the user: *"TallyPrime doesn't seem to be running. Please open TallyPrime on your computer and try again."*

---

## Step 1: Check If a Ledger Exists

Before creating any voucher, verify all referenced ledgers exist.

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>List of Accounts</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>'
```

Parse the XML response and grep for `<NAME>LEDGER_NAME</NAME>` to confirm existence.

---

## Step 2: Create a Ledger (if missing)

Use `REPORTNAME=All Masters` for all master creation.

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>All Masters</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <LEDGER NAME="LEDGER_NAME" ACTION="Create">
            <NAME>LEDGER_NAME</NAME>
            <PARENT>PARENT_GROUP</PARENT>
            <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
          </LEDGER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>'
```

### Ledger Group Reference

| Ledger Type | Parent Group | ISDEEMEDPOSITIVE |
|---|---|---|
| Customer (debtor) | `Sundry Debtors` | `Yes` |
| Vendor (creditor) | `Sundry Creditors` | `No` |
| Sales income | `Sales Accounts` | `No` |
| Purchase expense | `Purchase Accounts` | `No` |
| Bank account | `Bank Accounts` | `Yes` |
| Cash | `Cash-in-Hand` | `Yes` |
| GST Output (sales tax) | `Duties & Taxes` | `No` |
| GST Input (purchase tax) | `Duties & Taxes` | `Yes` |
| Other expense | `Indirect Expenses` | `No` |
| Direct cost/COGS | `Direct Expenses` | `No` |

**Success response:**
```xml
<RESPONSE><CREATED>1</CREATED><ERRORS>0</ERRORS></RESPONSE>
```

---

## Step 3: Create Vouchers

Use `REPORTNAME=Vouchers` for all voucher creation.

### 3a. Purchase Voucher (Vendor Bill)

Use when: A vendor sends a bill/invoice for goods or services purchased.

**Accounting entry:**
- Debit: Purchase / Expense ledger (cost increases)
- Debit: GST Input Credit ledger (if GST applicable)
- Credit: Vendor ledger (liability increases)

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Purchase" ACTION="Create">
            <GUID>UNIQUE_GUID_HERE</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
            <VOUCHERNUMBER>INVOICE_NUMBER</VOUCHERNUMBER>
            <NARRATION>Purchase from VENDOR_NAME | Invoice: INVOICE_NUMBER</NARRATION>
            <ISINVOICE>Yes</ISINVOICE>
            <PARTYLEDGERNAME>VENDOR_LEDGER_NAME</PARTYLEDGERNAME>

            <!-- Debit: Purchase/Expense account -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>PURCHASE_LEDGER_NAME</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-BASE_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Debit: GST Input (if applicable, 18% example) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST Input Credit</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-GST_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Credit: Vendor (payable) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>VENDOR_LEDGER_NAME</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>TOTAL_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>'
```

> **Amount signs for Purchase voucher:**
> - Purchase/expense: `AMOUNT = -(base amount)` → e.g., `-42373`
> - GST Input: `AMOUNT = -(gst amount)` → e.g., `-7627`
> - Vendor (credit): `AMOUNT = +(total invoice amount)` → e.g., `50000`
> - All amounts must balance to zero.

### 3b. Sales Voucher (Customer Invoice)

Use when: Business raises an invoice to a customer for goods/services sold.

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Sales" ACTION="Create">
            <GUID>UNIQUE_GUID_HERE</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>
            <VOUCHERNUMBER>INVOICE_NUMBER</VOUCHERNUMBER>
            <NARRATION>Sales invoice to CUSTOMER_NAME</NARRATION>
            <ISINVOICE>Yes</ISINVOICE>
            <PARTYLEDGERNAME>CUSTOMER_LEDGER_NAME</PARTYLEDGERNAME>

            <!-- Debit: Customer (receivable) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>CUSTOMER_LEDGER_NAME</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-TOTAL_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Credit: Sales account -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>SALES_LEDGER_NAME</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>BASE_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Credit: GST Output (if applicable) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST Output</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>GST_AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>'
```

### 3c. Payment Voucher (Money Paid Out)

Use when: Business pays a vendor, rent, salary, or any expense.

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Payment" ACTION="Create">
            <GUID>UNIQUE_GUID_HERE</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
            <NARRATION>Payment to PAYEE_NAME</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <PARTYLEDGERNAME>PAYEE_LEDGER_NAME</PARTYLEDGERNAME>

            <!-- Debit: Who is being paid -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>PAYEE_LEDGER_NAME</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Credit: Bank / Cash (source of payment) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>BANK_OR_CASH_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>'
```

### 3d. Receipt Voucher (Money Received)

Use when: Business receives money from a customer.

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Receipt" ACTION="Create">
            <GUID>UNIQUE_GUID_HERE</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Receipt</VOUCHERTYPENAME>
            <NARRATION>Receipt from CUSTOMER_NAME</NARRATION>
            <ISINVOICE>No</ISINVOICE>
            <PARTYLEDGERNAME>CUSTOMER_LEDGER_NAME</PARTYLEDGERNAME>

            <!-- Debit: Bank / Cash (destination) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>BANK_OR_CASH_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Credit: Customer ledger (reduces receivable) -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>CUSTOMER_LEDGER_NAME</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>'
```

### 3e. Journal Voucher (Adjustments / Provisions)

Use when: GST adjustments, provisions, depreciation, accruals, or any internal accounting entry.

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Journal" ACTION="Create">
            <GUID>UNIQUE_GUID_HERE</GUID>
            <DATE>YYYYMMDD</DATE>
            <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>
            <NARRATION>NARRATION_TEXT</NARRATION>
            <ISINVOICE>No</ISINVOICE>

            <!-- Debit entry -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>DEBIT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <!-- Credit entry -->
            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>CREDIT_LEDGER</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>AMOUNT</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>'
```

---

## Reading Data (Export Operations)

### Get Day Book (All Transactions for a Period)

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Day Book</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
          <SVFROMDATE>FROM_DATE_YYYYMMDD</SVFROMDATE>
          <SVTODATE>TO_DATE_YYYYMMDD</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>'
```

### Get Balance Sheet

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Balance Sheet</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>'
```

### Get Trial Balance

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Trial Balance</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
          <SVFROMDATE>FROM_DATE_YYYYMMDD</SVFROMDATE>
          <SVTODATE>TO_DATE_YYYYMMDD</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>'
```

### Get Ledger Statement (Transactions for a Specific Ledger)

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Export Data</TALLYREQUEST></HEADER>
  <BODY>
    <EXPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Ledger Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVEXPORTFORMAT>$$SysName:XML</SVEXPORTFORMAT>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
          <SVLEDGERNAME>LEDGER_NAME</SVLEDGERNAME>
          <SVFROMDATE>FROM_DATE_YYYYMMDD</SVFROMDATE>
          <SVTODATE>TO_DATE_YYYYMMDD</SVTODATE>
        </STATICVARIABLES>
      </REQUESTDESC>
    </EXPORTDATA>
  </BODY>
</ENVELOPE>'
```

---

## Full Example: WhatsApp Purchase Invoice → Tally

**Scenario:** Client sends a PDF invoice from "Reliance Retail Ltd." for ₹59,000 (₹50,000 base + ₹9,000 GST @ 18%), dated 15-Jan-2026, invoice no. RRL/2026/00123.

### Step 1 — Extract from PDF/Image

Use your vision capability to extract:

```
Vendor: Reliance Retail Ltd.
Vendor GSTIN: 27AABCR1234A1Z5
Invoice No: RRL/2026/00123
Date: 15-Jan-2026 → 20260115
Base Amount: ₹50,000
GST (18%): ₹9,000
Total: ₹59,000
Description: Office Supplies
```

### Step 2 — Check & Create Ledgers

Check if these 3 ledgers exist. Create any that are missing:

| Ledger | Group | Action |
|---|---|---|
| `Reliance Retail Ltd.` | `Sundry Creditors` | Create if missing |
| `Office Supplies` | `Purchase Accounts` | Create if missing |
| `GST Input Credit` | `Duties & Taxes` | Create if missing |

### Step 3 — Post Purchase Voucher

```bash
curl -s -X POST "$TALLY_URL" \
  -H "Content-Type: application/xml" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<ENVELOPE>
  <HEADER><TALLYREQUEST>Import Data</TALLYREQUEST></HEADER>
  <BODY>
    <IMPORTDATA>
      <REQUESTDESC>
        <REPORTNAME>Vouchers</REPORTNAME>
        <STATICVARIABLES>
          <SVCURRENTCOMPANY>COMPANY_NAME</SVCURRENTCOMPANY>
        </STATICVARIABLES>
      </REQUESTDESC>
      <REQUESTDATA>
        <TALLYMESSAGE xmlns:UDF="TallyUDF">
          <VOUCHER VCHTYPE="Purchase" ACTION="Create">
            <GUID>rrl-2026-00123-purchase</GUID>
            <DATE>20260115</DATE>
            <VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>
            <VOUCHERNUMBER>RRL/2026/00123</VOUCHERNUMBER>
            <NARRATION>Purchase from Reliance Retail Ltd. | Invoice: RRL/2026/00123 | Office Supplies</NARRATION>
            <ISINVOICE>Yes</ISINVOICE>
            <PARTYLEDGERNAME>Reliance Retail Ltd.</PARTYLEDGERNAME>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Office Supplies</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-50000</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>GST Input Credit</LEDGERNAME>
              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
              <AMOUNT>-9000</AMOUNT>
            </ALLLEDGERENTRIES.LIST>

            <ALLLEDGERENTRIES.LIST>
              <LEDGERNAME>Reliance Retail Ltd.</LEDGERNAME>
              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
              <AMOUNT>59000</AMOUNT>
            </ALLLEDGERENTRIES.LIST>
          </VOUCHER>
        </TALLYMESSAGE>
      </REQUESTDATA>
    </IMPORTDATA>
  </BODY>
</ENVELOPE>'
```

### Step 4 — Confirm to User

On success (`CREATED=1`), reply:

> ✅ **Purchase entry booked in Tally**
>
> | Field | Value |
> |---|---|
> | Company | *(as confirmed by user)* |
> | Vendor | Reliance Retail Ltd. |
> | Invoice No | RRL/2026/00123 |
> | Date | 15 Jan 2026 |
> | Base Amount | ₹50,000 |
> | GST (18%) | ₹9,000 |
> | **Total** | **₹59,000** |
>
> The vendor ledger "Reliance Retail Ltd." was created under Sundry Creditors.

---

## Error Handling

| Error Message | Cause | Fix |
|---|---|---|
| `TallyPrime Server is Running` not returned | Tally not open | Tell user to open TallyPrime |
| `Ledger 'X' does not exist` | Ledger missing | Create it via Step 2, then retry |
| `Voucher date is missing` | Date outside company's FY | Ask user: "What financial year is configured in your Tally company?" |
| `The date X is Out of Range` | Same as above | Same fix |
| `Could not find Report 'X'` | Wrong report name | Use exact report names from this skill |
| `CREATED=0, EXCEPTIONS=1` | Generic data error | Check narration for special characters — escape `&` as `&amp;` |

---

## GUID Generation

Always generate a unique GUID per voucher to prevent duplicates. A good pattern:

```
{company-short}-{voucher-type}-{invoice-number}-{date}
```

Examples:
- `ape-purchase-rrl202600123-20260115`
- `ape-sales-si001-20260302`
- `ape-payment-hdfc-20260115`

If the same GUID is sent twice, Tally will update the existing record instead of creating a duplicate — this makes the operation safely idempotent.

---

## Multi-Company Workflow for CA Firms

CAs typically manage 10–50+ companies in a single Tally installation. Handle company context like this:

1. **If the user mentions the company** (e.g., "for Sharma Traders" or "in my textile client's books") — use that name directly as `SVCURRENTCOMPANY` in the XML.
2. **If the user doesn't mention it** — always ask before posting: *"Which company should I book this in?"* Never assume.
3. **After posting** — always confirm the company name in your reply so the user can catch any mistakes.
4. **If unsure about the exact Tally company name** — you can fetch all available company names by querying `List of Accounts` without a `SVCURRENTCOMPANY` filter, or simply ask the user to confirm the exact spelling as it appears in Tally.

> **Note:** The company name in `SVCURRENTCOMPANY` must match *exactly* (case-sensitive) how it appears in Tally. Even a trailing space or different capitalisation will cause the request to fail silently or return data from the wrong company.
