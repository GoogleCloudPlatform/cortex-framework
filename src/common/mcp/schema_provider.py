# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Cortex Schema Provider for MCP Server and Agent Grounding."""

import pathlib
from typing import Any

import yaml


class CortexSchemaProvider:
    """Discovers, parses, and indexes Cortex Framework data products and schemas."""

    def __init__(self, repo_root: pathlib.Path | None = None) -> None:
        if repo_root is None:
            # Default to repo root relative to this file
            self.repo_root = pathlib.Path(__file__).resolve().parents[3]
        else:
            self.repo_root = pathlib.Path(repo_root)

        self.data_modules_dir = self.repo_root / "src" / "data_modules"
        self._products: dict[str, dict[str, Any]] = {}
        self._field_index: dict[str, list[dict[str, Any]]] = {}
        self._load_products()

    def _load_products(self) -> None:
        """Parses all manifest.yaml and annotation YAML files in data_modules."""
        if not self.data_modules_dir.exists():
            return

        for manifest_path in self.data_modules_dir.rglob("manifest.yaml"):
            product_dir = manifest_path.parent
            try:
                with open(manifest_path, encoding="utf-8") as f:
                    manifest_data = yaml.safe_load(f) or {}
            except Exception:
                continue

            product_type = manifest_data.get("type", product_dir.name)
            display_name = manifest_data.get("displayName", product_type)
            description = manifest_data.get("description", "")
            category = manifest_data.get("category", "")
            dependencies = manifest_data.get("dependencies", {})

            # Discover annotations
            tables: dict[str, dict[str, Any]] = {}
            annotations_dir = product_dir / "annotations"
            if annotations_dir.exists():
                for anno_file in annotations_dir.rglob("*.yaml"):
                    try:
                        with open(anno_file, encoding="utf-8") as f:
                            anno_data = yaml.safe_load(f) or {}
                    except Exception:
                        continue

                    table_name = anno_file.stem
                    table_desc = anno_data.get("description", "")
                    fields = anno_data.get("fields", [])

                    tables[table_name] = {
                        "table_name": table_name,
                        "description": table_desc,
                        "fields": fields,
                    }

                    # Index fields for reverse lookup
                    for field in fields:
                        f_name = field.get("name", "").lower()
                        f_desc = field.get("description", "")
                        if f_name not in self._field_index:
                            self._field_index[f_name] = []
                        self._field_index[f_name].append(
                            {
                                "product_type": product_type,
                                "display_name": display_name,
                                "table_name": table_name,
                                "field_name": f_name,
                                "description": f_desc,
                            }
                        )

            self._products[product_type] = {
                "type": product_type,
                "display_name": display_name,
                "description": description,
                "category": category,
                "dependencies": dependencies,
                "product_dir": str(product_dir.relative_to(self.repo_root)),
                "tables": tables,
            }

    def list_products(self) -> list[dict[str, Any]]:
        """Returns a list of all discovered Cortex data products."""
        return [
            {
                "type": p["type"],
                "display_name": p["display_name"],
                "description": p["description"],
                "category": p["category"],
                "table_count": len(p["tables"]),
                "tables": list(p["tables"].keys()),
            }
            for p in self._products.values()
        ]

    def get_product_schema(self, product_type: str) -> dict[str, Any] | None:
        """Returns the full schema definition and field dictionary for a data product."""
        return self._products.get(product_type)

    def explain_field(self, field_name: str) -> list[dict[str, Any]]:
        """Finds all occurrences, business descriptions, and product mappings for a field."""
        search_key = field_name.strip().lower()
        # Direct exact match
        if search_key in self._field_index:
            return self._field_index[search_key]

        # Suffix / substring match
        results = []
        for key, entries in self._field_index.items():
            if search_key in key or key.endswith(f"_{search_key}"):
                results.extend(entries)
        return results
