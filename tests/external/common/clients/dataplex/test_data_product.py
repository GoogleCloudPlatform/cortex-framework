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

from unittest.mock import MagicMock, patch

import pytest
from google.api_core import exceptions as google_exceptions
from google.cloud import dataplex_v1 as dataplex

from common.clients.dataplex.data_product import DataProductClient
from common.clients.dataplex.model import (
    BigQueryAssetLinks,
    BigQueryTableInfo,
    DataAssetInfo,
    DataProduct,
    DataProductInfo,
)
from common.clients.model.exception import (
    AlreadyExistsError,
    FailedOperationError,
    FailedPreconditionError,
    IllegalArgumentError,
    NotFoundError,
    ResourceQuotaExceededError,
)


@pytest.fixture
def mock_dataplex_client():
    return MagicMock(spec=dataplex.DataProductServiceClient)


def test_init_with_client(mock_dataplex_client):
    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)
    assert client._project_id == "test-proj"
    assert client._client == mock_dataplex_client


def test_init_default_client():
    with patch(
        "common.clients.dataplex.data_product.dataplex.DataProductServiceClient"
    ) as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance

        client = DataProductClient(project_id="test-proj")
        assert client._project_id == "test-proj"
        assert client._client == mock_instance
        mock_class.assert_called_once()


def test_list_data_product_infos(mock_dataplex_client):
    # Mock response list
    mock_product1 = MagicMock()
    mock_product1.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_product1.display_name = "Data Product 1"
    mock_product1.owner_emails = ["owner1@test.com"]
    mock_product1.description = "Description 1"
    mock_product1.labels = {"label1": "val1"}

    mock_product2 = MagicMock()
    mock_product2.name = "projects/test-proj/locations/us-central1/dataProducts/dp2"
    mock_product2.display_name = "Data Product 2"
    mock_product2.owner_emails = ["owner2@test.com"]
    mock_product2.description = "Description 2"
    mock_product2.labels = {}

    mock_dataplex_client.list_data_products.return_value = [mock_product1, mock_product2]

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)
    results = client.list_data_product_infos(location="us-central1")

    # Check mock call
    mock_dataplex_client.list_data_products.assert_called_once()
    call_args = mock_dataplex_client.list_data_products.call_args[1]["request"]
    assert isinstance(call_args, dataplex.ListDataProductsRequest)
    assert call_args.parent == "projects/test-proj/locations/us-central1"

    # Check mappings
    assert len(results) == 2
    assert results[0] == DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
        labels={"label1": "val1"},
    )
    assert results[1] == DataProductInfo(
        id="dp2",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 2",
        owner_emails=("owner2@test.com",),
        description="Description 2",
        labels={},
    )


def test_get_data_product(mock_dataplex_client):
    # Mock get_data_product response
    mock_product = MagicMock()
    mock_product.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_product.display_name = "Data Product 1"
    mock_product.owner_emails = ["owner1@test.com"]
    mock_product.description = "Description 1"
    mock_product.labels = {"key": "val"}
    mock_dataplex_client.get_data_product.return_value = mock_product

    # Mock list_data_assets response
    mock_asset1 = MagicMock()
    mock_asset1.name = "projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/asset1"
    mock_asset1.resource = "projects/linked-proj/datasets/linked-ds1"

    mock_asset2 = MagicMock()
    mock_asset2.name = "projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/asset2"
    mock_asset2.resource = "projects/linked-proj/datasets/linked-ds2"

    mock_dataplex_client.list_data_assets.return_value = [mock_asset1, mock_asset2]

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)
    result = client.get_data_product(location="us-central1", data_product_id="dp1")

    # Check get_data_product request
    mock_dataplex_client.get_data_product.assert_called_once()
    call_args_product = mock_dataplex_client.get_data_product.call_args[1]["request"]
    assert isinstance(call_args_product, dataplex.GetDataProductRequest)
    assert call_args_product.name == "projects/test-proj/locations/us-central1/dataProducts/dp1"

    # Check list_data_assets request
    mock_dataplex_client.list_data_assets.assert_called_once()
    call_args_assets = mock_dataplex_client.list_data_assets.call_args[1]["request"]
    assert isinstance(call_args_assets, dataplex.ListDataAssetsRequest)
    assert call_args_assets.parent == "projects/test-proj/locations/us-central1/dataProducts/dp1"

    # Check output DataProduct structure
    expected_product_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
        labels={"key": "val"},
    )
    expected_data_assets = [
        DataAssetInfo(
            id="asset1",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/asset1",
            linked_resource="projects/linked-proj/datasets/linked-ds1",
        ),
        DataAssetInfo(
            id="asset2",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/asset2",
            linked_resource="projects/linked-proj/datasets/linked-ds2",
        ),
    ]

    assert result.data_product_info == expected_product_info
    assert list(result.data_assets) == expected_data_assets


