# Analizador Léxico para Conversión de Unidades de Temperatura

Sistema que analiza instrucciones en lenguaje natural del tipo `convertir 100 celsius a fahrenheit` combinando un **AFD** (expresiones regulares) con un **LLM** (Groq) para el análisis léxico, un **parser descendente recursivo** para la sintaxis, y un **servicio Java** independiente para la validación semántica.

---

## Arquitectura (MVC)

```
app.py  (punto de entrada Flask)
  │
  ├── views/lexical_routes.py       ← CAPA DE PRESENTACIÓN (HTTP)
  │     Llama al controlador y decide el código HTTP de respuesta
  │
  ├── controllers/compiler_controller.py  ← CAPA DE ORQUESTACIÓN
  │     Orquesta: AFD → LLM → Merge → Sintaxis → Semántica (Java)
  │
  ├── services/syntax_service.py     ← CAPA DE SERVICIOS
  │     Valida la sintaxis usando el parser
  │
  ├── models/                        ← CAPA DE MODELOS (datos y lógica de negocio)
  │     ├── token.py          (entidad Token)
  │     ├── ast.py            (nodo del AST)
  │     ├── errors.py         (excepciones del parser)
  │     ├── automata.py       (AFD: reconoce NUMERO y PREPOSICION_A)
  │     ├── llm_model.py      (Groq: reconoce CONVERTIR y UNIDADES)
  │     └── parser.py         (analizador sintáctico descendente recursivo)
  │
  └── java_semantic/                 ← MICROSERVICIO JAVA
        Servicio HTTP (puerto 8090) que valida la semántica.
```

---

## Pipeline de Análisis (3 fases)

```
Entrada: "convertir 100 celsius a fahrenheit"
                    │
    ┌───────────────┴───────────────┐
    ▼                               ▼
FASE 1A: AFD                    FASE 1B: LLM (Groq)
(models/automata.py)             (models/llm_model.py)
                                │
  Reconoce:                     Reconoce:
  • NUMERO  → "100"             • CONVERTIR      → "convertir"
  • PREPOSICION_A → "a"         • UNIDAD_ORIGEN_C → "celsius"
                                • UNIDAD_DESTINO_F → "fahrenheit"
    │                               │
    └───────────────┬───────────────┘
                    ▼
           FUSIÓN (merge por posición)
                    │
                    ▼
           FASE 2: SINTAXIS
           (services/syntax_service.py → models/parser.py)
           ¿Los tokens están en el orden correcto?
           Si sí → genera AST (Árbol de Sintaxis Abstracta)
           Si no  → error "incomplete" o "invalid"
                    │
                    ▼
           FASE 3: SEMÁNTICA (Java)
           (java_semantic → puerto 8090)
           ¿La instrucción tiene sentido?
           • Regla 1: ¿unidad origen ≠ unidad destino?
           • Regla 2: ¿número > 0?
           • Regla 3: ¿Kelvin no negativo?
                    │
                    ▼
           RESPUESTA JSON
```

---

## ¿Dónde se definen los TOKENS?

Los tokens se definen en **dos lugares** porque cada fuente reconoce unos distintos:

### 1. AFD — `models/automata.py` (línea 6-10)

```python
TOKEN_PATTERNS = [
    ("NUMERO",         r"\d+(\.\d+)?"),   # números enteros y decimales
    ("PREPOSICION_A",  r"\ba\b"),          # palabra "a"
    ("SPACE",          r"\s+"),            # espacios (se ignoran)
    ("UNKNOWN",        r"[^\s]+"),         # todo lo demás (se filtra)
]
```

- Solo reconoce `NUMERO` y `PREPOSICION_A` mediante **expresiones regulares**.
- El resto se marca `UNKNOWN` y se **filtra** (esos los reconocerá el LLM).

### 2. LLM (Groq) — `models/llm_model.py:_build_prompt()` (línea 91)

El prompt contiene una **tabla de sinónimos** que el LLM usa para reconocer:

