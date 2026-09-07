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
const currency = require("includes/currency.js");
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
    "purchase_order_ebeln",
    "purchase_order_item_ebelp"
  ]
);

publish(moduleContext.moduleId + "_" + tableConfig.tableName, publishConfig).query(
  (ctx) => `
WITH date_dimension AS (
  ${date.getDateDimension()}
),
currency_decimal AS (
  ${currency.currencyDecimalShift(ctx.ref(moduleConfig.sources.sapModule.datasetId, "tcurx"))}
),
po_items_enriched AS (
  SELECT
    ekpo.mandt AS client_mandt,
    ekpo.ebeln AS purchase_order_ebeln,
    ekpo.ebelp AS purchase_order_item_ebelp,
    ekko.bukrs AS company_code_bukrs,
    ekko.ekorg AS purchasing_organization_ekorg,
    ekko.ekgrp AS purchasing_group_ekgrp,
    ekko.lifnr AS supplier_lifnr,
    lfa1.name1 AS supplier_name_name1,
    lfa1.land1 AS supplier_country_land1,
    ekko.bedat AS purchasing_document_date_bedat,
    ekko.waers AS currency_key_waers,
    ekpo.matnr AS material_number_matnr,
    ekpo.txz01 AS short_text_txz01,
    ekpo.matkl AS material_group_matkl,
    ekpo.werks AS plant_werks,
    ekpo.menge AS order_quantity_menge,
    ekpo.meins AS order_unit_meins,
    ekpo.netpr * COALESCE(curr.currfix, 1.0) AS net_price_netpr,
    ekpo.netwr * COALESCE(curr.currfix, 1.0) AS net_order_value_netwr,
    COALESCE(mara.brgew, ekpo.brgew, 0.0) AS gross_weight_brgew,
    COALESCE(mara.ntgew, ekpo.ntgew, 0.0) AS net_weight_ntgew,
    COALESCE(mara.gewei, ekpo.gewei, 'KG') AS weight_unit_gewei
  FROM
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "ekpo")} AS ekpo
  INNER JOIN
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "ekko")} AS ekko
    ON ekpo.mandt = ekko.mandt AND ekpo.ebeln = ekko.ebeln
  LEFT JOIN
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "lfa1")} AS lfa1
    ON ekko.mandt = lfa1.mandt AND ekko.lifnr = lfa1.lifnr
  LEFT JOIN
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "mara")} AS mara
    ON ekpo.mandt = mara.mandt AND ekpo.matnr = mara.matnr
  LEFT JOIN
    currency_decimal AS curr
    ON ekko.waers = curr.currkey
  ${incremental.filter(materializationType, "ekpo.recordstamp")}
),
carbon_calculated AS (
  SELECT
    client_mandt,
    purchase_order_ebeln,
    purchase_order_item_ebelp,
    company_code_bukrs,
    purchasing_organization_ekorg,
    purchasing_group_ekgrp,
    supplier_lifnr,
    supplier_name_name1,
    supplier_country_land1,
    purchasing_document_date_bedat,
    currency_key_waers,
    material_number_matnr,
    short_text_txz01,
    material_group_matkl,
    plant_werks,
    order_quantity_menge,
    order_unit_meins,
    net_price_netpr,
    net_order_value_netwr,
    net_weight_ntgew,
    weight_unit_gewei,
    ROUND(net_order_value_netwr * 0.38, 2) AS spend_based_emissions_kg_co2e,
    ROUND((order_quantity_menge * COALESCE(net_weight_ntgew, 1.0)) * 1.85, 2) AS mass_based_emissions_kg_co2e,
    ROUND((net_order_value_netwr * 0.38) + ((order_quantity_menge * COALESCE(net_weight_ntgew, 1.0)) * 1.85), 2) AS total_estimated_ghg_emissions_kg_co2e,
    CASE
      WHEN ((net_order_value_netwr * 0.38) + ((order_quantity_menge * COALESCE(net_weight_ntgew, 1.0)) * 1.85)) >= 1000.0 THEN 'HIGH_CARBON_INTENSIVE'
      WHEN ((net_order_value_netwr * 0.38) + ((order_quantity_menge * COALESCE(net_weight_ntgew, 1.0)) * 1.85)) >= 200.0 THEN 'MEDIUM_CARBON_INTENSIVE'
      ELSE 'LOW_CARBON_INTENSIVE'
    END AS carbon_intensity_classification
  FROM
    po_items_enriched
)
SELECT
  client_mandt,
  purchase_order_ebeln,
  purchase_order_item_ebelp,
  company_code_bukrs,
  purchasing_organization_ekorg,
  purchasing_group_ekgrp,
  supplier_lifnr,
  supplier_name_name1,
  supplier_country_land1,
  purchasing_document_date_bedat,
  currency_key_waers,
  material_number_matnr,
  short_text_txz01,
  material_group_matkl,
  plant_werks,
  order_quantity_menge,
  order_unit_meins,
  net_price_netpr,
  net_order_value_netwr,
  net_weight_ntgew,
  weight_unit_gewei,
  spend_based_emissions_kg_co2e,
  mass_based_emissions_kg_co2e,
  total_estimated_ghg_emissions_kg_co2e,
  carbon_intensity_classification
FROM
  carbon_calculated
`
);
