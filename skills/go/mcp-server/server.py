"""
go MCP Server — 最小验证版
只暴露一个 go_ping 工具，验证 ZCode 能否发现和调用
"""
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

server = Server("go-orchestrator")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="go_ping",
            description="测试工具: 返回 pong + 当前时间",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要回显的消息"
                    }
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    if name == "go_ping":
        import datetime
        msg = arguments.get("message", "")
        result = json.dumps({
            "pong": True,
            "echo": msg,
            "time": datetime.datetime.now().isoformat()
        })
        return [types.TextContent(type="text", text=result)]
    return [types.TextContent(type="text", text=f"未知工具: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
