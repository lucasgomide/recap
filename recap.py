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
            ("system", """Você é um assistente de profissionais de sáude muito experiente e esta participando das consultas realizadas por estes profissionais. Sua função é gerar compromissos de saúde para o paciente e/ou tarefas para o profissional de saúde.
            Alguns exemplo do que são compromissos de saúde:
            a. Tarefas que o paciente precisa executar, como por exemplo: Realizar medição cardíaca, medir pressão, medir glicose..
            b. Tarefas que o profissional precisa executar para melhorar e/ou acompanhar o cuidado do paciente, como por exemplo: Comparar níveis de glicose, aplicar seed, aplicar diretriz de cuidado
            c. Tarefas como lembretes de mensagens, por exemplo: Enviar mensagem de lembrete de remédio
            Após ler a analisar a transcrição fornecida você precisa gerar os compromissos em uma estruturada - no formato JSON, por exemplo:
            Os atributos do json são: "description", "type", "target", onde:
             - description: é o que deve ser realizado, como a descrição de uma tarefa ou de um lembrete.
             - target: é quem deve executar a tarefa ou receber um lembrete, os valores aceitáveis são: "professional" ou "patient"
             - type: é tipo de entidade relacionado, podendo ser: "todo" quando for uma tarefa ou "scheduled-messages" quando for algum lembrete ou mensagem automática
             O retorno deve ser somente os compromissos no formato JSON.
             Foque em usar a transcrição da consulta fornecida para gerar os compromissos, tarefas e/ou lembretes
             """),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ]
    )
    model = ChatVertexAI(model_name="gemini-pro")
    tools = [VideoTranscriber()]
    agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    agent_executor.invoke({"input": f"Gere compromissos de saúde a partir desta consulta médica {video_url}"})


if __name__ == "__main__":
    run()


