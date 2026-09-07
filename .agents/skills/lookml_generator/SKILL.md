---
name: lookml-generator
description: Automatically generates production-ready LookML views, dimensions, measures, and explores for Looker and BigQuery from Google Cloud Cortex Framework v7 data product annotations, manifests, and Dataform models.
---

# LookML Generator Skill

This skill guides the AI assistant in transforming Google Cloud Cortex Framework v7 data products into production-ready **Looker LookML** assets (`views/*.view.lkml` and `models/*.model.lkml`).

## Workflow Overview

When a user requests LookML generation (or triggers `/generate-lookml`):

1. **Discover Data Product Metadata:**
   - Locate the target product under `src/data_modules/cortex/<domain>/products/<product_name>/`.
   - Read `manifest.yaml` to identify product type, display name, and dependencies.
   - Inspect `table_settings.default.yaml` for table names and materialization keys.
   - Read field definitions from `annotations/<version>/<table_name>.yaml`.

2. **Map Fields to LookML Dimensions:**
   - Consult [lookml_patterns.md](references/lookml_patterns.md) for standard type mappings.
   - Identify Primary Keys: Set `primary_key: yes` for designated grain keys (e.g. `client_mandt`, `document_number_belnr`, etc.).
   - Identify Dates/Timestamps: Convert SAP date suffixes (`_budat`, `_bldat`, `_bedat`, `_cpudt`) into `dimension_group` blocks with standard timeframes: `[raw, date, week, month, quarter, year]`.
   - String & Code Fields: Map to standard `type: string` with field descriptions from the YAML annotations.

3. **Generate Analytical Measures:**
   - Always include a baseline record counter:
     ```lookml
     measure: count {
       type: count
       drill_fields: [detail*]
     }
     ```
   - Identify Monetary and Amount Fields (e.g. `amount`, `netwr`, `dmbtr`, `emissions`):
     - Generate `type: sum` with `value_format_name: usd` or appropriate decimal scaling.
     - Generate `type: average` where relevant for operational analysis.

4. **Construct Star-Schema Explores:**
   - Create or update the LookML model file (`cortex_analytics.model.lkml`).
   - Define explores joining transaction tables (e.g. `procurement_carbon_footprint`, `financial_ledger_reconciliation`) to master data dimensions (`supplier`, `plant`, `company_code`).

5. **Output Generation:**
   - Leverage [view_template.lkml](assets/view_template.lkml) as the foundational boilerplate.
   - Save generated view files to `looker/views/<product_name>/<table_name>.view.lkml`.
   - Provide the user with a summary of generated LookML files and explore join graphs.