def test_get_data_product_not_found(mock_dataplex_client):
    mock_dataplex_client.get_data_product.side_effect = google_exceptions.NotFound("Not found")

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)
    with pytest.raises(NotFoundError):
        client.get_data_product(location="us-central1", data_product_id="dp1")


def test_get_data_product_list_assets_quota_exceeded(mock_dataplex_client):
    mock_product = MagicMock()
    mock_product.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_product.display_name = "Data Product 1"
    mock_product.owner_emails = ["owner1@test.com"]
    mock_product.description = "Description 1"
    mock_product.labels = {"key": "val"}
    mock_dataplex_client.get_data_product.return_value = mock_product

    mock_dataplex_client.list_data_assets.side_effect = google_exceptions.ResourceExhausted(
        "Quota exceeded"
    )

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)
    with pytest.raises(ResourceQuotaExceededError) as exc_info:
        client.get_data_product(location="us-central1", data_product_id="dp1")
    assert "listing data assets" in str(exc_info.value)


def test_get_data_product_list_assets_failed_operation(mock_dataplex_client):
    mock_product = MagicMock()
    mock_product.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_dataplex_client.get_data_product.return_value = mock_product

    mock_dataplex_client.list_data_assets.side_effect = google_exceptions.GoogleAPICallError(
        "Internal error"
    )

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)
    with pytest.raises(FailedOperationError) as exc_info:
        client.get_data_product(location="us-central1", data_product_id="dp1")
    assert "list data assets for data product" in str(exc_info.value)


def test_create_data_product_success(mock_dataplex_client):
    # Mock Create operation LRO
    mock_operation = MagicMock()
    mock_created_product = MagicMock()
    mock_created_product.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_created_product.display_name = "Data Product 1"
    mock_created_product.owner_emails = ["owner1@test.com"]
    mock_created_product.description = "Description 1"
    mock_created_product.labels = {
        "cortex-framework-created": "true",
        "cortex-framework-version": "7-0-0",
    }
    mock_operation.result.return_value = mock_created_product
    mock_dataplex_client.create_data_product.return_value = mock_operation

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)

    input_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
    )

    result = client.create_data_product(data_product_info=input_info)

    # Check create_data_product request
    mock_dataplex_client.create_data_product.assert_called_once()
    call_args = mock_dataplex_client.create_data_product.call_args[1]["request"]
    assert isinstance(call_args, dataplex.CreateDataProductRequest)
    assert call_args.parent == "projects/test-proj/locations/us-central1"
    assert call_args.data_product_id == "dp1"
    assert call_args.data_product.display_name == "Data Product 1"
    assert call_args.data_product.description == "Description 1"
    assert call_args.data_product.owner_emails == ["owner1@test.com"]
    assert call_args.data_product.labels == {
        "cortex-framework-created": "true",
        "cortex-framework-version": "7-0-0",
    }

    # Check returned result
    expected_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
        labels={
            "cortex-framework-created": "true",
            "cortex-framework-version": "7-0-0",
        },
    )
    assert result.data_product_info == expected_info
    assert list(result.data_assets) == []


def test_create_data_product_already_exists(mock_dataplex_client):
    mock_dataplex_client.create_data_product.side_effect = google_exceptions.AlreadyExists(
        "Already exists"
    )

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)

    input_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
    )

    with pytest.raises(AlreadyExistsError):
        client.create_data_product(data_product_info=input_info)


