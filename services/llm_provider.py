from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMProvider(ABC):
    @property
    @abstractmethod
    def model_info(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def normalize(self, source: str) -> Dict[str, Any]:
        pass
