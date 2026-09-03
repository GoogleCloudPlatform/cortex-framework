---
name: using-cortex-skills
description: Discovers and invokes Cortex external agent skills. Use when starting a session or when you need to discover which skill applies to the current task.
---

# Using Cortex Skills

## Overview

Cortex External Agent Skills is a collection of engineering workflow skills designed specifically for configuring, building, validating, and deploying data products in Cortex Framework V7. This meta-skill helps you discover and apply the right skill for your current task.

## Skill Discovery

When a task arrives, identify the development phase and apply the corresponding skill:

```
Task arrives
    │
    ├── Asked to setup/configure/validate environment config? ──→ setup-cortex-config
    │
    ├── Asked to create or scaffold a data product? ────────────→ create-data-product
    │
    ├── Asked to update or change an existing data product? ────→ update-data-product
    │
    ├── Asked to validate/test/audit a data product? ───────────→ validate-data-product
    │
    ├── Asked to write/generate python unit tests? ─────────────→ create-python-tests
    │
    ├── Asked to compile/build/deploy/ship a data product? ─────→ build-and-deploy-data-product
    │
    ├── Asked to generate ER diagrams or data model graphs? ────→ generate-er-diagram
    │
    ├── Asked to generate data quality/integrity assertions? ──→ dataform-assertion-generator
    │
    ├── Asked to generate Looker LookML views or explores? ────→ lookml-generator
    │
    ├── Asked to create/scaffold a new skill or custom rules? ─→ create-skill
    │
    └── Asked to align/review model against business rules? ────→ data-modeling-standards
```

---

## Core Operating Behaviors

These behaviors apply at all times, across all skills. They are non-negotiable.

### 1. Surface Assumptions

Before implementing any changes, explicitly state your assumptions:

```
ASSUMPTIONS I'M MAKING:
1. [assumption about requirements]
2. [assumption about data foundation / tables]
3. [assumption about target environment / configuration]
→ Correct me now or I'll proceed with these.
```

Don't silently fill in ambiguous requirements. Surface uncertainty early — it's cheaper than rework.

### 2. Manage Confusion Actively

When you encounter inconsistencies, conflicting requirements, or unclear specifications:

1. **STOP.** Do not proceed with a guess.
2. Name the specific confusion.
3. Present the tradeoff or ask the clarifying question.
4. Wait for resolution before continuing.

**Bad:** Silently picking one interpretation and hoping it's right.
**Good:** "I see X in the spec but Y in the existing code. Which takes precedence?"

### 3. AI Development & Research Rules

*   **Ignore Source Skill Directories:** You **MUST** completely ignore the root folders `external-skills/` and `internal-skills/` when reading, writing, or modifying code, configurations, or data products. All active code, configurations, and tests reside strictly inside `cortex-framework-core/`. Do not write files or reference paths inside the root `external-skills/` and `internal-skills/` directories unless explicitly instructed by setup scripts.
*   **No Hallucination:** Do not hallucinate business logic or SAP table fields.
*   **SAP Target Version & Live System Inspection:** When implementing SAP-related data models:
    - You **MUST** explicitly establish and confirm with the user whether the data product targets **ECC**, **S/4HANA**, or **Both**. Proper implementation is impossible without confirming this target version.
    - You **MUST** retrieve the exact field schemas, data types, key flags, and check table relations for **all** involved SAP tables directly from the replicated SAP Data Dictionary (DDIC) tables in BigQuery using the `query-sap-ddic` skill (via `cortex-framework-core/.venv/bin/python external-skills/.agents/skills/query_sap_ddic/scripts/query_sap_ddic.py`).
    - You **MUST** explicitly identify and document any structural, field name, or data type differences between ECC and S/4HANA, and handle these differences explicitly in your plan and code (e.g., using version-specific directories like `annotations/ecc/` and `annotations/s4/`, or conditional SQL logic).
*   **Extensibility & Namespace:** Custom development **MUST** prefer custom namespaces (e.g., `custom`, `myorg`). If the user has not explicitly specified a namespace, you **MUST** ask for a custom namespace before proposing a plan or writing code. Proceed with the standard `cortex` namespace **ONLY** after explicitly warning the user of overwrite/upgrade conflicts and getting their explicit confirmation.
*   **Verify Foundations:** NEVER assume a field exists in the foundation. You **MUST** verify all required tables exist in `src/data_modules/<namespace>/<source>/foundations/sap/table_settings.default.yaml` and column fields exist in `src/data_modules/<namespace>/<source>/foundations/sap/annotations/`.
*   **Python Environment & Dependencies:** If running python tools or scripts fails due to missing packages or env errors, you **MUST** run `uv sync` in the `cortex-framework-core/` folder first, and then execute using the virtual environment's interpreter (`cortex-framework-core/.venv/bin/python`).

### 4. Code Structure & File Formats

*   **Language & Engine:** Cortex V7 uses Dataform. All data models must be written as Dataform `.js` files.
*   **Target Paths:**
    *   Data Product code goes under `src/data_modules/<namespace>/<source>/products/<type>/`
    *   Data Product config files go under `config/<namespace>/<source>/products/<type>/`
    *   Data Foundation elements belong under `src/data_modules/<namespace>/<source>/foundations/sap/`
