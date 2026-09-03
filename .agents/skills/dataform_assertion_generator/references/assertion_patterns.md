# Dataform Assertion Patterns in Cortex Framework

This reference document outlines the standard assertion design patterns supported in Google Cloud Cortex Framework v7.

---

## 1. Core Assertion Concepts

In Google Cloud Dataform, an **assertion** is a query that checks for data quality issues.
* **Pass condition:** The assertion query returns `0` rows.
* **Fail condition:** The assertion query returns `1 or more` rows (these rows are treated as defect records).

---

## 2. Standard Pattern Library

### Pattern A: Multi-Column Composite Unique Key
Validates that composite primary keys (e.g., client, company code, document number, item number) are unique.

```sql
config {
  type: "assertion"
}

SELECT
  client_mandt,
  company_code_bukrs,
  accounting_document_belnr,
  fiscal_year_gjahr,
  line_item_buzei,
  COUNT(*) AS duplicate_instances
FROM
  ${ref("universal_journal_entry_line_items")}
GROUP BY
  client_mandt,
  company_code_bukrs,
  accounting_document_belnr,
  fiscal_year_gjahr,
  line_item_buzei
HAVING
  COUNT(*) > 1
```

---

### Pattern B: Non-Null Mandatory Attributes
Validates that essential business dimensions and foreign keys are never null.

```sql
config {
  type: "assertion"
}

SELECT
  *
FROM
  ${ref("sales_document_headers")}
WHERE
  client_mandt IS NULL
  OR document_number_vbeln IS NULL
  OR creation_date_erdat IS NULL
```

---

### Pattern C: Parent-Child Referential Integrity (Orphan Detection)
Validates that child line items have a corresponding parent document.

```sql
config {
  type: "assertion"
}

SELECT
  item.client_mandt,
  item.document_number_vbeln,
  item.item_number_posnr
FROM
  ${ref("sales_document_items")} AS item
LEFT JOIN
  ${ref("sales_document_headers")} AS header
  ON item.client_mandt = header.client_mandt
 AND item.document_number_vbeln = header.document_number_vbeln
WHERE
  header.document_number_vbeln IS NULL
```

---

### Pattern D: Financial Zero-Balance Ledger Reconciliation
In double-entry bookkeeping (SAP Universal Journal `ACDOCA`), the sum of debits and credits for any posted accounting document must equal zero.

```sql
config {
  type: "assertion"
}

SELECT
  client_mandt,
  company_code_bukrs,
  accounting_document_belnr,
  fiscal_year_gjahr,
  ledger_rldnr,
  ROUND(SUM(amount_in_company_code_currency_dmbtr), 2) AS ledger_imbalance
FROM
  ${ref("universal_journal_entry_line_items")}
GROUP BY
  client_mandt,
  company_code_bukrs,
  accounting_document_belnr,
  fiscal_year_gjahr,
  ledger_rldnr
HAVING
  ABS(ROUND(SUM(amount_in_company_code_currency_dmbtr), 2)) > 0.05
```
