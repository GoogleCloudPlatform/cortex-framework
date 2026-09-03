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

from unittest.mock import MagicMock

import pytest
from google.api_core.exceptions import GoogleAPICallError
from google.cloud import resourcemanager_v3

from common.clients.resource_manager import ResourceManagerClient


@pytest.fixture
def mock_folders_client():
    return MagicMock(spec=resourcemanager_v3.FoldersClient)


def test_get_project_number_success(mock_folders_client):
    # Mock the ProjectsClient
    mock_client = MagicMock(spec=resourcemanager_v3.ProjectsClient)

    # Mock the Project object returned by get_project
    mock_project = MagicMock()
    mock_project.name = "projects/123456789012"
    mock_client.get_project.return_value = mock_project

    # Instantiate the ResourceManagerClient with the mocked client
    rm_client = ResourceManagerClient(client=mock_client, folders_client=mock_folders_client)

    # Call the method
    project_number = rm_client.get_project_number("my-project-id")

    # Assertions
    assert project_number == "123456789012"
    mock_client.get_project.assert_called_once_with(name="projects/my-project-id")


def test_get_project_number_failure(mock_folders_client):
    # Mock the ProjectsClient to raise an exception
    mock_client = MagicMock(spec=resourcemanager_v3.ProjectsClient)
    mock_client.get_project.side_effect = GoogleAPICallError(
        "Permission denied or project not found"
    )

    rm_client = ResourceManagerClient(client=mock_client, folders_client=mock_folders_client)

    # Call the method and expect an exception
    with pytest.raises(GoogleAPICallError) as exc_info:
        rm_client.get_project_number("my-project-id")

    assert "Permission denied or project not found" in str(exc_info.value)
    mock_client.get_project.assert_called_once_with(name="projects/my-project-id")


def test_get_project_ancestry_success(mock_folders_client):
    mock_projects_client = MagicMock(spec=resourcemanager_v3.ProjectsClient)

    mock_project = MagicMock()
    mock_project.name = "projects/123456789012"
    mock_project.parent = "folders/111"
    mock_projects_client.get_project.return_value = mock_project

    mock_folder = MagicMock()
    mock_folder.name = "folders/111"
    mock_folder.parent = "organizations/999"
    mock_folders_client.get_folder.return_value = mock_folder

    rm_client = ResourceManagerClient(
        client=mock_projects_client, folders_client=mock_folders_client
    )
    ancestry = rm_client.get_project_ancestry("my-project-id")

    assert ancestry == [
        "projects/my-project-id",
        "projects/123456789012",
        "folders/111",
        "organizations/999",
    ]
    mock_projects_client.get_project.assert_called_once_with(name="projects/my-project-id")
    mock_folders_client.get_folder.assert_called_once_with(name="folders/111")


def test_get_project_ancestry_failure_fallback(mock_folders_client):
    mock_projects_client = MagicMock(spec=resourcemanager_v3.ProjectsClient)
    mock_projects_client.get_project.side_effect = GoogleAPICallError("API error")

    rm_client = ResourceManagerClient(
        client=mock_projects_client, folders_client=mock_folders_client
    )
    ancestry = rm_client.get_project_ancestry("my-project-id")

    assert ancestry == ["projects/my-project-id"]
