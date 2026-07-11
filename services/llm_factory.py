import os

from services.llm_provider import LLMProvider
from services.groq_strategy import GroqStrategy
from services.ollama_strategy import OllamaStrategy


class LLMFactory:
    @staticmethod
    def create() -> LLMProvider:
        provider = os.getenv("LLM_PROVIDER").lower().strip()

        if provider == "groq":
            return GroqStrategy()
        elif provider == "ollama":
            return OllamaStrategy()
        else:
            raise ValueError(
                f"LLM_PROVIDER desconocido: '{provider}'. "
                f"Valores válidos: 'groq', 'ollama'."
            )
