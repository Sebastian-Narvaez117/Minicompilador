import re


class Automata:
    """Autómata Finito Determinista (AFD) para análisis léxico.
    Reconoce tokens mediante expresiones regulares.
    Solo reconoce NUMERO y PREPOSICION_A; el resto lo marca UNKNOWN.
    Los tokens UNKNOWN se filtran y el LLM los reconoce después.
    """

    TOKEN_PATTERNS = [
        ("NUMERO", r"\d+(\.\d+)?"),
        ("PREPOSICION_A", r"\ba\b"),
        ("SPACE", r"\s+"),
        ("UNKNOWN", r"[^\s]+"),
    ]

    def analyze(self, source: str):
        """Analiza el texto y retorna lista de tokens detectados."""
        pattern = "|".join(
            f"(?P<{name}>{regex})"
            for name, regex in self.TOKEN_PATTERNS
        )

        tokens = []

        for match in re.finditer(pattern, source, re.IGNORECASE):
            token_type = match.lastgroup
            token_value = match.group()

            if token_type == "SPACE":
                continue

            tokens.append({
                "token": token_type,
                "lexeme": token_value,
                "position": match.start(),
                "length": len(token_value),
                "source": "AFD",
            })

        return tokens
