# SAP Financial Audit & Compliance Data Product

The **Financial Audit & Compliance** data product provides automated general ledger reconciliation and forensic journal anomaly detection for SAP S/4HANA financial environments in BigQuery.

---

## Overview

Enterprise financial audits require continuous reconciliation of general ledger balances and rapid detection of high-risk journal entries. This data product transforms raw SAP `ACDOCA`, `BKPF`, and `BSEG` transactions into AI-ready, audit-compliant analytical tables.

### Key Capabilities
* **Automated Ledger Reconciliation:** Calculates net ledger balance per document, verifying that total debits equal total credits with exact `TCURX` decimal shifting.
* **Forensic Anomaly Detection:** Flags suspicious transactions based on SOX compliance rules:
  - Weekend or off-hours manual postings.
  - Large round-dollar manual entries ($\ge \$10,000$).
  - Entries missing external reference documentation.
  - Backdated or forward-dated transactions (> 30-day posting discrepancy).

---

## Data Models

| Table Name | Description | Source SAP Tables |
| :--- | :--- | :--- |
| `financial_ledger_reconciliation` | Reconciles debits and credits across SAP S/4HANA Universal Journal line items. | `ACDOCA`, `TCURX` |
| `suspicious_journal_entries` | Identifies anomalous journal entries with forensic accounting flags. | `BKPF`, `BSEG`, `TCURX` |

---

## Deployment & Configuration

Configure this product in `config/config.yaml` under `data.products`:

```yaml
data:
  products:
    - namespace: cortex
      source: sap
      type: financial_audit_and_compliance
      target: product_target
```
