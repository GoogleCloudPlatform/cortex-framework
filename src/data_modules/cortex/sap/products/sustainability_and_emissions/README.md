# SAP Sustainability & Carbon Emissions Data Product

## Overview
The **SAP Sustainability & Carbon Emissions** (`sustainability_and_emissions`) data product provides automated, auditable calculations of corporate greenhouse gas (GHG) emissions directly from **SAP S/4HANA** enterprise operations.

Designed to fulfill the rigorous audit requirements of the **EU Corporate Sustainability Due Diligence Directive (CSDDD)**, **Corporate Sustainability Reporting Directive (CSRD)**, and the **SEC Climate Disclosure Rules**, this data product integrates SAP Purchasing (`EKKO`, `EKPO`), Material Management (`MARA`), Supplier Master (`LFA1`), and Universal Material Movements (`MATDOC`, `T001W`).

---

## Analytical Models

### 1. `procurement_carbon_footprint` (Scope 3 Category 1)
- **Standard:** GHG Protocol Corporate Value Chain (Scope 3) Standard.
- **Grain:** `client_mandt`, `purchase_order_ebeln`, `purchase_order_item_ebelp`.
- **Methodology:** Combines spend-based emission factors ($kg CO_2e / \$$) and mass-based factors ($kg CO_2e / kg$) across supplier commodities and material groups.

### 2. `plant_logistics_emissions` (Scope 1 & Scope 3 Category 4)
- **Standard:** GLEC Framework / ISO 14083 freight emissions standards.
- **Grain:** `client_mandt`, `material_document_mblnr`, `material_year_mjahr`, `document_item_zeile`.
- **Methodology:** Converts universal material movements into metric tons and computes transport emission footprints for inter-plant transfers and plant goods issues.
