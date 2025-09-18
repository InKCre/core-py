__all__ = ["get_embeddings", "one_chat", "multi_chat"]

import os
import typing
from typing import Annotated as Anno, Literal as Lit, Optional as Opt
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
    ChatCompletionToolMessageParam,
)

if typing.TYPE_CHECKING:
    from ..schemas.root import Vector


# Config
LLM_SP_AK = os.getenv("LLM_SP_AK", "")
LLM_SP_BASE_URL = os.getenv("LLM_SP_BASE_URL", "")

OPENAI_CLIENT = OpenAI(
    base_url=LLM_SP_BASE_URL,
    api_key=LLM_SP_AK,
)


class MessageContent:
    def __init__(self, content: str) -> None:
        self._content = content

    def __str__(self) -> str:
        return self._content

    def to_message(self, role: "Message.Role") -> "Message":
        return Message(
            role=role,
            content=self,
        )

    def contact(self, other: "MessageContent") -> "MessageContent":
        self._content += str(other)
        return self

    def format(self, **variables: typing.Any) -> None:
        self._content = self._content.format(**variables)


class Prompt(MessageContent):
    def __init__(self, prompt_name: str) -> None:
        with open(
            r"data/ai/prompts/{prompt_name}.txt".format(prompt_name=prompt_name),
            "r",
            encoding="utf-8",
        ) as f:
            super().__init__(f.read())


class CSVMessageContent(MessageContent):
    def __init__(
        self,
        header: typing.Iterable[str],
        rows: typing.Iterable[typing.Iterable[Opt[str]]],
    ) -> None:
        self._header = header
        self._rows = rows

    def __str__(self) -> str:
        lines = [",".join(self._header)]
        for row in self._rows:
            lines.append(",".join('""' if v is None else v for v in row))
        main = "\n".join(lines)
        return f"```csv\n{main}\n```"


class Message:
    type Role = Lit["user", "assistant", "system", "tool"]

    def __init__(
        self,
        role: Role,
        content: MessageContent,
    ) -> None:
        self._role = role
        self._content = content

    @property
    def content(self) -> str:
        return str(self._content)

    def to_openai(self) -> ChatCompletionMessageParam:
        if self._role == "user":
            return ChatCompletionUserMessageParam(
                role="user",
                content=str(self._content),
            )
        elif self._role == "system":
            return ChatCompletionSystemMessageParam(
                role="system",
                content=str(self._content),
            )
        elif self._role == "assistant":
            return ChatCompletionAssistantMessageParam(
                role="assistant",
                content=str(self._content),
            )
        raise ValueError(f"Unsupported role: {self._role}")


class Chat:
    def __init__(self, provider: str, model: str) -> None:
        self._provider = provider
        self._model = model
        self._messages: list[Message] = []

    def add_messages(self, *add_messages: Message) -> None:
        self._messages.extend(add_messages)

    def complete(self, *add_messages: Message, add_to_history: bool = False) -> Message:
        """补全

        :param add_messages: 追加的消息
        :param add_history: 是否将追加消息和模型回复添加到消息记录中
        """
        res = OPENAI_CLIENT.chat.completions.create(
            model=self._model,
            messages=tuple(msg.to_openai() for msg in self._messages)
            + tuple(msg.to_openai() for msg in add_messages),
            stream=False,
        )
        res_message = Message(
            role="assistant",
            content=MessageContent(res.choices[0].message.content or ""),
        )
        if add_to_history:
            self.add_messages(*add_messages, res_message)
        return res_message


class Embedding:
    def __init__(self, provider: str, model: str) -> None:
        self._provider = provider
        self._model = model

    def embed(self, text: str) -> "Vector":
        response = OPENAI_CLIENT.embeddings.create(
            model=self._model, input=text, encoding_format="float"
        )
        return tuple(response.data[0].embedding)


def get_embeddings(
    text: str,
    model: str = "baai/bge-m3",
    encoding_format: typing.Literal["float", "base64"] = "float",
) -> "Vector":
    response = OPENAI_CLIENT.embeddings.create(
        model=model, input=text, encoding_format=encoding_format
    )
    return tuple(response.data[0].embedding)


def one_chat(
    prompt: str | None = None,
    model: str = "deepseek/deepseek-v3-0324",
    history_messages: list[ChatCompletionUserMessageParam | ChatCompletionAssistantMessageParam]
    | None = None,
):
    chat_completion_res = OPENAI_CLIENT.chat.completions.create(
        model=model,
        messages=[
            ChatCompletionUserMessageParam(
                role="user",
                content=prompt,
            ),
            *(history_messages or []),
        ],
        stream=False,
    )
    return chat_completion_res.choices[0].message.content


def multi_chat(
    init_prompt: str | None = None, model: str = "deepseek/deepseek-v3-0324"
) -> typing.Callable[[str], str]:
    messages = []

    def wrapper(prompt: str) -> str:
        nonlocal messages

        if not messages:
            prompt = init_prompt + prompt
        messages.append(
            ChatCompletionUserMessageParam(
                role="user",
                content=prompt,
            )
        )
        response = one_chat(prompt=prompt, model=model, history_messages=messages)
        messages.append(
            ChatCompletionAssistantMessageParam(
                role="assistant",
                content=response,
            )
        )
        return response

    return wrapper


def one_chat_with_vlm(
    image_url: str,
    prompt: str,
    model: str = "qwen-vl-ocr-2025-04-13",
):
    completion = OPENAI_CLIENT.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        stream=False,
    )
    return completion.choices[0].message.content