def test_create_data_product_with_linked_assets_default_project(mock_dataplex_client):
    # Mock Create operation LRO for data product
    mock_product_operation = MagicMock()
    mock_created_product = MagicMock()
    mock_created_product.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_created_product.display_name = "Data Product 1"
    mock_created_product.owner_emails = ["owner1@test.com"]
    mock_created_product.description = "Description 1"
    mock_created_product.labels = {
        "cortex-framework-created": "true",
        "cortex-framework-version": "7-0-0",
    }
    mock_product_operation.result.return_value = mock_created_product
    mock_dataplex_client.create_data_product.return_value = mock_product_operation

    # Mock Create operation LRO for data assets using side effect
    def create_data_asset_side_effect(request, **kwargs):
        mock_op = MagicMock()
        mock_asset = MagicMock()
        # The ID will be the last element of the resource URI
        asset_id = request.data_asset.resource.split("/")[-1]
        mock_asset.name = f"{request.parent}/dataAssets/{asset_id}"
        mock_asset.resource = request.data_asset.resource
        mock_op.result.return_value = mock_asset
        return mock_op

    mock_dataplex_client.create_data_asset.side_effect = create_data_asset_side_effect

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)

    input_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
    )

    asset_links = BigQueryAssetLinks(
        dataset_ids=("ds1",),
        table_infos=(BigQueryTableInfo(dataset_id="ds2", table_id="t2"),),
    )

    result = client.create_data_product(
        data_product_info=input_info,
        bigquery_asset_links=asset_links,
    )

    # Check create_data_product request
    mock_dataplex_client.create_data_product.assert_called_once()

    # Check create_data_asset requests
    assert mock_dataplex_client.create_data_asset.call_count == 2
    calls = mock_dataplex_client.create_data_asset.call_args_list

    # Extract request arguments
    requested_assets = [call[1]["request"].data_asset.resource for call in calls]
    expected_resources = {
        "//bigquery.googleapis.com/projects/test-proj/datasets/ds1",
        "//bigquery.googleapis.com/projects/test-proj/datasets/ds2/tables/t2",
    }
    assert set(requested_assets) == expected_resources

    # Check returned result
    expected_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
        labels={
            "cortex-framework-created": "true",
            "cortex-framework-version": "7-0-0",
        },
    )
    assert result.data_product_info == expected_info

    expected_assets = [
        DataAssetInfo(
            id="ds1",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/ds1",
            linked_resource="//bigquery.googleapis.com/projects/test-proj/datasets/ds1",
        ),
        DataAssetInfo(
            id="t2",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/t2",
            linked_resource="//bigquery.googleapis.com/projects/test-proj/datasets/ds2/tables/t2",
        ),
    ]
    assert len(result.data_assets) == 2
    assert set(result.data_assets) == set(expected_assets)


def test_create_data_product_with_linked_assets_custom_project(mock_dataplex_client):
    # Mock Create operation LRO for data product
    mock_product_operation = MagicMock()
    mock_created_product = MagicMock()
    mock_created_product.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_created_product.display_name = "Data Product 1"
    mock_created_product.owner_emails = ["owner1@test.com"]
    mock_created_product.description = "Description 1"
    mock_created_product.labels = {
        "cortex-framework-created": "true",
        "cortex-framework-version": "7-0-0",
    }
    mock_product_operation.result.return_value = mock_created_product
    mock_dataplex_client.create_data_product.return_value = mock_product_operation

    # Mock Create operation LRO for data assets using side effect
    def create_data_asset_side_effect(request, **kwargs):
        mock_op = MagicMock()
        mock_asset = MagicMock()
        asset_id = request.data_asset.resource.split("/")[-1]
        mock_asset.name = f"{request.parent}/dataAssets/{asset_id}"
        mock_asset.resource = request.data_asset.resource
        mock_op.result.return_value = mock_asset
        return mock_op

    mock_dataplex_client.create_data_asset.side_effect = create_data_asset_side_effect

    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)

    input_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
    )

    asset_links = BigQueryAssetLinks(
        dataset_ids=("ds1",),
        table_infos=(BigQueryTableInfo(dataset_id="ds2", table_id="t2"),),
        bigquery_project_id="custom-bq-proj",
    )

    result = client.create_data_product(
        data_product_info=input_info,
        bigquery_asset_links=asset_links,
    )

    # Check create_data_product request
    mock_dataplex_client.create_data_product.assert_called_once()

    # Check create_data_asset requests
    assert mock_dataplex_client.create_data_asset.call_count == 2
    calls = mock_dataplex_client.create_data_asset.call_args_list

    # Extract request arguments
    requested_assets = [call[1]["request"].data_asset.resource for call in calls]
    expected_resources = {
        "//bigquery.googleapis.com/projects/custom-bq-proj/datasets/ds1",
        "//bigquery.googleapis.com/projects/custom-bq-proj/datasets/ds2/tables/t2",
    }
    assert set(requested_assets) == expected_resources

    # Check returned result
    expected_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        description="Description 1",
        labels={
            "cortex-framework-created": "true",
            "cortex-framework-version": "7-0-0",
        },
    )
    assert result.data_product_info == expected_info

    expected_assets = [
        DataAssetInfo(
            id="ds1",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/ds1",
            linked_resource="//bigquery.googleapis.com/projects/custom-bq-proj/datasets/ds1",
        ),
        DataAssetInfo(
            id="t2",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/t2",
            linked_resource="//bigquery.googleapis.com/projects/custom-bq-proj/datasets/ds2/tables/t2",
        ),
    ]
    assert len(result.data_assets) == 2
    assert set(result.data_assets) == set(expected_assets)


