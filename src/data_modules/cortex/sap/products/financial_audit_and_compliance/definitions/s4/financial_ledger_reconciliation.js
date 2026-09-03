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
    "ledger_rldnr"
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
line_items_shifted AS (
  SELECT
    acdoca.mandt AS client_mandt,
    acdoca.rldnr AS ledger_rldnr,
    acdoca.rbukrs AS company_code_bukrs,
    acdoca.gjahr AS fiscal_year_gjahr,
    acdoca.belnr AS document_number_belnr,
    acdoca.docln AS line_item_docln,
    acdoca.budat AS posting_date_budat,
    acdoca.bldat AS document_date_bldat,
    acdoca.cpudt AS entry_date_cpudt,
    acdoca.usnam AS user_name_usnam,
    acdoca.blart AS document_type_blart,
    acdoca.rwcur AS transaction_currency_rwcur,
    acdoca.rhcur AS company_code_currency_rhcur,
    acdoca.wsl * COALESCE(curr_trans.currfix, 1.0) AS amount_in_transaction_currency_wsl,
    acdoca.hsl * COALESCE(curr_comp.currfix, 1.0) AS amount_in_company_code_currency_hsl,
    acdoca.drcrk AS debit_credit_indicator_drcrk,
    acdoca.racct AS account_number_racct,
    acdoca.rcntr AS cost_center_rcntr,
    acdoca.prctr AS profit_center_prctr,
    acdoca.bttype AS business_transaction_type_bttype
  FROM
    ${ctx.ref(moduleConfig.sources.sapModule.datasetId, "acdoca")} AS acdoca
  LEFT JOIN
    currency_decimal AS curr_trans
    ON acdoca.rwcur = curr_trans.currkey
  LEFT JOIN
    currency_decimal AS curr_comp
    ON acdoca.rhcur = curr_comp.currkey
  ${incremental.filter(materializationType, "acdoca.recordstamp")}
)
SELECT
  line.client_mandt,
  line.company_code_bukrs,
  line.document_number_belnr,
  line.fiscal_year_gjahr,
  line.ledger_rldnr,
  MAX(line.document_type_blart) AS document_type_blart,
  MAX(line.posting_date_budat) AS posting_date_budat,
  MAX(line.document_date_bldat) AS document_date_bldat,
  MAX(line.entry_date_cpudt) AS entry_date_cpudt,
  MAX(line.user_name_usnam) AS user_name_usnam,
  MAX(line.company_code_currency_rhcur) AS company_code_currency_rhcur,
  COUNT(DISTINCT line.line_item_docln) AS total_line_items_count,
  SUM(CASE WHEN line.debit_credit_indicator_drcrk = 'S' THEN line.amount_in_company_code_currency_hsl ELSE 0 END) AS total_debit_amount_in_company_currency,
  SUM(CASE WHEN line.debit_credit_indicator_drcrk = 'H' THEN line.amount_in_company_code_currency_hsl ELSE 0 END) AS total_credit_amount_in_company_currency,
  SUM(line.amount_in_company_code_currency_hsl) AS net_ledger_balance_amount,
  CASE
    WHEN ABS(SUM(line.amount_in_company_code_currency_hsl)) < 0.01 THEN 'BALANCED'
    ELSE 'IMBALANCED'
  END AS reconciliation_status
FROM
  line_items_shifted AS line
GROUP BY
  line.client_mandt,
  line.company_code_bukrs,
  line.document_number_belnr,
  line.fiscal_year_gjahr,
  line.ledger_rldnr
`
);
