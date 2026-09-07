/**
 * Copyright 2026 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

// ___MODULE_CONTEXT___
// ___TABLE_CONFIG___

const moduleConfig = config.product[moduleContext.moduleId];
const materializationType = tableConfig.materializationType || "incremental";
const date = require("includes/date.js");
const incremental = require("includes/incremental.js");
const publish_config = require("includes/publish_config.js");
const sql_helper = require("includes/sql_helper.js");

const publishConfig = publish_config.getPublishConfig(
  materializationType,
  tableConfig,
  moduleConfig,
  [
    "client_mandt",
    "material_document_mblnr",
    "material_year_mjahr",
    "document_item_zeile"
  ]
);

publish(moduleContext.moduleId + "_" + tableConfig.tableName, publishConfig).query(
  (ctx) => `
WITH date_dimension AS (
  ${date.getDateDimension()}
),
matdoc_movements AS (
  SELECT
    matdoc.mandt AS client_mandt,
    matdoc.mblnr AS material_document_mblnr,
    matdoc.mjahr AS material_year_mjahr,
    matdoc.zeile AS document_item_zeile,
    matdoc.bwart AS movement_type_bwart,
    matdoc.matnr AS material_number_matnr,
    matdoc.werks AS source_plant_werks,
    t_source.name1 AS source_plant_name,
    t_source.land1 AS source_country_land1,
    matdoc.lgort AS storage_location_lgort,
    matdoc.umwrk AS receiving_plant_umwrk,
    t_dest.name1 AS receiving_plant_name,
    t_dest.land1 AS receiving_country_land1,
    matdoc.umlgo AS receiving_storage_location_umlgo,
    matdoc.shkzg AS debit_credit_shkzg,
    matdoc.budat AS posting_date_budat,
    matdoc.cpudt AS entry_date_cpudt,
    matdoc.usnam AS entered_by_usnam,
    matdoc.menge AS quantity_menge,
    matdoc.meins AS base_unit_meins,
    COALESCE(mara.brgew, 0.0) AS item_gross_weight_brgew,
    COALESCE(mara.gewei, 'KG') AS weight_unit_gewei
  FROM
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "matdoc")} AS matdoc
  LEFT JOIN
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "mara")} AS mara
    ON matdoc.mandt = mara.mandt AND matdoc.matnr = mara.matnr
  LEFT JOIN
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "t001w")} AS t_source
    ON matdoc.mandt = t_source.mandt AND matdoc.werks = t_source.werks
  LEFT JOIN
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "t001w")} AS t_dest
    ON matdoc.mandt = t_dest.mandt AND matdoc.umwrk = t_dest.werks
  ${incremental.filter(materializationType, "matdoc.recordstamp")}
),
logistics_carbon AS (
  SELECT
    client_mandt,
    material_document_mblnr,
    material_year_mjahr,
    document_item_zeile,
    movement_type_bwart,
    material_number_matnr,
    source_plant_werks,
    source_plant_name,
    source_country_land1,
    storage_location_lgort,
    receiving_plant_umwrk,
    receiving_plant_name,
    receiving_country_land1,
    receiving_storage_location_umlgo,
    debit_credit_shkzg,
    posting_date_budat,
    entry_date_cpudt,
    entered_by_usnam,
    quantity_menge,
    base_unit_meins,
    item_gross_weight_brgew,
    weight_unit_gewei,
    ROUND((quantity_menge * COALESCE(item_gross_weight_brgew, 1.0)) / 1000.0, 3) AS total_weight_metric_tons,
    CASE
      WHEN receiving_plant_umwrk IS NOT NULL AND receiving_plant_umwrk != source_plant_werks THEN TRUE
      ELSE FALSE
    END AS is_interplant_transfer,
    CASE
      WHEN receiving_plant_umwrk IS NOT NULL AND receiving_plant_umwrk != source_plant_werks THEN 'SCOPE_3_CATEGORY_4_UPSTREAM_TRANSPORT'
      WHEN movement_type_bwart IN ('201', '261') THEN 'SCOPE_1_INTERNAL_OPERATIONS'
      ELSE 'SCOPE_3_OTHER_MOVEMENTS'
    END AS ghg_scope_boundary,
    ROUND(
      ((quantity_menge * COALESCE(item_gross_weight_brgew, 1.0)) / 1000.0) *
      CASE
        WHEN receiving_plant_umwrk IS NOT NULL AND receiving_plant_umwrk != source_plant_werks THEN 14.5
        ELSE 4.2
      END,
      2
    ) AS estimated_logistics_emissions_kg_co2e
  FROM
    matdoc_movements
)
SELECT
  client_mandt,
  material_document_mblnr,
  material_year_mjahr,
  document_item_zeile,
  movement_type_bwart,
  material_number_matnr,
  source_plant_werks,
  source_plant_name,
  source_country_land1,
  storage_location_lgort,
  receiving_plant_umwrk,
  receiving_plant_name,
  receiving_country_land1,
  receiving_storage_location_umlgo,
  debit_credit_shkzg,
  posting_date_budat,
  entry_date_cpudt,
  entered_by_usnam,
  quantity_menge,
  base_unit_meins,
  item_gross_weight_brgew,
  weight_unit_gewei,
  total_weight_metric_tons,
  is_interplant_transfer,
  ghg_scope_boundary,
  estimated_logistics_emissions_kg_co2e
FROM
  logistics_carbon
`
);
