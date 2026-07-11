import json
import os
import re

import requests
from dotenv import load_dotenv

from services.llm_provider import LLMProvider

load_dotenv()


class GroqStrategy(LLMProvider):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "llama3-70b-8192")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY no está definida en .env")

    @property
    def model_info(self):
        return {"provider": "Groq", "model_name": self.model}

    def normalize(self, source: str):
        source_text = str(source)
        prompt = self._build_prompt(source_text)

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Eres un tokenizador léxico. Responde ÚNICAMENTE JSON válido, sin explicaciones."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0,
                    "max_tokens": 256,
                    "response_format": {"type": "json_object"}
                },
                timeout=120
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"].strip()
        except requests.RequestException as exc:
            print(f"[Groq] Groq no disponible: {exc}")
            if hasattr(exc, 'response') and exc.response is not None:
                print(f"[Groq] Respuesta: {exc.response.text}")
            return {"tokens": []}

        if text.startswith("```"):
            text = text.replace("```json", "")
            text = text.replace("```", "")
            text = text.strip()

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group()

        try:
            data = json.loads(text)
        except Exception:
            data = {"tokens": []}

        if "tokens" not in data:
            data["tokens"] = []

        valid_tokens = []
        search_start = 0
        for token in data["tokens"]:
            if "token" not in token or "lexeme" not in token:
                continue

            lexeme = str(token["lexeme"]).strip()
            position = source_text.lower().find(lexeme.lower(), search_start)

            if position == -1:
                position = source_text.lower().find(lexeme.lower())

            if position == -1:
                print(f"[Groq] Token descartado: {lexeme}")
                continue

            token["position"] = position
            token["length"] = len(lexeme)
            token["source"] = "LLM"
            search_start = position + len(lexeme)
            valid_tokens.append(token)

        data["tokens"] = valid_tokens
        return data

    def _build_prompt(self, source: str):
        return f"""
Eres un Tokenizador Léxico para un compilador de conversión de unidades.

Tu única función es reconocer tokens léxicos presentes literalmente en el texto.

==================================================

REGLAS IMPORTANTES

1. NO expliques nada.
2. NO respondas como un chatbot.
3. NO inventes palabras.
4. NO corrijas errores ortográficos.
5. NO completes frases.
6. NO agregues números.
7. NO agregues unidades.
8. NO cambies verbos.
9. Solo devuelve lexemas que EXISTAN literalmente en el texto.
10. Si una palabra no aparece exactamente en el texto, NO la devuelvas.
11. Las palabras pueden aparecer en mayúsculas, minúsculas o combinación de ambas.
12. El reconocimiento NO distingue entre mayúsculas y minúsculas.

==================================================

GRAMÁTICA

CONVERTIR NUMERO UNIDAD_ORIGEN PREPOSICION_A UNIDAD_DESTINO

==================================================

REGLAS DE CONTEXTO

• La unidad antes de la palabra "a" es una UNIDAD_ORIGEN.
• La unidad después de la palabra "a" es una UNIDAD_DESTINO.

==================================================

SINÓNIMOS

CONVERTIR
- convertir

CELSIUS
- celsius
- centígrados
- grado centígrado
- grados centígrados
- °C
- °c

FAHRENHEIT
- fahrenheit
- grados fahrenheit
- °F
- °f

KELVIN
- kelvin
- grados kelvin
- K

==================================================

EJEMPLO 1

Entrada: convertir 100 grados centígrados a fahrenheit

Salida: {{"tokens":[{{"token":"CONVERTIR","lexeme":"convertir"}},{{"token":"UNIDAD_ORIGEN_C","lexeme":"grados centígrados"}},{{"token":"UNIDAD_DESTINO_F","lexeme":"fahrenheit"}}]}}

==================================================

EJEMPLO 2

Entrada: convertir 32 fahrenheit a celsius

Salida: {{"tokens":[{{"token":"CONVERTIR","lexeme":"convertir"}},{{"token":"UNIDAD_ORIGEN_F","lexeme":"fahrenheit"}},{{"token":"UNIDAD_DESTINO_C","lexeme":"celsius"}}]}}

==================================================

EJEMPLO 3

Entrada: convertir 100 °C a kelvin

Salida: {{"tokens":[{{"token":"CONVERTIR","lexeme":"convertir"}},{{"token":"UNIDAD_ORIGEN_C","lexeme":"°C"}},{{"token":"UNIDAD_DESTINO_K","lexeme":"kelvin"}}]}}

==================================================

Texto a analizar: {source}

==================================================

RESPONDE ÚNICAMENTE JSON.

Formato EXACTO: {{"tokens":[{{"token":"","lexeme":""}}]}}

Si no reconoces ningún token responde: {{"tokens":[]}}
"""
