import asyncio
import os
import importlib
import sys

from pydantic import Field

from oxygent import MAS, Config, OxyRequest, OxyResponse, oxy
from oxygent.prompts import INTENTION_PROMPT

Config.set_agent_llm_model("default_llm")


async def workflow(oxy_request: OxyRequest):
    short_memory = oxy_request.get_short_memory()
    print("--- History record --- :", short_memory)
    master_short_memory = oxy_request.get_short_memory(master_level=True)
    print("--- History record-User layer --- :", master_short_memory)
    print("user query:", oxy_request.get_query(master_level=True))
    await oxy_request.send_message("msg")
    oxy_response = await oxy_request.call(
        callee="time_agent",
        arguments={"query": "What time is it now in Asia/Shanghai?"},
    )
    print("--- Current time --- :", oxy_response.output)
    oxy_response = await oxy_request.call(
        callee="default_llm",
        arguments={
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
            "llm_params": {"temperature": 0.6},
        },
    )
    print(oxy_response.output)
    import re

    numbers = re.findall(r"\d+", oxy_request.get_query())
    if numbers:
        n = numbers[-1]
        oxy_response = await oxy_request.call(callee="calc_pi", arguments={"prec": n})
        return f"Save {n} positions: {oxy_response.output}"
    else:
        return "Save 2 positions: 3.14, or you could ask me to save how many positions you want."


def update_query(oxy_request: OxyRequest) -> OxyRequest:
    print(oxy_request.shared_data)
    user_query = oxy_request.get_query(master_level=True)
    current_query = oxy_request.get_query()
    print(user_query + "\n" + current_query)
    oxy_request.arguments["who"] = oxy_request.callee
    return oxy_request


def format_output(oxy_response: OxyResponse) -> OxyResponse:
    oxy_response.output = "Answer: " + oxy_response.output
    return oxy_response


oxy_space = [
    oxy.HttpLLM(
        name="default_llm",
        api_key=os.getenv("DEFAULT_LLM_API_KEY"),
        base_url=os.getenv("DEFAULT_LLM_BASE_URL"),
        model_name=os.getenv("DEFAULT_LLM_MODEL_NAME"),
        llm_params={"temperature": 0.01},
        semaphore=4,
    ),
    oxy.ChatAgent(name="intent_agent", prompt=INTENTION_PROMPT),
    oxy.StdioMCPClient(
        name="time",
        params={
            "command": "uvx",
            "args": ["mcp-server-time", "--local-timezone=Asia/Shanghai"],
        },
    ),
    oxy.StdioMCPClient(
        name="filesystem",
        params={
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "./local_file"],
        },
    ),
    oxy.StdioMCPClient(
        name="my_tools",
        params={
            "command": "uv",
            "args": ["--directory", "./mcp_servers", "run", "my_tools.py"],
        },
    ),
    # 添加浏览器MCP客户端
    oxy.StdioMCPClient(
        name="browser_tools",
        params={
            "command": "uv",
            "args": ["--directory", "./mcp_servers", "run", "browser_tools.py"],
        },
    ),
    oxy.ReActAgent(
        name="master_agent",
        sub_agents=[
            "time_agent",
            "file_agent",
            "math_agent",
            "browser_agent",
        ],  # 添加browser_agent到子代理列表
        is_master=True,
        func_format_output=format_output,
        timeout=100,
        llm_model="default_llm",
    ),
    oxy.ReActAgent(
        name="time_agent",
        desc="A tool for time query.",
        tools=["time"],
        func_process_input=update_query,
        trust_mode=False,
        timeout=10,
    ),
    oxy.ReActAgent(
        name="file_agent",
        desc="A tool for file operation.",
        tools=["filesystem"],
    ),
    oxy.WorkflowAgent(
        name="math_agent",
        desc="A tool for pi query",
        sub_agents=["time_agent"],
        tools=["my_tools"],
        func_workflow=workflow,
        is_retain_master_short_memory=True,
    ),
    # 使用MCP客户端的browser_agent
    oxy.ReActAgent(
        name="browser_agent",
        desc="A tool for browser operations like visiting URLs, getting page content, and analyzing web pages.",
        tools=["browser_tools"],  # 使用browser_tools MCP客户端
        timeout=30,
    ),
]


async def main():
    """
    Method 1:
        mas = await MAS.create(oxy_space=oxy_space)
    call directly:
        await mas.call(callee = 'joke_tool', arguments = {'joke_type': 'comic'})
    call as a cli:
        await mas.start_cli_mode(first_query='Get what time it is and save in `log.txt` under `/local_file`')
        await mas.start_web_service(first_query='Get what time it is and save in `log.txt` under `/local_file`')
        await mas.start_batch_processing(['Hello', 'What time is it now', '200 positions of Pi', 'Get what time it is and save in `log.txt` under `/local_file`'])
        await mas.start_batch_processing(['Hello'] * 10)
    """
    # Method 2
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(
            first_query="搜索‘武汉市天气’，提取搜索结果的天气概览数据保存到`./local_file/weather-{今天日期}.txt`"
        )


if __name__ == "__main__":
    asyncio.run(main())
