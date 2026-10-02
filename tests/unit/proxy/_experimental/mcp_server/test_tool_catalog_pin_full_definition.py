from mcp.types import Tool, ToolAnnotations

from litellm.proxy._experimental.mcp_server.tool_catalog_guard import (
    pin_tool_catalog,
    snapshot_pinned_tool,
)
from litellm.types.mcp_server.mcp_server_manager import PinnedMCPTool


_INPUT_SCHEMA = {
    "type": "object",
    "properties": {"env": {"type": "string"}},
}


def _tool(*, readonly: bool, output_key: str) -> Tool:
    return Tool(
        name="deploy",
        description="Deploy the service",
        inputSchema=_INPUT_SCHEMA,
        outputSchema={
            "type": "object",
            "properties": {output_key: {"type": "string"}},
        },
        annotations=ToolAnnotations(
            readOnlyHint=readonly,
            destructiveHint=not readonly,
            idempotentHint=readonly,
            openWorldHint=not readonly,
        ),
    )


def test_snapshot_covers_annotations_and_output_schema():
    pinned = snapshot_pinned_tool(_tool(readonly=True, output_key="status"))

    assert pinned.tool_definition is not None
    assert pinned.tool_definition["outputSchema"] == {
        "type": "object",
        "properties": {"status": {"type": "string"}},
    }
    assert pinned.tool_definition["annotations"]["readOnlyHint"] is True
    assert pinned.tool_definition["annotations"]["destructiveHint"] is False


def test_full_pin_detects_drift_and_serves_pinned_definition():
    original = _tool(readonly=True, output_key="status")
    changed = _tool(readonly=False, output_key="exfil")

    served, drift = pin_tool_catalog(
        [changed],
        {"deploy": snapshot_pinned_tool(original)},
    )

    assert drift is not None
    assert drift.changed == ("deploy",)
    assert served[0].annotations == original.annotations
    assert served[0].output_schema == original.output_schema
    assert served[0].input_schema == original.input_schema


def test_legacy_pin_keeps_legacy_comparison_behavior():
    original = _tool(readonly=True, output_key="status")
    changed = _tool(readonly=False, output_key="exfil")
    legacy_pin = PinnedMCPTool(
        description=original.description or "",
        input_schema=original.input_schema,
    )

    served, drift = pin_tool_catalog([changed], {"deploy": legacy_pin})

    assert drift is None
    assert served == (changed,)
