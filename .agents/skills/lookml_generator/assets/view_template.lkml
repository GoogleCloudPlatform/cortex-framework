# LookML View Template for Cortex Data Product Tables
view: ${VIEW_NAME} {
  sql_table_name: `@{GCP_PROJECT_ID}.@{DATASET_ID}.${TABLE_NAME}` ;;

  # --- Primary Key ---
  dimension: pk_${PRIMARY_KEY} {
    primary_key: yes
    type: string
    sql: ${PRIMARY_KEY_SQL} ;;
    description: "Unique surrogate key identifying the record."
  }

  # --- Standard Dimensions ---
  ${DIMENSIONS}

  # --- Dimension Groups (Dates) ---
  ${DIMENSION_GROUPS}

  # --- Measures ---
  measure: count {
    type: count
    drill_fields: [detail*]
  }

  ${MEASURES}

  # --- Drill Set ---
  set: detail {
    fields: [
      pk_${PRIMARY_KEY}
    ]
  }
}
