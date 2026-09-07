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

"""Cortex Model Context Protocol (MCP) Server for Gemini Agent Grounding."""

import argparse
import json
import sys
from typing import Any

from common.mcp.query_generator import CortexQueryGenerator
from common.mcp.schema_provider import CortexSchemaProvider


class CortexMCPServer:
    """Standard JSON-RPC 2.0 Stdio Model Context Protocol Server."""

    def __init__(self) -> None:
        self.schema_provider = CortexSchemaProvider()
        self.query_generator = CortexQueryGenerator(self.schema_provider)
        self.tools = self._register_tools()

    def _register_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "list_cortex_data_products",
                "description": (
                    "Lists all available Google Cloud Cortex data products across ERP domains "
                    "(Finance, Sales, Supply Chain, Audit)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_data_product_schema",
                "description": (
                    "Retrieves the full semantic schema, table definitions, "
                    "and column descriptions for a specific Cortex data product."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_type": {
                            "type": "string",
                            "description": (
                                "The unique type name of the data product "
                                "(e.g., 'universal_journal', 'sales_documents')."
                            ),
                        }
                    },
                    "required": ["product_type"],
                },
            },
            {
                "name": "explain_sap_field",
                "description": (
                    "Translates cryptic SAP abbreviations "
                    "(e.g., 'BELNR', 'BUKRS', 'DMBTR', 'MANDT') "
                    "into human-readable business definitions and product locations."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "field_name": {
                            "type": "string",
                            "description": "The SAP field name or suffix to look up.",
                        }
                    },
                    "required": ["field_name"],
                },
            },
            {
                "name": "generate_grounded_sql",
                "description": (
                    "Generates a grounded, verified BigQuery SQL query template "
                    "for a Cortex data product."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_type": {
                            "type": "string",
                            "description": "The target data product type.",
                        },
                        "table_name": {
                            "type": "string",
                            "description": "Optional specific table name within the product.",
                        },
                        "project_id": {
                            "type": "string",
                            "description": "GCP Project ID hosting the deployed BigQuery datasets.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of rows to return (default: 50).",
                        },
                    },
                    "required": ["product_type"],
                },
            },
        ]

    def handle_tool_call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Dispatches an MCP tool call."""
        if name == "list_cortex_data_products":
            return {"products": self.schema_provider.list_products()}

        elif name == "get_data_product_schema":
            p_type = args.get("product_type", "")
            schema = self.schema_provider.get_product_schema(p_type)
            if not schema:
                return {"error": f"Product '{p_type}' not found."}
            return schema

        elif name == "explain_sap_field":
            f_name = args.get("field_name", "")
            matches = self.schema_provider.explain_field(f_name)
            return {"field": f_name, "matches": matches, "match_count": len(matches)}

        elif name == "generate_grounded_sql":
            p_type = args.get("product_type", "")
            t_name = args.get("table_name")
            proj_id = args.get("project_id", "YOUR_PROJECT_ID")
            limit = args.get("limit", 50)
            return self.query_generator.generate_sample_query(
                product_type=p_type,
                table_name=t_name,
                project_id=proj_id,
                limit=limit,
            )

        return {"error": f"Unknown tool: {name}"}

    def process_rpc_request(self, request: dict[str, Any]) -> dict[str, Any] | None:
        """Processes a single JSON-RPC 2.0 request."""
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "cortex-mcp-server",
                        "version": "7.0.4",
                    },
                    "capabilities": {
                        "tools": {"listChanged": False},
                    },
                },
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.tools},
            }

        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            res = self.handle_tool_call(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2),
                        }
                    ]
                },
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        # Notifications (no id) return None
        if req_id is None:
            return None

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"},
        }

    def run_stdio_loop(self) -> None:
        """Runs the standard I/O communication loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.process_rpc_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {e}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


def main() -> None:
    parser = argparse.ArgumentParser(description="Google Cloud Cortex MCP Server.")
    parser.add_argument(
        "--list-tools", action="store_true", help="List registered MCP tools and exit."
    )
    parser.add_argument("--explain", type=str, help="Explain a specific SAP field and exit.")
    args = parser.parse_args()

    server = CortexMCPServer()

    if args.list_tools:
        print(json.dumps(server.tools, indent=2))
        return

    if args.explain:
        result = server.handle_tool_call("explain_sap_field", {"field_name": args.explain})
        print(json.dumps(result, indent=2))
        return

    server.run_stdio_loop()


if __name__ == "__main__":
    main()
