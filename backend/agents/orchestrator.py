from deepagents import create_deep_agent
from functools import lru_cache

from backend.config import get_settings

# Subagents
from backend.agents.subagents.doc_parser import DOC_PARSER_CONFIG
from backend.agents.subagents.quiz_generator import QUIZ_GEN_CONFIG
from backend.agents.subagents.qa_agent import QA_CONFIG
from backend.agents.subagents.analyst import ANALYST_CONFIG


@lru_cache
def get_orchestrator():
    """
    Returns a singleton Deep Agent orchestrator with all subagents.
    """

    settings = get_settings()

    # -----------------------------
    # Model Selection
    # -----------------------------
    # Default: Claude (recommended for deepagents)
    model = "anthropic:claude-sonnet-4-6"

    # Optional fallback to OpenAI
    if settings.OPENAI_API_KEY:
        model = "openai:gpt-4o"

    # -----------------------------
    # Create Deep Agent
    # -----------------------------
    agent = create_deep_agent(
        model=model,

        # Shared tools for main agent (keep minimal)
        tools=[],

        system_prompt="""
You are the main coordinator for an AI Study Assistant.

Your job is to:
- Understand user intent
- Delegate tasks to the correct subagent using the task() tool
- NEVER perform complex operations yourself

Delegation rules:
- Document processing → doc-parser
- Quiz generation → quiz-generator
- Q&A about documents → qa-agent
- Progress analysis & recommendations → progress-analyst

Strict rules:
- Always delegate when a subagent is suitable
- Do NOT hallucinate data
- Keep responses minimal and structured
""",

        subagents=[
            DOC_PARSER_CONFIG,
            QUIZ_GEN_CONFIG,
            QA_CONFIG,
            ANALYST_CONFIG,
        ],

        name="study-assistant-main",
    )

    return agent