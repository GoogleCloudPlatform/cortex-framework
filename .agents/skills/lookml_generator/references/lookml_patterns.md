# LookML Design Patterns for Cortex Framework

## 1. Type Mapping Matrix

| BigQuery / SAP Semantic Type | LookML Element | Example LookML Syntax |
| :--- | :--- | :--- |
| Primary Key | `dimension` | `primary_key: yes` |
| Text / Code (`CHAR`, `STRING`) | `dimension` | `type: string` |
| Integer / Quantity (`INT64`, `NUMERIC`) | `dimension` | `type: number` |
| Boolean (`BOOLEAN`, `FLAG`) | `dimension` | `type: yesno` |
| Date (`DATE`) | `dimension_group` | `type: time, timeframes: [date, month, quarter, year]` |
| Timestamp (`TIMESTAMP`) | `dimension_group` | `type: time, timeframes: [raw, time, date, week, month]` |
| Monetary Amount | `measure` | `type: sum, value_format_name: usd` |
| Carbon Emissions ($kg CO_2e$) | `measure` | `type: sum, value_format: "#,##0.00 "kg CO2e""` |

## 2. Standard View Structure

```lookml
view: procurement_carbon_footprint {
  sql_table_name: `@{GCP_PROJECT_ID}.@{DATASET_ID}.sustainability_and_emissions_procurement_carbon_footprint` ;;

  dimension: purchase_order_key {
    primary_key: yes
    type: string
    sql: CONCAT(${TABLE}.client_mandt, '-', ${TABLE}.purchase_order_ebeln, '-', CAST(${TABLE}.purchase_order_item_ebelp AS STRING)) ;;
  }

  dimension_group: purchasing_document {
    type: time
    timeframes: [raw, date, week, month, quarter, year]
    convert_tz: no
    datatype: date
    sql: ${TABLE}.purchasing_document_date_bedat ;;
  }

  measure: total_estimated_ghg_emissions {
    type: sum
    sql: ${TABLE}.total_estimated_ghg_emissions_kg_co2e ;;
    value_format: "#,##0.00 \"kg CO2e\""
  }
}
```
