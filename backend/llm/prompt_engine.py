from typing import List, Dict
from .prompt_templates import NBA_SYSTEM_PROMPT, CHAT_PROMPT_TEMPLATE


class PromptEngine:
    """
    Builds structured prompts for LLMs.
    """

    def build_chat_prompt(self, query: str, context: str = "") -> List[Dict[str, str]]:
        user_content = CHAT_PROMPT_TEMPLATE.format(
            context=context or "No context available",
            query=query
        )

        return [
            {"role": "system", "content": NBA_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def build_agent_prompt(self, state: dict) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": NBA_SYSTEM_PROMPT},
            {"role": "user", "content": str(state)}
        ]