| Token | Sinónimos que reconoce |
|-------|----------------------|
| `CONVERTIR` | convertir |
| `UNIDAD_ORIGEN_C` | celsius, centígrados, grado centígrado, grados centígrados, °C |
| `UNIDAD_ORIGEN_F` | fahrenheit, grados fahrenheit, °F |
| `UNIDAD_ORIGEN_K` | kelvin, grados kelvin, K |
| `UNIDAD_DESTINO_C` | celsius, centígrados, grado centígrado, grados centígrados, °C |
| `UNIDAD_DESTINO_F` | fahrenheit, grados fahrenheit, °F |
| `UNIDAD_DESTINO_K` | kelvin, grados kelvin, K |

- El LLM **nunca** inventa palabras: solo devuelve lexemas que existen literalmente en el texto.
- Reconoce mayúsculas/minúsculas y variaciones (acentos, símbolos °C/°F/K).

### 3. Gramática — `models/parser.py` (línea 11-17)

El parser **valida el orden** de los tokens:

```
Programa       ::= Instruccion
Instruccion    ::= CONVERTIR NUMERO UnidadOrigen PREPOSICION_A UnidadDestino
UnidadOrigen   ::= UNIDAD_ORIGEN_C | UNIDAD_ORIGEN_F | UNIDAD_ORIGEN_K
UnidadDestino  ::= UNIDAD_DESTINO_C | UNIDAD_DESTINO_F | UNIDAD_DESTINO_K
```

**Ejemplo válido:** `CONVERTIR NUMERO UNIDAD_ORIGEN_C PREPOSICION_A UNIDAD_DESTINO_F`
**Ejemplo inválido:** `NUMERO CONVERTIR ...` (CONVERTIR debe ir primero)

### Resumen visual de quién reconoce qué

| Token | Reconocido por | Método |
|-------|---------------|--------|
| `NUMERO` (ej: 100) | AFD | Regex `\d+(\.\d+)?` |
| `PREPOSICION_A` (a) | AFD | Regex `\ba\b` |
| `CONVERTIR` | LLM (Groq) | Tabla de sinónimos en prompt |
| `UNIDAD_ORIGEN_C/F/K` | LLM (Groq) | Tabla de sinónimos en prompt |
| `UNIDAD_DESTINO_C/F/K` | LLM (Groq) | Tabla de sinónimos en prompt |

---

## Estructura del Proyecto

```
analizador_lexico/
│
├── app.py                          # Punto de entrada Flask
├── .env                            # Variables de entorno (GROQ_API_KEY, etc.)
├── requirements.txt                # Dependencias Python
│
├── models/                         # Modelos: datos + lógica de negocio
│   ├── __init__.py
│   ├── token.py                    # Entidad Token (tipo + lexema)
│   ├── ast.py                      # Nodo del Árbol de Sintaxis Abstracta
│   ├── errors.py                   # Excepciones del parser
│   ├── automata.py                 # AFD: reconoce NUMERO y PREPOSICION_A
│   ├── llm_model.py                # Cliente LLM (Groq): reconoce CONVERTIR y UNIDADES
│   └── parser.py                   # Parser descendente recursivo
│
├── services/                       # Servicios de validación
│   ├── __init__.py
│   └── syntax_service.py           # Valida sintaxis usando el parser
│
├── controllers/                    # Orquestación del pipeline
│   ├── __init__.py
│   └── compiler_controller.py     # Coordina AFD → LLM → Merge → Sintaxis → Java
│
├── views/                          # Presentación HTTP
│   ├── __init__.py
│   └── lexical_routes.py          # Endpoint POST /api/analyze
│
├── java_semantic/                  # Microservicio de validación semántica (Java)
│   ├── build.ps1
│   ├── run.ps1
│   ├── lib/gson.jar
│   └── src/semantic/
│       ├── SemanticServer.java     # Servidor HTTP (puerto 8090)
│       ├── service/SemanticValidator.java  # Reglas semánticas
│       ├── model/AstNode.java
│       └── exception/             # SameUnitException, NegativeValueException, etc.
│
├── tests/                          # Pruebas unitarias
│   └── test_syntax_validator.py
│
└── frontend/                       # Frontend Angular (opcional)
```

---

## Cómo Ejecutar

### 1. Backend Python (Flask)

