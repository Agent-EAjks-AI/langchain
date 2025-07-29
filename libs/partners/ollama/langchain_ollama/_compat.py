"""V1 message conversion utilities for Ollama."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from langchain_core.messages import content_blocks as types
from langchain_core.messages.content_blocks import (
    ImageContentBlock,
    ReasoningContentBlock,
    TextContentBlock,
    ToolCall,
)
from langchain_core.messages.v1 import AIMessage as AIMessageV1
from langchain_core.messages.v1 import AIMessageChunk as AIMessageChunkV1
from langchain_core.messages.v1 import HumanMessage as HumanMessageV1
from langchain_core.messages.v1 import MessageV1, ResponseMetadata
from langchain_core.messages.v1 import SystemMessage as SystemMessageV1
from langchain_core.messages.v1 import ToolMessage as ToolMessageV1


def _convert_from_v1_to_ollama_format(message: MessageV1) -> dict[str, Any]:
    """Convert v1 message to Ollama API format."""
    if isinstance(message, HumanMessageV1):
        return _convert_human_message_v1(message)
    if isinstance(message, AIMessageV1):
        return _convert_ai_message_v1(message)
    if isinstance(message, SystemMessageV1):
        return _convert_system_message_v1(message)
    if isinstance(message, ToolMessageV1):
        return _convert_tool_message_v1(message)
    msg = f"Unsupported message type: {type(message)}"
    raise ValueError(msg)


def _convert_content_blocks_to_ollama_format(
    content: list[types.ContentBlock],
) -> tuple[str, list[str], list[dict[str, Any]]]:
    """Convert v1 content blocks to Ollama API format.

    Returns:
        Tuple of (text_content, images, tool_calls)
    """
    text_content = ""
    images = []
    tool_calls = []

    for block in content:
        block_type = block.get("type")
        if block_type == "text":
            text_block = cast(TextContentBlock, block)
            text_content += text_block["text"]
        elif block_type == "image":
            image_block = cast(ImageContentBlock, block)
            if image_block.get("source_type") == "base64":
                images.append(image_block.get("data", ""))
            else:
                msg = "Only base64 image data is supported by Ollama"
                raise ValueError(msg)
        elif block_type == "audio":
            msg = "Audio content blocks are not supported by Ollama"
            raise ValueError(msg)
        elif block_type == "tool_call":
            tool_call_block = cast(ToolCall, block)
            tool_calls.append(
                {
                    "type": "function",
                    "id": tool_call_block["id"],
                    "function": {
                        "name": tool_call_block["name"],
                        "arguments": tool_call_block["args"],
                    },
                }
            )
        # Skip other content block types that aren't supported

    return text_content, images, tool_calls  # type: ignore[return-value]


def _convert_human_message_v1(message: HumanMessageV1) -> dict[str, Any]:
    """Convert HumanMessageV1 to Ollama format."""
    text_content, images, _ = _convert_content_blocks_to_ollama_format(message.content)

    msg: dict[str, Any] = {
        "role": "user",
        "content": text_content,
        "images": images,
    }
    if message.name:
        # Ollama doesn't have direct name support, include in content
        msg["content"] = f"[{message.name}]: {text_content}"

    return msg


def _convert_ai_message_v1(message: AIMessageV1) -> dict[str, Any]:
    """Convert AIMessageV1 to Ollama format."""
    text_content, _, tool_calls = _convert_content_blocks_to_ollama_format(
        message.content
    )

    msg: dict[str, Any] = {
        "role": "assistant",
        "content": text_content,
    }

    if tool_calls:
        msg["tool_calls"] = tool_calls

    if message.name:
        # Ollama doesn't have direct name support, include in content
        msg["content"] = f"[{message.name}]: {text_content}"

    return msg


def _convert_system_message_v1(message: SystemMessageV1) -> dict[str, Any]:
    """Convert SystemMessageV1 to Ollama format."""
    text_content, _, _ = _convert_content_blocks_to_ollama_format(message.content)

    return {
        "role": "system",
        "content": text_content,
    }


def _convert_tool_message_v1(message: ToolMessageV1) -> dict[str, Any]:
    """Convert ToolMessageV1 to Ollama format."""
    text_content, _, _ = _convert_content_blocks_to_ollama_format(message.content)

    return {
        "role": "tool",
        "content": text_content,
        "tool_call_id": message.tool_call_id,
    }


def _convert_to_v1_from_ollama_format(response: dict[str, Any]) -> AIMessageV1:
    """Convert Ollama API response to AIMessageV1."""
    content: list[types.ContentBlock] = []

    # Handle text content
    if "message" in response and "content" in response["message"]:
        text_content = response["message"]["content"]
        if text_content:
            content.append(TextContentBlock(type="text", text=text_content))

    # Handle reasoning content first (should come before main response)
    if "message" in response and "thinking" in response["message"]:
        thinking_content = response["message"]["thinking"]
        if thinking_content:
            content.append(
                ReasoningContentBlock(
                    type="reasoning",
                    reasoning=thinking_content,
                )
            )

    # Handle tool calls
    if "message" in response and "tool_calls" in response["message"]:
        tool_calls = response["message"]["tool_calls"]
        content.extend(
            [
                ToolCall(
                    type="tool_call",
                    id=tool_call.get("id", str(uuid4())),
                    name=tool_call["function"]["name"],
                    args=tool_call["function"]["arguments"],
                )
                for tool_call in tool_calls
            ]
        )

    # Build response metadata
    response_metadata = ResponseMetadata()
    if "model" in response:
        response_metadata["model_name"] = response["model"]
    if "created_at" in response:
        response_metadata["created_at"] = response["created_at"]  # type: ignore[typeddict-unknown-key]
    if "done" in response:
        response_metadata["done"] = response["done"]  # type: ignore[typeddict-unknown-key]
    if "done_reason" in response:
        response_metadata["done_reason"] = response["done_reason"]  # type: ignore[typeddict-unknown-key]
    if "total_duration" in response:
        response_metadata["total_duration"] = response["total_duration"]  # type: ignore[typeddict-unknown-key]
    if "load_duration" in response:
        response_metadata["load_duration"] = response["load_duration"]  # type: ignore[typeddict-unknown-key]
    if "prompt_eval_count" in response:
        response_metadata["prompt_eval_count"] = response["prompt_eval_count"]  # type: ignore[typeddict-unknown-key]
    if "prompt_eval_duration" in response:
        response_metadata["prompt_eval_duration"] = response["prompt_eval_duration"]  # type: ignore[typeddict-unknown-key]
    if "eval_count" in response:
        response_metadata["eval_count"] = response["eval_count"]  # type: ignore[typeddict-unknown-key]
    if "eval_duration" in response:
        response_metadata["eval_duration"] = response["eval_duration"]  # type: ignore[typeddict-unknown-key]

    return AIMessageV1(
        content=content,
        response_metadata=response_metadata,
    )


def _convert_chunk_to_v1(chunk: dict[str, Any]) -> AIMessageChunkV1:
    """Convert Ollama streaming chunk to AIMessageChunkV1."""
    content: list[types.ContentBlock] = []

    # Handle reasoning content first in chunks
    if "message" in chunk and "thinking" in chunk["message"]:
        thinking_content = chunk["message"]["thinking"]
        if thinking_content:
            content.append(
                ReasoningContentBlock(
                    type="reasoning",
                    reasoning=thinking_content,
                )
            )

    # Handle streaming text content
    if "message" in chunk and "content" in chunk["message"]:
        text_content = chunk["message"]["content"]
        if text_content:
            content.append(TextContentBlock(type="text", text=text_content))

    # Handle streaming tool calls
    if "message" in chunk and "tool_calls" in chunk["message"]:
        tool_calls = chunk["message"]["tool_calls"]
        content.extend(
            [
                ToolCall(
                    type="tool_call",
                    id=tool_call.get("id", str(uuid4())),
                    name=tool_call.get("function", {}).get("name", ""),
                    args=tool_call.get("function", {}).get("arguments", {}),
                )
                for tool_call in tool_calls
            ]
        )

    # Build response metadata for final chunks
    response_metadata = None
    if chunk.get("done") is True:
        response_metadata = ResponseMetadata()
        if "model" in chunk:
            response_metadata["model_name"] = chunk["model"]
        if "created_at" in chunk:
            response_metadata["created_at"] = chunk["created_at"]  # type: ignore[typeddict-unknown-key]
        if "done_reason" in chunk:
            response_metadata["done_reason"] = chunk["done_reason"]  # type: ignore[typeddict-unknown-key]
        if "total_duration" in chunk:
            response_metadata["total_duration"] = chunk["total_duration"]  # type: ignore[typeddict-unknown-key]
        if "load_duration" in chunk:
            response_metadata["load_duration"] = chunk["load_duration"]  # type: ignore[typeddict-unknown-key]
        if "prompt_eval_count" in chunk:
            response_metadata["prompt_eval_count"] = chunk["prompt_eval_count"]  # type: ignore[typeddict-unknown-key]
        if "prompt_eval_duration" in chunk:
            response_metadata["prompt_eval_duration"] = chunk["prompt_eval_duration"]  # type: ignore[typeddict-unknown-key]
        if "eval_count" in chunk:
            response_metadata["eval_count"] = chunk["eval_count"]  # type: ignore[typeddict-unknown-key]
        if "eval_duration" in chunk:
            response_metadata["eval_duration"] = chunk["eval_duration"]  # type: ignore[typeddict-unknown-key]

    return AIMessageChunkV1(
        content=content,
        response_metadata=response_metadata or ResponseMetadata(),
    )
