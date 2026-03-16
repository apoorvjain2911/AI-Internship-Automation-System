# llm_factory.py

import os
from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama


def get_llm():
    """
    Returns LLM based on environment variable.
    Default = OpenAI.
    """

    provider = os.getenv("LLM_PROVIDER", "openai")

    if provider == "openai":
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )

    elif provider == "ollama":
        return ChatOllama(
            model="llama3",
            temperature=0
        )

    else:
        raise ValueError("Unsupported LLM provider")