import time
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Dict, Any

from models.automata import Automata
from services.llm_factory import LLMFactory
from services.syntax_service import SyntaxService
from services.merge_service import MergeService
from services.semantic_client import SemanticClient
from services.conversion_service import convert as convert_temperature


class CompilerController:
    def __init__(self):
        self.automata = Automata()
        self.llm = LLMFactory.create()
        self.syntax_service = SyntaxService()
        self.merge_service = MergeService()
        self.semantic_client = SemanticClient()

    def analyze(self, source: str) -> Dict[str, Any]:
        source = source.strip()

        if not source:
            raise ValueError("La oración no puede estar vacía.")

        return self._compile(source)

    def _compile(self, source: str) -> Dict[str, Any]:
        total_start = time.perf_counter()

        def timed_automata():
            start = time.perf_counter()
            tokens = self.automata.analyze(source)
            ms = round((time.perf_counter() - start) * 1000, 3)
            return tokens, ms

        def timed_llm():
            start = time.perf_counter()
            response = self.llm.normalize(source)
            ms = round((time.perf_counter() - start) * 1000, 3)
            return response, ms

        with ThreadPoolExecutor(max_workers=2) as executor:
            fut_afd = executor.submit(timed_automata)
            fut_llm = executor.submit(timed_llm)
            wait([fut_afd, fut_llm])

            automata_tokens, automata_ms = fut_afd.result()
            llm_response, llm_ms = fut_llm.result()

        total_ms = round((time.perf_counter() - total_start) * 1000, 3)

        metrics = {
            "automata_ms": automata_ms,
            "llm_ms": llm_ms,
            "total_ms": total_ms,
        }

        model = self.llm.model_info

        llm_tokens = llm_response.get("tokens", [])
        merged_tokens = self.merge_service.merge(automata_tokens, llm_tokens)

        syntax_result = self.syntax_service.validate(merged_tokens)

        if syntax_result.get("valid"):
            semantic_result = self.semantic_client.validate(syntax_result.get("tree"))
            if semantic_result.get("valid"):
                details = semantic_result.get("details", {})
                conversion = None
                if details:
                    try:
                        conversion = convert_temperature(
                            details["numero"],
                            details["unidad_origen_token"],
                            details["unidad_destino_token"],
                        )
                    except Exception as e:
                        conversion = {"error": str(e)}

                return {
                    "source": source,
                    "automata": automata_tokens,
                    "llm": llm_tokens,
                    "merged": merged_tokens,
                    "valid": True,
                    "status": "correct",
                    "message": semantic_result.get("message", "Instrucción válida."),
                    "missing": [],
                    "lexical": {"automata": automata_tokens, "llm": llm_tokens, "merged": merged_tokens},
                    "syntax": syntax_result,
                    "semantic": semantic_result,
                    "conversion": conversion,
                    "metrics": metrics,
                    "model": model,
                }

            return {
                "source": source,
                "automata": automata_tokens,
                "llm": llm_tokens,
                "merged": merged_tokens,
                "valid": False,
                "status": semantic_result.get("status", "invalid"),
                "message": semantic_result.get("message", "La instrucción no es semánticamente válida."),
                "missing": semantic_result.get("missing", []),
                "lexical": {"automata": automata_tokens, "llm": llm_tokens, "merged": merged_tokens},
                "syntax": syntax_result,
                "semantic": semantic_result,
                "metrics": metrics,
                "model": model,
            }

        return {
            "source": source,
            "automata": automata_tokens,
            "llm": llm_tokens,
            "merged": merged_tokens,
            "valid": False,
            "status": "incomplete",
            "message": syntax_result.get("message", "No se pudo validar la instrucción."),
            "missing": [],
            "lexical": {"automata": automata_tokens, "llm": llm_tokens, "merged": merged_tokens},
            "syntax": syntax_result,
            "semantic": {"valid": False, "status": "invalid", "message": "No se realizó análisis semántico."},
            "metrics": metrics,
            "model": model,
        }