def test_is_managed_data_product_true(mock_dataplex_client):
    info = DataProductInfo(
        id="dp1",
        project_id="proj",
        location="loc",
        display_name="DP1",
        owner_emails=(),
        labels={"cortex-framework-created": "true", "cortex-framework-version": "7-0-0"},
    )
    dp = DataProduct(data_product_info=info)
    client = DataProductClient(project_id="proj", dataplex_client=mock_dataplex_client)
    assert client.is_managed_data_product(dp) is True


def test_is_managed_data_product_false_missing_created_label(mock_dataplex_client):
    info = DataProductInfo(
        id="dp1",
        project_id="proj",
        location="loc",
        display_name="DP1",
        owner_emails=(),
        labels={"cortex-framework-version": "7-0-0"},
    )
    dp = DataProduct(data_product_info=info)
    client = DataProductClient(project_id="proj", dataplex_client=mock_dataplex_client)
    assert client.is_managed_data_product(dp) is False


def test_is_managed_data_product_false_version_mismatch(mock_dataplex_client):
    info = DataProductInfo(
        id="dp1",
        project_id="proj",
        location="loc",
        display_name="DP1",
        owner_emails=(),
        labels={"cortex-framework-created": "true", "cortex-framework-version": "6-0-0"},
    )
    dp = DataProduct(data_product_info=info)
    client = DataProductClient(project_id="proj", dataplex_client=mock_dataplex_client)
    assert client.is_managed_data_product(dp) is False


def test_is_managed_data_product_no_info_raises(mock_dataplex_client):
    dp = DataProduct(data_product_info=None)
    client = DataProductClient(project_id="proj", dataplex_client=mock_dataplex_client)
    with pytest.raises(IllegalArgumentError):
        client.is_managed_data_product(dp)