```powershell
# Entorno virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# Dependencias
pip install -r requirements.txt

# Configurar .env
# GROQ_API_KEY=gsk_tu_key_aqui
# GROQ_MODEL=llama-3.3-70b-versatile

# Ejecutar
python app.py
```

Servidor en `http://localhost:5000`.

### 2. Servicio Java (Semántica)

```powershell
cd java_semantic
.\run.ps1
```

Servidor en `http://localhost:8090`.

> Si Java no está corriendo, la API responde con `503` y un mensaje claro.

### 3. Frontend Angular (opcional)

```powershell
cd frontend
npm install
npm start
```

`http://localhost:4200`

---

## Códigos HTTP de Respuesta

| Código | Significado |
|--------|-------------|
| **200** | Análisis completado (válido o inválido) |
| **400** | El body no es JSON válido |
| **401** | Falta el campo `source` o está vacío |
| **502** | Error de comunicación con el servicio Java |
| **503** | Servicio Java no disponible |

---

## Cómo Probar

### Con Postman

```
POST http://localhost:5000/api/analyze
Content-Type: application/json

{
    "source": "convertir 100 celsius a fahrenheit"
}
```

### Con curl

```bash
curl -X POST http://localhost:5000/api/analyze ^
  -H "Content-Type: application/json" ^
  -d "{\"source\": \"convertir 100 celsius a fahrenheit\"}"
```

### Respuesta (200)

```json
{
  "valid": true,
  "status": "correct",
  "message": "Instrucción semánticamente correcta.",
  "lexical": {
    "automata": [
      {"token": "NUMERO", "lexeme": "100", "source": "AFD"},
      {"token": "PREPOSICION_A", "lexeme": "a", "source": "AFD"}
    ],
    "llm": [
      {"token": "CONVERTIR", "lexeme": "convertir", "source": "LLM"},
      {"token": "UNIDAD_ORIGEN_C", "lexeme": "celsius", "source": "LLM"},
      {"token": "UNIDAD_DESTINO_F", "lexeme": "fahrenheit", "source": "LLM"}
    ],
    "merged": [
      {"token": "CONVERTIR", "lexeme": "convertir", "source": "LLM", "position": 0},
      {"token": "NUMERO", "lexeme": "100", "source": "AFD", "position": 10},
      {"token": "UNIDAD_ORIGEN_C", "lexeme": "celsius", "source": "LLM", "position": 14},
      {"token": "PREPOSICION_A", "lexeme": "a", "source": "AFD", "position": 22},
      {"token": "UNIDAD_DESTINO_F", "lexeme": "fahrenheit", "source": "LLM", "position": 24}
    ]
  },
  "syntax": {
    "valid": true,
    "message": "Instrucción sintácticamente correcta."
  },
  "semantic": {
    "valid": true,
    "message": "Instrucción semánticamente correcta.",
    "details": {
      "numero": 100.0,
      "unidad_origen": "CELSIUS",
      "unidad_destino": "FAHRENHEIT"
    }
  },
  "metrics": {
    "automata_ms": 0.5,
    "llm_ms": 1200.0,
    "total_ms": 1202.0
  }
}
```

### Ejemplos para probar

| Entrada | Esperado |
|---------|----------|
| `convertir 100 celsius a fahrenheit` | ✅ Válido |
| `convertir 0 celsius a kelvin` | ❌ Número debe ser > 0 |
| `convertir 100 celsius a celsius` | ❌ Misma unidad |
| `convertir -10 kelvin a celsius` | ❌ Kelvin negativo |
| `convertir a fahrenheit` | ❌ Falta NUMERO |
| `hola mundo` | ❌ Falta CONVERTIR |

---

## Variables de Entorno (`.env`)

| Variable | Descripción | Valor ejemplo |
|----------|-------------|---------------|
| `GROQ_API_KEY` | API Key de Groq | `gsk_...` |
| `GROQ_MODEL` | Modelo Groq | `llama-3.3-70b-versatile` |
| `FLASK_PORT` | Puerto Flask | `5000` |
| `FLASK_DEBUG` | Modo debug | `True` |
| `JAVA_SEMANTIC_URL` | URL del servicio Java | `http://localhost:8090/api/validate-semantic` |
