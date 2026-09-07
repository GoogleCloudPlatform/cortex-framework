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

import importlib
import inspect
import pathlib
import sys

import pytest
import yaml

from common.builders.base import BaseBuilder
from common.registry import auto_discover_plugins, builder_registry
from common.schemas.manifest_schema import ManifestConfig


def test_builder_resolution_integrity(repo_root: pathlib.Path):
    """
    Validates that any builder explicitly declared in a manifest.yaml
    is correctly resolvable via the builder_registry, and any local
    builder.py contains a valid subclass of BuilderPlugin.
    """
    # 1. Populate the global registry
    sys.path.insert(0, str(repo_root / "src"))
    auto_discover_plugins("common.builders")

    src_dir = repo_root / "src"
    errors = []

    for manifest_path in src_dir.rglob("manifest.yaml"):
        module_dir = manifest_path.parent

        with open(manifest_path) as f:
            manifest_data = yaml.safe_load(f) or {}

        manifest = ManifestConfig(**manifest_data)

        # Check Explicit Builder Declaration
        if manifest.builder and not builder_registry.get(manifest.builder):
            errors.append(
                f"Manifest at '{manifest_path.relative_to(repo_root)}' declares builder "
                f"'{manifest.builder}', but it is not registered in the builder_registry. "
                f"Did you forget the @builder_registry.register() decorator?"
            )
        # Check Local Builder Implementations
        local_builder_path = module_dir / "builder.py"
        if local_builder_path.exists():
            rel_path = module_dir.relative_to(src_dir)
            local_module_path = f"{rel_path.as_posix().replace('/', '.')}.builder"
            try:
                # Dynamically import the local builder module
                module = importlib.import_module(local_module_path)
                # Check if it actually contains a valid BuilderPlugin subclass
                has_valid_plugin = False
                for _, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, BaseBuilder)
                        and obj is not BaseBuilder
                        and obj.__module__ == local_module_path
                    ):
                        has_valid_plugin = True
                        break

                if not has_valid_plugin:
                    errors.append(
                        f"Local builder script found at "
                        f"'{local_builder_path.relative_to(repo_root)}' "
                        f"but it does not contain a valid subclass of BuilderPlugin."
                    )
            except Exception as e:
                errors.append(
                    f"Failed to import local builder script at "
                    f"'{local_builder_path.relative_to(repo_root)}': {e}"
                )

    if errors:
        error_msg = "\n".join(["Builder resolution integrity violations found:"] + errors)
        pytest.fail(error_msg)
