# Cortex 7 Extensibility & Development Assistant

System instructions and task guidelines for working with Google Cloud Cortex Framework V7 and modular developer agent skills.

---

## Lifecycle Slash Commands

When the user issues any of the following commands, you must immediately load the referenced `.agents/skills/<skill_name>/SKILL.md` instructions into your active context and follow the workflow steps, quality gates, and validation checks outlined therein. Do not begin writing or modifying any code until you have fully parsed the relevant skill instructions.

| Command | Associated Skill | Target Action & Purpose |
|:---|:---|:---|
| `/using-cortex-skills` | [using_cortex_skills](file:///.agents/skills/using_cortex_skills/SKILL.md) | Discovers and invokes Cortex agent skills. Use when starting a session or when you need to discover which skill applies to the current task. |
| `/setup-cortex-config` | [setup_cortex_config](file:///.agents/skills/setup_cortex_config/SKILL.md) | Guides the interactive slot-filling setup, targets configuration, and environment setup of the main `config.yaml`. |
| `/create-data-product` | [create_data_product](file:///.agents/skills/create_data_product/SKILL.md) | Scaffolds standard directory structure, parses source datasets, maps fields, and creates a new Cortex data product. |
| `/update-data-product` | [update_data_product](file:///.agents/skills/update_data_product/SKILL.md) | Workflow for impact analysis, research documentation, coding updates, and validation for changing existing products. |
| `/validate-data-product` | [validate_data_product](file:///.agents/skills/validate_data_product/SKILL.md) | Performs structural checks, syntax checking, pipeline execution, and runs the pytest validation suite. |
| `/build-and-deploy` | [build_and_deploy_data_product](file:///.agents/skills/build_and_deploy_data_product/SKILL.md) | Syncs environment variables, identifies configuration profiles, builds Dataform models, and deploys data products. |
| `/query-sap-ddic` | [query_sap_ddic](file:///.agents/skills/query_sap_ddic/SKILL.md) | Inspects and dumps SAP table schemas directly from replicated SAP DDIC tables in BigQuery. |
| `/generate-er-diagram` | [generate_er_diagram](file:///.agents/skills/generate_er_diagram/SKILL.md) | Extracts schema definitions, automatically infers entity relationships via SAP field suffixes, and generates visual ERDs. |
| `/generate-assertions` | [dataform_assertion_generator](file:///.agents/skills/dataform_assertion_generator/SKILL.md) | Inspects data products and generates automated Dataform data-integrity assertions and ledger reconciliation checks. |
| `/generate-lookml` | [lookml_generator](file:///.agents/skills/lookml_generator/SKILL.md) | Generates production-ready Looker LookML views, dimensions, measures, and explores from Cortex data product schemas. |
| `/create-skill` | [create_skill](file:///.agents/skills/create_skill/SKILL.md) | Evaluates overlap, scaffolds new skills or custom folder overrides, authors instructions, and validates anatomy. |

---

## Primary Code Structure & Formats

*   **Data Products**: All custom modules and transformations must reside under `src/data_modules/<namespace>/[...optional_segments...]/<type>/` with configurations at `config/<namespace>/[...optional_segments...]/<type>/`. The first segment must be the namespace (e.g., `cortex`), the last segment (the leaf) must match the `type` defined in the manifest, and any middle segments are optional organizational folders (e.g., `<source>/products`).
*   **Data Foundation**: Core core/foundation pipelines reside under `src/data_modules/cortex/<source>/foundations/sap/` and configurations under `config/cortex/<source>/foundations/sap/`.
*   **Language**: Cortex V7 targets **Dataform**. Data models and tables should be authored as Dataform `.js` or `.sqlx` scripts in their respective directories. Do not write legacy raw SQL formats.
*   **Relationship Discovery**: When building relationships dynamically, always refer to field names. SAP-replicated tables map primary/foreign key bounds based on raw SAP suffix indicators (like `_lifnr` or `_matnr`), keeping in mind to ignore common client identifiers (`mandt`, `client`), ingestion timestamps, and technical system fields.

## CRITICAL: Skill Customization & Extensibility

Skills may have a `/custom` subdirectory which extends/overrides aspects of the base skill instructions. If they do have files in the folder always read, merge with and follow instructions in there. If the `/custom` directory is empty, then follow the base skill instructions.