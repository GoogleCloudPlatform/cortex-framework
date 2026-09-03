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


class KnowledgeCatalogSyncError(Exception):
    """Base exception for errors during the knowledge catalog sync process."""

    pass


class DataProductConfigurationError(KnowledgeCatalogSyncError):
    """Raised when there is an error in the deployed data product configuration."""

    pass


class DataModulesPathNotFoundError(KnowledgeCatalogSyncError):
    """Raised when the data modules path is not found."""

    pass


class ManifestNotFoundError(KnowledgeCatalogSyncError):
    """Raised when the data product manifest is not found."""

    pass


class TableSettingsFileNotFoundError(KnowledgeCatalogSyncError):
    """Raised when the data product table settings file is not found."""

    pass
