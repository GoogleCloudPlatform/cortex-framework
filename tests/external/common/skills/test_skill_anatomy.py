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

import pathlib

import pytest
import yaml


def test_skill_anatomy(repo_root: pathlib.Path):
    skills_dir = repo_root / ".agents" / "skills"
    if not skills_dir.exists():
        pytest.skip("No skills directory found.")

    errors = []
    for skill_path in skills_dir.iterdir():
        if not skill_path.is_dir():
            continue

        skill_name = skill_path.name
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"Missing SKILL.md in {skill_name}")
            continue

        custom_dir = skill_path / "custom"
        if not custom_dir.exists():
            errors.append(f"Missing custom/ directory in {skill_name}")

        text = skill_md.read_text(encoding="utf-8").lstrip("\ufeff")
        if not text.startswith("---"):
            errors.append(f"Missing opening frontmatter in {skill_name}")
            continue

        parts = text.split("---", 2)
        if len(parts) < 3:
            errors.append(f"Malformed frontmatter in {skill_name}")
            continue

        try:
            data = yaml.safe_load(parts[1]) or {}
        except Exception as e:
            errors.append(f"Failed to parse YAML frontmatter in {skill_name}: {e}")
            continue

        name = data.get("name", "")
        desc = data.get("description", "")
        if not name:
            errors.append(f"Missing 'name' in frontmatter for {skill_name}")
        if not desc:
            errors.append(f"Missing 'description' in frontmatter for {skill_name}")
        elif len(str(desc)) > 1024:
            errors.append(f"Description too long in {skill_name} ({len(str(desc))} > 1024)")

    if errors:
        pytest.fail("\n".join(errors))
