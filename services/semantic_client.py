import os
from typing import Dict, Any

import requests
from dotenv import load_dotenv

load_dotenv()

JAVA_SEMANTIC_URL = os.getenv("JAVA_SEMANTIC_URL")


class SemanticClient:
    def validate(self, ast_dict: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(
                JAVA_SEMANTIC_URL,
                json={"tree": ast_dict},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError:
            return {
                "valid": False,
                "status": "unavailable",
                "message": "Servicio semántico (Java) no disponible.",
            }
        except requests.RequestException as e:
            return {
                "valid": False,
                "status": "error",
                "message": f"Error en el servicio semántico: {e}",
            }
