from typing import Dict, Any, List


class MergeService:
    def merge(
        self,
        automata_tokens: List[Dict[str, Any]],
        llm_tokens: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        cleaned_automata = [
            token for token in automata_tokens
            if token.get("token") != "UNKNOWN"
        ]
        merged = cleaned_automata + [
            token for token in llm_tokens
            if token.get("position", -1) != -1
        ]
        merged.sort(key=lambda item: item.get("position", 0))
        return merged
