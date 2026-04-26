# Error Codes and Troubleshooting

## Pangolinfo API Error Codes

| Code | Meaning | Resolution |
|------|---------|------------|
| 0 | Success | No action needed |
| 1004 | Invalid token | Auto-retried by script |
| 1009 | Invalid parser name | Check `--parser` value |
| 2001 | Insufficient credits | Top up at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_amz) |
| 2005 | No active plan | Subscribe at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_amz) |
| 2007 | Account expired | Renew at [pangolinfo.com](https://pangolinfo.com/?referrer=clawhub_amz) |
| 2009 | Usage limit reached | Wait for next billing cycle or contact support |
| 2010 | Bill day not configured | Contact support |
| 4029 | Rate limited | Reduce request frequency |
| 10000 | Task execution failed | Retry. Check query/URL format. |
| 10001 | Task execution failed | Retry. Likely transient. |

## Authentication

- Tokens are **permanent** (don't expire unless account deactivated)
- Error code `1004` triggers automatic token refresh
- Resolution order: `PANGOLINFO_API_KEY` env > `~/.pangolinfo_api_key` cache > fresh login

## Credit Costs

| Operation | Credits |
|---|---|
| Amazon scrape (json) | 1 |
| Amazon scrape (rawHtml/markdown) | 0.75 |
| Follow Seller | 1 |
| Variant ASIN | 1 |
| Review page | 5 per page |

Credits consumed on success (code 0) only.

## Common Issues

**"No authentication credentials" error** -- Set `PANGOLINFO_API_KEY` env var.

**Empty results** -- Check ASIN/keyword spelling, try different region.

**Timeout errors** -- Script retries 3x with exponential backoff. Check network.

**Reviews returning empty** -- Not all products have reviews. Try `--filter-star all_stars`.
