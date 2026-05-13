import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main() -> None:
    async with streamablehttp_client("http://127.0.0.1:8000/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            result = await session.call_tool(
                "analyze_sentiment",
                {"text": "삼성전자 3분기 영업이익 시장 기대치 상회"},
            )
            print("Result:", result.structuredContent or result.content)


if __name__ == "__main__":
    asyncio.run(main())
