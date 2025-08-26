import asyncio
import json

from oxygent import MAS, Config, OxyRequest, OxyResponse, oxy
from oxygent.preset_tools import file_tools
from oxygent.schemas import LLMResponse, LLMState
from oxygent.utils.common_utils import extract_first_json
from oxygent.utils.env_utils import get_env_var


def func_parse_llm_response(ori_response: str, oxy_request: OxyRequest) -> LLMResponse:
    try:
        if "</think>" in ori_response:
            ori_response = ori_response.split("</think>")[-1].strip()
        tool_call_dict = json.loads(extract_first_json(ori_response))
        if "tool_name" in tool_call_dict:
            return LLMResponse(
                state=LLMState.TOOL_CALL,
                output=tool_call_dict,
                ori_response=ori_response,
            )
        return LLMResponse(
            state=LLMState.ANSWER, output=ori_response, ori_response=ori_response
        )
    except json.JSONDecodeError:
        if all(tk in ori_response for tk in ["tool_name", "arguments", "{", "}"]):
            return LLMResponse(
                state=LLMState.ERROR_PARSE,
                output="can not parse json, please regenerate the answer.",
                ori_response=ori_response,
            )
        return LLMResponse(
            state=LLMState.ANSWER, output=ori_response, ori_response=ori_response
        )
    except Exception as e:
        return LLMResponse(
            state=LLMState.ERROR_PARSE, output=e, ori_response=ori_response
        )


async def master_file_workflow(oxy_request: OxyRequest) -> OxyResponse:
    resp = await oxy_request.call(
        callee="file_react_agent",
        arguments={
            "query": oxy_request.get_query(),
            "attachments": oxy_request.arguments.get("attachments", []),
        },
    )
    return resp.output


Config.set_agent_llm_model("default_chat")

oxy_space = [
    oxy.HttpLLM(
        name="default_chat",
        api_key=get_env_var("DEFAULT_LLM_API_KEY"),
        base_url=get_env_var("DEFAULT_LLM_BASE_URL"),
        model_name=get_env_var("DEFAULT_LLM_MODEL_NAME"),
        llm_params={"temperature": 0.3, "max_tokens": 2048},
    ),
    file_tools,
    oxy.ReActAgent(
        name="file_react_agent",
        llm_name="default_chat",
        tools=["file_tools"],  # make sure the docx tools is avaliable
        func_parse_llm_response=func_parse_llm_response,
    ),
    oxy.Workflow(
        name="file_master_agent",
        is_master=True,
        permitted_tool_name_list=["file_react_agent"],
        func_workflow=master_file_workflow,
    ),
]


async def main():
    async with MAS(oxy_space=oxy_space) as mas:
        payload = {
            "query": "Introduce the content of the file",
            "attachments": ["file.docx"],
        }
        oxy_response = await mas.chat_with_agent(payload=payload)
        print("LLM: ", oxy_response.output)


async def web():
    async with MAS(oxy_space=oxy_space) as mas:
        await mas.start_web_service(first_query="Introduce the content of the file")


if __name__ == "__main__":
    # asyncio.run(main())
    asyncio.run(web())