def test_update_data_product_success(mock_dataplex_client):
    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)

    # 1. Existing data product returned by get_data_product
    existing_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        labels={"cortex-framework-created": "true", "cortex-framework-version": "7-0-0"},
    )
    existing_assets = (
        DataAssetInfo(
            id="ds1",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/ds1",
            linked_resource="//bigquery.googleapis.com/projects/test-proj/datasets/ds1",
        ),
        DataAssetInfo(
            id="t2",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/t2",
            linked_resource="//bigquery.googleapis.com/projects/test-proj/datasets/ds2/tables/t2",
        ),
    )
    existing_dp = DataProduct(data_product_info=existing_info, data_assets=existing_assets)

    # Mock get_data_product on the client
    client.get_data_product = MagicMock(return_value=existing_dp)

    # 2. Mock Dataplex client response for update_data_product
    mock_op_product = MagicMock()
    mock_updated_product = MagicMock()
    mock_updated_product.name = "projects/test-proj/locations/us-central1/dataProducts/dp1"
    mock_updated_product.display_name = "Data Product 1 Updated"
    mock_updated_product.owner_emails = ["owner1@test.com"]
    mock_updated_product.description = "Description 1 Updated"
    mock_updated_product.labels = {
        "cortex-framework-created": "true",
        "cortex-framework-version": "7-0-0",
    }
    mock_op_product.result.return_value = mock_updated_product
    mock_dataplex_client.update_data_product.return_value = mock_op_product

    # Mock Dataplex client response for create_data_asset
    mock_op_create = MagicMock()
    mock_created_asset = MagicMock()
    mock_created_asset.name = (
        "projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/t3"
    )
    mock_created_asset.resource = (
        "//bigquery.googleapis.com/projects/test-proj/datasets/ds3/tables/t3"
    )
    mock_op_create.result.return_value = mock_created_asset
    mock_dataplex_client.create_data_asset.return_value = mock_op_create

    # Mock Dataplex client response for delete_data_asset
    mock_op_delete = MagicMock()
    mock_dataplex_client.delete_data_asset.return_value = mock_op_delete

    # Input to update
    input_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1 Updated",
        owner_emails=("owner1@test.com",),
        description="Description 1 Updated",
    )

    asset_links = BigQueryAssetLinks(
        dataset_ids=("ds1",),  # existing dataset, will be kept
        table_infos=(BigQueryTableInfo(dataset_id="ds3", table_id="t3"),),
        # new table, will be created
    )

    # Execute
    result = client.update_data_product(
        data_product_info=input_info,
        bigquery_asset_links=asset_links,
    )

    # Assertions
    client.get_data_product.assert_called_once_with("us-central1", "dp1")

    # Check update_data_product request
    mock_dataplex_client.update_data_product.assert_called_once()
    call_args_update = mock_dataplex_client.update_data_product.call_args[1]["request"]
    assert isinstance(call_args_update, dataplex.UpdateDataProductRequest)
    assert (
        call_args_update.data_product.name
        == "projects/test-proj/locations/us-central1/dataProducts/dp1"
    )
    assert call_args_update.data_product.display_name == "Data Product 1 Updated"
    assert call_args_update.data_product.description == "Description 1 Updated"

    # Check delete_data_asset request (should delete t2 since it is not in asset_links)
    mock_dataplex_client.delete_data_asset.assert_called_once()
    call_args_delete = mock_dataplex_client.delete_data_asset.call_args[1]["request"]
    assert isinstance(call_args_delete, dataplex.DeleteDataAssetRequest)
    assert (
        call_args_delete.name
        == "projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/t2"
    )

    # Check create_data_asset request (should create t3)
    mock_dataplex_client.create_data_asset.assert_called_once()
    call_args_create = mock_dataplex_client.create_data_asset.call_args[1]["request"]
    assert isinstance(call_args_create, dataplex.CreateDataAssetRequest)
    assert call_args_create.parent == "projects/test-proj/locations/us-central1/dataProducts/dp1"
    assert (
        call_args_create.data_asset.resource
        == "//bigquery.googleapis.com/projects/test-proj/datasets/ds3/tables/t3"
    )

    # Check final returned product
    expected_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1 Updated",
        owner_emails=("owner1@test.com",),
        description="Description 1 Updated",
        labels={
            "cortex-framework-created": "true",
            "cortex-framework-version": "7-0-0",
        },
    )
    expected_assets = [
        # Kept asset
        DataAssetInfo(
            id="ds1",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/ds1",
            linked_resource="//bigquery.googleapis.com/projects/test-proj/datasets/ds1",
        ),
        # Newly created asset
        DataAssetInfo(
            id="t3",
            resource_name="projects/test-proj/locations/us-central1/dataProducts/dp1/dataAssets/t3",
            linked_resource="//bigquery.googleapis.com/projects/test-proj/datasets/ds3/tables/t3",
        ),
    ]

    assert result.data_product_info == expected_info
    assert len(result.data_assets) == 2
    assert set(result.data_assets) == set(expected_assets)


def test_update_data_product_not_managed_raises(mock_dataplex_client):
    client = DataProductClient(project_id="test-proj", dataplex_client=mock_dataplex_client)

    # Existing data product is NOT managed (labels missing)
    existing_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1",
        owner_emails=("owner1@test.com",),
        labels={},
    )
    existing_dp = DataProduct(data_product_info=existing_info)
    client.get_data_product = MagicMock(return_value=existing_dp)

    input_info = DataProductInfo(
        id="dp1",
        project_id="test-proj",
        location="us-central1",
        display_name="Data Product 1 Updated",
        owner_emails=("owner1@test.com",),
    )

    with pytest.raises(FailedPreconditionError):
        client.update_data_product(data_product_info=input_info)
