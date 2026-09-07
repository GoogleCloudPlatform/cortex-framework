---
name: dataform-assertion-generator
description: Inspects Cortex Framework data products and scaffolds Dataform data quality and business integrity assertions including primary key uniqueness, non-null checks, foreign key referential integrity, and ledger reconciliation checks.
---

# Dataform Assertion Generator Skill

This skill guides the inspection, design, scaffolding, and validation of automated Dataform data quality and integrity assertions for Cortex Framework V7 data products.

---

## Operational Rules & Quality Gates

1. **Assertion Contract:** In Dataform, an assertion query is considered **failing** if it returns one or more rows. All assertion SQL queries MUST be authored such that they return zero rows when the data is valid and return violating rows when data integrity is breached.
2. **Namespace Isolation:** Never hardcode dataset or table names. Always resolve references dynamically using `ctx.ref(moduleConfig.sources.<source_module>.datasetId, "<table_name>")` or `${ref("<table_name>")}`.
3. **Link Integrity:** All relative markdown links referenced in this skill must resolve to real files on disk.
4. **Custom Overrides First:** Check the `custom/` folder before generating assertions. If project-specific compliance rules or custom thresholds exist, merge and prioritize them.

---

## Workflow Steps

### Step 1: Target Product & Key Identification
1. Read the target data product's `manifest.yaml` and `table_settings.default.yaml` under `src/data_modules/<namespace>/<source>/products/<product_name>/`.
2. Inspect the table definitions in `definitions/` to identify:
   - Primary key candidate columns (e.g. `client_mandt`, `document_number_vbeln`, `item_number_posnr`).
   - Critical non-nullable columns (e.g. `creation_date`, `currency_key`, `amount`).
   - Foreign key relationship bounds (e.g. line items pointing to existing header records).
   - Domain-specific financial/accounting invariants (e.g. total debits equal total credits).

### Step 2: Scaffold Assertion Definitions
Select the appropriate assertion pattern based on the target validation rule (refer to [assertion_patterns.md](references/assertion_patterns.md)):

1. **Unique Key Constraint Assertion:**
   Checks that candidate primary keys are unique across the dataset.
2. **Non-Null Invariant Assertion:**
   Ensures mandatory business fields are never null.
3. **Referential Integrity (Orphan Detection) Assertion:**
   Detects child line items that reference non-existent parent headers.
4. **Financial Invariant (Ledger Balance) Assertion:**
   Verifies that total ledger debits and credits balance to zero per fiscal period.

### Step 3: Write Assertion Files
Save generated assertions into `src/data_modules/<namespace>/<source>/products/<product_name>/definitions/assertions/` or the appropriate Dataform definitions directory. Use the `.sqlx` template from [assertion_template.sqlx](assets/assertion_template.sqlx).

### Step 4: Verification & Validation Gate
1. Validate the syntax of generated assertions against BigQuery ZetaSQL dialect.
2. Run unit tests to confirm manifest and dependency integrity:
   ```bash
   uv run pytest tests/external/common/validation/ -q
   ```
