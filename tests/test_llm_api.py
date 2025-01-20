# -*- coding: utf-8 -*-
# @Time    : 2025/1/1
# @Author  : wenshao
# @Email   : wenshaoguo1026@gmail.com
# @Project : browser-use-webui
# @FileName: test_llm_api.py
import os
import pdb
import pytest

from dotenv import load_dotenv

load_dotenv()

import sys

sys.path.append(".")


def test_openai_model():
    from langchain_core.messages import HumanMessage
    from src.utils import utils

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")

    llm = utils.get_llm_model(
        provider="openai",
        model_name="gpt-4o",
        temperature=0.8,
        base_url=os.getenv("OPENAI_ENDPOINT", ""),
        api_key=api_key
    )
    image_path = "assets/examples/test.png"
    image_data = utils.encode_image(image_path)
    message = HumanMessage(
        content=[
            {"type": "text", "text": "describe this image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ]
    )
    ai_msg = llm.invoke([message])
    print(ai_msg.content)


def test_gemini_model():
    # you need to enable your api key first: https://ai.google.dev/palm_docs/oauth_quickstart
    from langchain_core.messages import HumanMessage
    from src.utils import utils

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not set")

    llm = utils.get_llm_model(
        provider="gemini",
        model_name="gemini-1.5-pro",
        temperature=0.8,
        api_key=api_key
    )

    image_path = "assets/examples/test.png"
    image_data = utils.encode_image(image_path)
    message = HumanMessage(
        content=[
            {"type": "text", "text": "describe this image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ]
    )
    ai_msg = llm.invoke([message])
    print(ai_msg.content)


def test_azure_openai_model():
    from langchain_core.messages import HumanMessage
    from src.utils import utils

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not api_key or not endpoint:
        pytest.skip("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT not set")

    llm = utils.get_llm_model(
        provider="azure_openai",
        model_name="gpt-4",
        temperature=0.8,
        base_url=endpoint,
        api_key=api_key
    )
    image_path = "assets/examples/test.png"
    image_data = utils.encode_image(image_path)
    message = HumanMessage(
        content=[
            {"type": "text", "text": "describe this image"},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ]
    )
    ai_msg = llm.invoke([message])
    print(ai_msg.content)


def test_deepseek_model():
    from langchain_core.messages import HumanMessage
    from src.utils import utils

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        pytest.skip("DEEPSEEK_API_KEY not set")

    llm = utils.get_llm_model(
        provider="deepseek",
        model_name="deepseek-chat",
        temperature=0.8,
        base_url=os.getenv("DEEPSEEK_ENDPOINT", ""),
        api_key=api_key
    )
    message = HumanMessage(
        content=[
            {"type": "text", "text": "who are you?"}
        ]
    )
    ai_msg = llm.invoke([message])
    print(ai_msg.content)


def test_anthropic_model():
    from langchain_core.messages import HumanMessage
    from src.utils import utils

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not set")

    llm = utils.get_llm_model(
        provider="anthropic",
        model_name="claude-3-5-sonnet-latest",
        temperature=0.8,
        api_key=api_key
    )
    message = HumanMessage(
        content=[
            {"type": "text", "text": "who are you?"}
        ]
    )
    ai_msg = llm.invoke([message])
    print(ai_msg.content)


def test_ollama_model():
    from langchain_ollama import ChatOllama

    # Check if Ollama is running by trying to connect to its default port
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        result = sock.connect_ex(('localhost', 11434))
        if result != 0:
            pytest.skip("Ollama server not running on localhost:11434")
    finally:
        sock.close()

    llm = ChatOllama(model="qwen2.5:7b")
    ai_msg = llm.invoke("Sing a ballad of LangChain.")
    print(ai_msg.content)


if __name__ == '__main__':
    # test_openai_model()
    # test_gemini_model()
    # test_azure_openai_model()
    # test_deepseek_model()
    # test_anthropic_model()
    test_ollama_model()
