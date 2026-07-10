from dataclasses import dataclass


@dataclass
class Token:
    token: str  # Tipo del token (CONVERTIR, NUMERO, UNIDAD_ORIGEN_C, etc.)
    lexeme: str  # Texto original extraído (convertir, 100, celsius, etc.)
