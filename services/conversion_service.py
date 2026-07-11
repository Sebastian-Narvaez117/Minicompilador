from typing import Dict, Any, Tuple

UNIT_MAP = {
    "UNIDAD_ORIGEN_C": "CELSIUS",
    "UNIDAD_ORIGEN_F": "FAHRENHEIT",
    "UNIDAD_ORIGEN_K": "KELVIN",
    "UNIDAD_DESTINO_C": "CELSIUS",
    "UNIDAD_DESTINO_F": "FAHRENHEIT",
    "UNIDAD_DESTINO_K": "KELVIN",
}

"""
    Conversor de unidades de temperatura.
    
    Fórmulas:
    - Celsius → Fahrenheit: °F = (°C × 1.8) + 32
    - Celsius → Kelvin:     K = °C + 273.15
    - Fahrenheit → Celsius: °C = (°F - 32) / 1.8
    - Fahrenheit → Kelvin:  K = (°F - 32) / 1.8 + 273.15
    - Kelvin → Celsius:     °C = K - 273.15
    - Kelvin → Fahrenheit:  °F = (K - 273.15) × 1.8 + 32
    """

def convert(value: float, origen: str, destino: str) -> Dict[str, Any]:
    origen_name = UNIT_MAP.get(origen, origen)
    destino_name = UNIT_MAP.get(destino, destino)

    result_value, formula = _apply_formula(value, origen_name, destino_name)

    return {
        "value": round(result_value, 4),
        "from": {"unit": origen_name, "value": value},
        "to": {"unit": destino_name, "value": round(result_value, 4)},
        "formula": formula,
    }


def _apply_formula(value: float, origen: str, destino: str) -> Tuple[float, str]:
    pair = (origen, destino)

    formulas = {
        ("CELSIUS", "FAHRENHEIT"): (
            value * 1.8 + 32,
            f"{value} °C × 1.8 + 32 = {round(value * 1.8 + 32, 4)} °F",
        ),
        ("CELSIUS", "KELVIN"): (
            value + 273.15,
            f"{value} °C + 273.15 = {round(value + 273.15, 4)} K",
        ),
        ("FAHRENHEIT", "CELSIUS"): (
            (value - 32) / 1.8,
            f"({value} °F - 32) ÷ 1.8 = {round((value - 32) / 1.8, 4)} °C",
        ),
        ("FAHRENHEIT", "KELVIN"): (
            (value - 32) / 1.8 + 273.15,
            f"({value} °F - 32) ÷ 1.8 + 273.15 = {round((value - 32) / 1.8 + 273.15, 4)} K",
        ),
        ("KELVIN", "CELSIUS"): (
            value - 273.15,
            f"{value} K - 273.15 = {round(value - 273.15, 4)} °C",
        ),
        ("KELVIN", "FAHRENHEIT"): (
            (value - 273.15) * 1.8 + 32,
            f"({value} K - 273.15) × 1.8 + 32 = {round((value - 273.15) * 1.8 + 32, 4)} °F",
        ),
    }

    if pair not in formulas:
        raise ValueError(f"Conversión no soportada: {origen} → {destino}")

    result, formula = formulas[pair]
    return result, formula
