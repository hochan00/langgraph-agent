from langchain_core.prompts import ChatPromptTemplate, load_prompt


def prompt(filename: str) -> ChatPromptTemplate:
    yaml_prompt = load_prompt(f"api/prompts/{filename}", encoding="utf-8")
    return ChatPromptTemplate.from_messages([("human", yaml_prompt.template)])


RAG_PROMPT = prompt("rag.yaml")
