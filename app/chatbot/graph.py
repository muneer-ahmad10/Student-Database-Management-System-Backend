"""
LangGraph chatbot agent.

Builds a small ReAct-style graph:

    START -> agent (Gemini + tools) -> [tools?] -> agent -> ... -> END

The agent node calls Gemini (via langchain-google-genai). If Gemini's
response includes tool calls, we route to the `tools` node which executes
them against the student database (see chatbot/tools.py), feeds the
results back to the agent, and loops until Gemini produces a final answer.

The graph is compiled once and reused across requests; conversation state
(message history) is passed in per-call rather than kept in module state,
so the same compiled graph safely serves many concurrent chat sessions.
"""
from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from app.config import settings
from app.chatbot.tools import ALL_TOOLS

SYSTEM_PROMPT = """You are the AI assistant for a Student Database Management System.
You help staff and students query student records, courses, enrollments, and grades.

Rules:
- Always use the provided tools to look up real data — never invent student names, grades, or IDs.
- For fuzzy/interest-based questions (e.g. "who's into AI"), use the semantic search tool.
- For exact lookups (by name, ID, course code), use the direct database tools.
- Keep answers concise and cite student IDs / course codes when relevant.
- You cannot create, update, or delete records — you are read-only. If asked to modify data,
  explain that changes must be made via the REST API (e.g. POST /api/v1/students).
"""


class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def _build_llm() -> ChatGoogleGenerativeAI:
    if not settings.GOOGLE_API_KEY:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add your Gemini API key to the .env file "
            "to enable the chatbot."
        )
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_CHAT_MODEL,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=0.2,
    ).bind_tools(ALL_TOOLS)


def _agent_node(state: ChatState) -> dict:
    llm = _build_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def build_graph():
    graph = StateGraph(ChatState)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


def run_chat(user_message: str, history: list[dict] | None = None) -> dict:
    """
    Runs one turn of the chatbot.

    `history` is an optional list of {"role": "user"|"assistant", "content": str}
    from a previous turn, allowing the caller (API layer) to maintain multi-turn
    context without the server holding session state in memory.

    Returns {"answer": str, "messages": [...]} where messages is the serialized
    trace of the turn (useful for debugging / showing tool calls in a UI).
    """
    graph = get_graph()

    messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]
    for turn in history or []:
        if turn["role"] == "user":
            messages.append(HumanMessage(content=turn["content"]))
        else:
            from langchain_core.messages import AIMessage

            messages.append(AIMessage(content=turn["content"]))
    messages.append(HumanMessage(content=user_message))

    result = graph.invoke({"messages": messages})
    final_message = result["messages"][-1]

    trace = [
        {"type": m.__class__.__name__, "content": getattr(m, "content", "")}
        for m in result["messages"]
    ]
    return {"answer": final_message.content, "trace": trace}
