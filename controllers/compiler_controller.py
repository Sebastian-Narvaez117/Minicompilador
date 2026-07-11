import os
import threading
import time
from typing import Dict, Any, List

import requests

from models.automata import Automata
from models.llm_model import LLMModel
from services.syntax_service import SyntaxService
from services.conversion_service import convert as convert_temperature


JAVA_SEMANTIC_URL = os.getenv("JAVA_SEMANTIC_URL")


class CompilerController:
    """Orquestador del pipeline de análisis: AFD → LLM → Merge → Sintaxis → Semántica (Java)."""

    def __init__(self):
        self.automata = Automata()
        self.llm = LLMModel()

    def analyze(self, source: str) -> Dict[str, Any]:
        """Punto de entrada: recibe el texto, lo analiza completo y retorna el resultado."""
        source = source.strip()

        if not source:
            raise ValueError("La oración no puede estar vacía.")

        return self._compile(source)

    def _compile(self, source: str) -> Dict[str, Any]:
        result_automata: Dict[str, Any] = {}
        result_llm: Dict[str, Any] = {}
        metrics: Dict[str, Any] = {}

        def run_automata():
            print("[Thread-AFD] Ejecutando AFD...")
            start = time.perf_counter()
            result_automata["tokens"] = self.automata.analyze(source)
            metrics["automata_ms"] = round((time.perf_counter() - start) * 1000, 3)
            print("[Thread-AFD] Finalizado.")

        def run_llm():
            print("[Thread-LLM] Ejecutando LLM...")
            start = time.perf_counter()
            response = self.llm.normalize(source)
            result_llm["tokens"] = response.get("tokens", [])
            metrics["llm_ms"] = round((time.perf_counter() - start) * 1000, 3)
            print("[Thread-LLM] Finalizado.")

        total_start = time.perf_counter()

        thread_afd = threading.Thread(target=run_automata, name="Thread-AFD")
        thread_afd.start()
        thread_afd.join()

        thread_llm = threading.Thread(target=run_llm, name="Thread-LLM")
        thread_llm.start()
        thread_llm.join()

        metrics["total_ms"] = round((time.perf_counter() - total_start) * 1000, 3)

        automata_tokens = result_automata.get("tokens", [])
        llm_tokens = result_llm.get("tokens", [])
        merged_tokens = self._merge_tokens(automata_tokens, llm_tokens)

        syntax_result = self._run_syntax_analysis(merged_tokens)

        if syntax_result.get("valid"):
            semantic_result = self._call_java_semantic_service(syntax_result.get("tree"))
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
        }

    def _merge_tokens(self, automata_tokens: List[Dict[str, Any]], llm_tokens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combina tokens del AFD y del LLM ordenándolos por posición en el texto original."""
        cleaned_automata = [token for token in automata_tokens if token.get("token") != "UNKNOWN"]
        merged = cleaned_automata + [token for token in llm_tokens if token.get("position", -1) != -1]
        merged.sort(key=lambda item: item.get("position", 0))
        return merged

    def _run_syntax_analysis(self, tokens: List[Dict[str, Any]]) -> Dict[str, Any]:
        service = SyntaxService()
        return service.validate(tokens)

    def _call_java_semantic_service(self, ast_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(
                JAVA_SEMANTIC_URL,
                json={"tree": ast_dict},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError:
            return {
                "valid": False,
                "status": "unavailable",
                "message": "Servicio semántico (Java) no disponible."
            }
        except requests.RequestException as e:
            return {
                "valid": False,
                "status": "error",
                "message": f"Error en el servicio semántico: {e}"
            }
