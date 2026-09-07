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

"""Unit tests for Cortex Model Context Protocol (MCP) Server."""

import json

import pytest

from tools.mcp_server import CortexMCPServer


@pytest.fixture
def mcp_server():
    return CortexMCPServer()


def test_mcp_server_initialize(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {},
    }
    resp = mcp_server.process_rpc_request(req)
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "cortex-mcp-server"
    assert resp["result"]["serverInfo"]["version"] == "7.0.4"


def test_mcp_server_tools_list(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {},
    }
    resp = mcp_server.process_rpc_request(req)
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "list_cortex_data_products" in tool_names
    assert "get_data_product_schema" in tool_names
    assert "explain_sap_field" in tool_names
    assert "generate_grounded_sql" in tool_names


def test_mcp_tool_list_products(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_cortex_data_products",
            "arguments": {},
        },
    }
    resp = mcp_server.process_rpc_request(req)
    assert resp["id"] == 3
    content = json.loads(resp["result"]["content"][0]["text"])
    products = content["products"]
    types = [p["type"] for p in products]
    assert "universal_journal" in types
    assert "sales_documents" in types
    assert "financial_audit_and_compliance" in types


def test_mcp_tool_explain_field(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "explain_sap_field",
            "arguments": {"field_name": "belnr"},
        },
    }
    resp = mcp_server.process_rpc_request(req)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["match_count"] > 0
    assert any(
        "Accounting Document Number" in m["description"] or "document_number" in m["field_name"]
        for m in content["matches"]
    )


def test_mcp_tool_generate_grounded_sql(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "generate_grounded_sql",
            "arguments": {
                "product_type": "sales_documents",
                "project_id": "test-analytics-prj",
                "limit": 25,
            },
        },
    }
    resp = mcp_server.process_rpc_request(req)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert "SELECT" in content["sql"]
    assert "`test-analytics-prj.cortex7_data_products.sales_documents_" in content["sql"]
    assert "LIMIT 25" in content["sql"]
