import os
from oxygent import MAS, Config, oxy, preset_tools

Config.set_agent_llm_model("default_llm")

oxy_space = [
    # LLM模型
    oxy.HttpLLM(
        name="default_llm",
        api_key=os.getenv("DEFAULT_LLM_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
        llm_params={"temperature": 0.01},
        semaphore=4,
    ),
    
    # 浏览器工具
    oxy.StdioMCPClient(
        name="browser_tools",
        params={
            "command": "uv",
            "args": ["--directory", "./mcp_servers", "run", "browser/server.py"],
        }
    ),
    
    # 浏览器agent
    oxy.ReActAgent(
        name="browser_agent",
        desc="A tool for browser operations like visiting URLs, getting page content, and analyzing web pages",
        tools=["browser_tools"],
    ),
    
    # 文件工具和agent
    preset_tools.file_tools,
    oxy.ReActAgent(
        name="file_agent",
        desc="A tool that can operate the file system",
        tools=["file_tools"],
    ),
    
    # 主控制agent
    oxy.ReActAgent(
        is_master=True,
        name="master_agent",
        sub_agents=["browser_agent", "file_agent"],
    ),
]

async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="请打开百度搜索'北京天气'，提取天气信息并保存到weather.txt文件"
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())