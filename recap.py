import click
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from tools import VideoTranscriber
from langchain.agents import AgentExecutor, create_tool_calling_agent


@click.command()
@click.argument("video_url")
def run(video_url: str):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "You are a helpful assistant"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    model = ChatVertexAI(model_name="gemini-pro")
    tools = [VideoTranscriber()]
    agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    agent_executor.invoke({"input": f"Resume this video {video_url}"})


if __name__ == "__main__":
    run()
