---
name: lap-account-api
description: "Account API skill. Use when working with Account for checkAccountHolder, closeAccount, closeAccountHolder. Covers 20 endpoints."
version: 1.0.0
generator: lapsh
metadata:
  openclaw:
    requires:
      env:
        - ACCOUNT_API_KEY
---

# Account API
API version: 6

## Auth
ApiKey X-API-Key in header | Bearer basic

## Base URL
https://cal-test.adyen.com/cal/services/Account/v6

## Setup
1. Set Authorization header with your Bearer token
3. POST /checkAccountHolder -- create first checkAccountHolder

## Endpoints

20 endpoints across 20 groups. See references/api-spec.lap for full details.

### checkAccountHolder
| Method | Path | Description |
|--------|------|-------------|
| POST | /checkAccountHolder | Trigger verification |

### closeAccount
| Method | Path | Description |
|--------|------|-------------|
| POST | /closeAccount | Close an account |

### closeAccountHolder
| Method | Path | Description |
|--------|------|-------------|
| POST | /closeAccountHolder | Close an account holder |

### closeStores
| Method | Path | Description |
|--------|------|-------------|
| POST | /closeStores | Close stores |

### createAccount
| Method | Path | Description |
|--------|------|-------------|
| POST | /createAccount | Create an account |

### createAccountHolder
| Method | Path | Description |
|--------|------|-------------|
| POST | /createAccountHolder | Create an account holder |

### deleteBankAccounts
| Method | Path | Description |
|--------|------|-------------|
| POST | /deleteBankAccounts | Delete bank accounts |

### deleteLegalArrangements
| Method | Path | Description |
|--------|------|-------------|
| POST | /deleteLegalArrangements | Delete legal arrangements |

### deletePayoutMethods
| Method | Path | Description |
|--------|------|-------------|
| POST | /deletePayoutMethods | Delete payout methods |

### deleteShareholders
| Method | Path | Description |
|--------|------|-------------|
| POST | /deleteShareholders | Delete shareholders |

### deleteSignatories
| Method | Path | Description |
|--------|------|-------------|
| POST | /deleteSignatories | Delete signatories |

### getAccountHolder
| Method | Path | Description |
|--------|------|-------------|
| POST | /getAccountHolder | Get an account holder |

### getTaxForm
| Method | Path | Description |
|--------|------|-------------|
| POST | /getTaxForm | Get a tax form |

### getUploadedDocuments
| Method | Path | Description |
|--------|------|-------------|
| POST | /getUploadedDocuments | Get documents |

### suspendAccountHolder
| Method | Path | Description |
|--------|------|-------------|
| POST | /suspendAccountHolder | Suspend an account holder |

### unSuspendAccountHolder
| Method | Path | Description |
|--------|------|-------------|
| POST | /unSuspendAccountHolder | Unsuspend an account holder |

### updateAccount
| Method | Path | Description |
|--------|------|-------------|
| POST | /updateAccount | Update an account |

### updateAccountHolder
| Method | Path | Description |
|--------|------|-------------|
| POST | /updateAccountHolder | Update an account holder |

### updateAccountHolderState
| Method | Path | Description |
|--------|------|-------------|
| POST | /updateAccountHolderState | Update payout or processing state |

### uploadDocument
| Method | Path | Description |
|--------|------|-------------|
| POST | /uploadDocument | Upload a document |

## Common Questions

Match user requests to endpoints in references/api-spec.lap. Key patterns:
- "Create a checkAccountHolder?" -> POST /checkAccountHolder
- "Create a closeAccount?" -> POST /closeAccount
- "Create a closeAccountHolder?" -> POST /closeAccountHolder
- "Create a closeStore?" -> POST /closeStores
- "Create a createAccount?" -> POST /createAccount
- "Create a createAccountHolder?" -> POST /createAccountHolder
- "Create a deleteBankAccount?" -> POST /deleteBankAccounts
- "Create a deleteLegalArrangement?" -> POST /deleteLegalArrangements
- "Create a deletePayoutMethod?" -> POST /deletePayoutMethods
- "Create a deleteShareholder?" -> POST /deleteShareholders
- "Create a deleteSignatory?" -> POST /deleteSignatories
- "Create a getAccountHolder?" -> POST /getAccountHolder
- "Create a getTaxForm?" -> POST /getTaxForm
- "Create a getUploadedDocument?" -> POST /getUploadedDocuments
- "Create a suspendAccountHolder?" -> POST /suspendAccountHolder
- "Create a unSuspendAccountHolder?" -> POST /unSuspendAccountHolder
- "Create a updateAccount?" -> POST /updateAccount
- "Create a updateAccountHolder?" -> POST /updateAccountHolder
- "Create a updateAccountHolderState?" -> POST /updateAccountHolderState
- "Create a uploadDocument?" -> POST /uploadDocument
- "How to authenticate?" -> See Auth section

## Response Tips
- Check response schemas in references/api-spec.lap for field details
- Create/update endpoints typically return the created/updated object

## CLI

```bash
# Update this spec to the latest version
npx @lap-platform/lapsh get account-api -o references/api-spec.lap

# Search for related APIs
npx @lap-platform/lapsh search account-api
```

## References
- Full spec: See references/api-spec.lap for complete endpoint details, parameter tables, and response schemas

> Generated from the official API spec by [LAP](https://lap.sh)
