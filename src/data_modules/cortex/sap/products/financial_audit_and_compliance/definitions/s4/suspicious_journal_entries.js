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
    "company_code_bukrs",
    "document_number_belnr",
    "fiscal_year_gjahr",
    "line_item_buzei"
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
raw_journal_entries AS (
  SELECT
    bkpf.mandt AS client_mandt,
    bkpf.bukrs AS company_code_bukrs,
    bkpf.belnr AS document_number_belnr,
    bkpf.gjahr AS fiscal_year_gjahr,
    bseg.buzei AS line_item_buzei,
    bkpf.blart AS document_type_blart,
    bkpf.bldat AS document_date_bldat,
    bkpf.budat AS posting_date_budat,
    bkpf.monat AS posting_period_monat,
    bkpf.cpudt AS entry_date_cpudt,
    bkpf.cputm AS time_of_entry_cputm,
    bkpf.usnam AS entered_by_usnam,
    bkpf.tcode AS transaction_code_tcode,
    bkpf.xblnr AS reference_document_xblnr,
    bkpf.bktxt AS document_header_text_bktxt,
    bseg.bschl AS posting_key_bschl,
    bseg.shkzg AS debit_credit_shkzg,
    bseg.hkont AS general_ledger_account_hkont,
    bseg.dmbtr * COALESCE(curr_comp.currfix, 1.0) AS amount_in_local_currency_dmbtr,
    bkpf.waers AS currency_key_waers,
    bseg.kostl AS cost_center_kostl,
    bseg.prctr AS profit_center_prctr,
    bseg.sgtxt AS item_text_sgtxt
  FROM
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "bkpf")} AS bkpf
  INNER JOIN
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "bseg")} AS bseg
    ON bkpf.mandt = bseg.mandt
   AND bkpf.bukrs = bseg.bukrs
   AND bkpf.belnr = bseg.belnr
   AND bkpf.gjahr = bseg.gjahr
  LEFT JOIN
    currency_decimal AS curr_comp
    ON bkpf.waers = curr_comp.currkey
  ${incremental.filter(materializationType, "bkpf.recordstamp")}
),
flagged_entries AS (
  SELECT
    entry.*,
    EXTRACT(DAYOFWEEK FROM entry.entry_date_cpudt) IN (1, 7) AS is_weekend_entry,
    (MOD(CAST(ROUND(entry.amount_in_local_currency_dmbtr, 2) AS INT64), 1000) = 0 AND entry.amount_in_local_currency_dmbtr >= 10000) AS is_round_sum_entry,
    (entry.reference_document_xblnr IS NULL OR TRIM(entry.reference_document_xblnr) = '') AS is_missing_reference_document,
    (DATE_DIFF(entry.posting_date_budat, entry.entry_date_cpudt, DAY) > 30 OR DATE_DIFF(entry.entry_date_cpudt, entry.posting_date_budat, DAY) > 30) AS is_out_of_period_entry
  FROM
    raw_journal_entries AS entry
)
SELECT
  flagged.client_mandt,
  flagged.company_code_bukrs,
  flagged.document_number_belnr,
  flagged.fiscal_year_gjahr,
  flagged.line_item_buzei,
  flagged.document_type_blart,
  flagged.document_date_bldat,
  flagged.posting_date_budat,
  flagged.posting_period_monat,
  flagged.entry_date_cpudt,
  flagged.time_of_entry_cputm,
  flagged.entered_by_usnam,
  flagged.transaction_code_tcode,
  flagged.reference_document_xblnr,
  flagged.document_header_text_bktxt,
  flagged.posting_key_bschl,
  flagged.debit_credit_shkzg,
  flagged.general_ledger_account_hkont,
  flagged.amount_in_local_currency_dmbtr,
  flagged.currency_key_waers,
  flagged.cost_center_kostl,
  flagged.profit_center_prctr,
  flagged.item_text_sgtxt,
  flagged.is_weekend_entry,
  flagged.is_round_sum_entry,
  flagged.is_missing_reference_document,
  flagged.is_out_of_period_entry,
  CASE
    WHEN flagged.is_weekend_entry
      OR flagged.is_round_sum_entry
      OR flagged.is_missing_reference_document
      OR flagged.is_out_of_period_entry
    THEN 'HIGH_RISK_AUDIT_FLAG'
    ELSE 'STANDARD_POSTING'
  END AS audit_risk_classification
FROM
  flagged_entries AS flagged
`
);
