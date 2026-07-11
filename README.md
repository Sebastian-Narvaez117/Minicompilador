# Minicompilador — Conversión de Unidades de Temperatura

Sistema que analiza instrucciones en lenguaje natural como `convertir 100 celsius a fahrenheit` y devuelve el resultado de la conversión. Combina un **AFD** (regex) con un **LLM** (Groq u Ollama) para el análisis léxico, un **parser descendente recursivo** para la sintaxis, un **servicio Java** para la semántica, y una **fase de conversión** que aplica las fórmulas.

---

## Arquitectura (MVC)

```
app.py  (Flask)
  │
  ├── views/lexical_routes.py          ← CAPA HTTP
  │     POST /api/analyze
  │
  ├── controllers/compiler_controller.py  ← ORQUESTACIÓN
  │     AFD → LLM → Merge → Sintaxis → Semántica → Conversión
  │
  ├── services/                        ← CAPA DE SERVICIOS
  │   ├── llm_provider.py       (ABC para proveedores LLM)
  │   ├── groq_strategy.py      (implementación Groq)
  │   ├── ollama_strategy.py    (implementación Ollama)
  │   ├── llm_factory.py        (selecciona estrategia según .env)
  │   ├── merge_service.py      (fusión de tokens AFD + LLM)
  │   ├── semantic_client.py    (comunicación con Java)
  │   ├── syntax_service.py     (validación sintáctica)
  │   └── conversion_service.py (fórmulas de temperatura)
  │
  ├── models/                         ← CAPA DE MODELOS
  │   ├── token.py             (Token)
  │   ├── ast.py               (ASTNode)
  │   ├── errors.py            (ParserError)
  │   ├── automata.py          (AFD: NUMERO, PREPOSICION_A)
  │   └── parser.py            (parser descendente recursivo)
  │
  └── java_semantic/                  ← MICROSERVICIO JAVA (puerto 8090)
        Valida reglas semánticas.
```

---

## Pipeline (4 fases)

```
"convertir -5 celsius a kelvin"
          │
  ┌───────┴───────┐
  ▼               ▼
AFD             LLM (Groq u Ollama)
(regex)         (strategy pattern)
  │               │
  │ NUMERO "-5"   │ CONVERTIR
  │ PREPOSICION_A │ UNIDAD_ORIGEN_C
  │               │ UNIDAD_DESTINO_K
  └───────┬───────┘
          ▼
     MERGE (MergeService)
     fusiona y ordena por posición
          │
          ▼
     FASE 2: SINTAXIS (parser)
     ¿orden correcto?
     Si → genera AST
     No → error "incomplete"/"invalid"
          │
          ▼
     FASE 3: SEMÁNTICA (Java)
     • Regla 1: ¿origen ≠ destino?
     • Regla 2: ¿Kelvin ≥ 0?
          │
          ▼
     FASE 4: CONVERSIÓN (conversion_service)
     Aplica fórmula según par (origen, destino)
          │
          ▼
     RESPUESTA JSON
```

El AFD y el LLM se ejecutan **en paralelo** mediante `ThreadPoolExecutor(max_workers=2)`, de modo que el tiempo total se aproxima al máximo de ambas tareas y no a la suma.

---

## Patrón Strategy — Proveedores LLM

El sistema usa el patrón **Strategy** para seleccionar el proveedor de LLM sin modificar el resto del código.

### Clases

| Clase | Rol |
|---|---|
| `LLMProvider` (ABC) | Interfaz abstracta con método `normalize(source)` |
| `GroqStrategy` | Implementación para la API de Groq |
| `OllamaStrategy` | Implementación para Ollama (local) |
| `LLMFactory` | Factory que crea la estrategia según `LLM_PROVIDER` |

### Cómo cambiar de proveedor

Editar únicamente la variable `LLM_PROVIDER` en `.env`:

```env
# Para usar Groq (nube):
LLM_PROVIDER=groq

# Para usar Ollama (local):
LLM_PROVIDER=ollama
```

**No es necesario modificar ninguna otra clase.** El `CompilerController` obtiene el proveedor mediante:

```python
self.llm = LLMFactory.create()  # ← polimórfico
```

### Variables de entorno por proveedor

**Groq:**
```
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
```

**Ollama:**
```
MODEL_LOCAL_LLAMA=llama3.2:3b
HOST_MODEL_LOCAL_LLAMA=http://localhost:11434/api/generate
```

---

## Tokens

### AFD — `models/automata.py`

| Token | Regex | Ejemplo |
|-------|-------|---------|
| `NUMERO` | `-?\d+(\.\d+)?` | `100`, `-5`, `32.5` |
| `PREPOSICION_A` | `\ba\b` | `a` |
| `SPACE` | `\s+` | (se ignora) |
| `UNKNOWN` | `[^\s]+` | (se filtra, lo toma el LLM) |

### LLM — definido en el prompt de cada estrategia

| Token | Sinónimos |
|-------|-----------|
| `CONVERTIR` | convertir |
| `UNIDAD_ORIGEN_C` / `UNIDAD_DESTINO_C` | celsius, centígrados, grado centígrado, grados centígrados, °C, °c |
| `UNIDAD_ORIGEN_F` / `UNIDAD_DESTINO_F` | fahrenheit, grados fahrenheit, °F, °f |
| `UNIDAD_ORIGEN_K` / `UNIDAD_DESTINO_K` | kelvin, grados kelvin, K |

### Gramática — `models/parser.py`

```
Programa       ::= Instruccion
Instruccion    ::= CONVERTIR NUMERO UnidadOrigen PREPOSICION_A UnidadDestino
UnidadOrigen   ::= UNIDAD_ORIGEN_C | UNIDAD_ORIGEN_F | UNIDAD_ORIGEN_K
UnidadDestino  ::= UNIDAD_DESTINO_C | UNIDAD_DESTINO_F | UNIDAD_DESTINO_K
```

---

## Reglas Semánticas (Java)

1. **Misma unidad**: No convertir una unidad a sí misma.
2. **Kelvin no negativo**: Si el origen es Kelvin, el valor debe ser ≥ 0.

Celsius y Fahrenheit **sí** aceptan valores negativos.

---

## Fórmulas de Conversión

| Origen → Destino | Fórmula |
|-----------------|---------|
| Celsius → Fahrenheit | °F = (°C × 1.8) + 32 |
| Celsius → Kelvin | K = °C + 273.15 |
| Fahrenheit → Celsius | °C = (°F − 32) ÷ 1.8 |
| Fahrenheit → Kelvin | K = (°F − 32) ÷ 1.8 + 273.15 |
| Kelvin → Celsius | °C = K − 273.15 |
| Kelvin → Fahrenheit | °F = (K − 273.15) × 1.8 + 32 |

---

## Estructura del Proyecto

```
Minicompilador/
├── app.py                          # Flask entry point
├── .env                            # Configuración (proveedor, APIs, etc.)
├── requirements.txt
│
├── models/                         # Datos del dominio
│   ├── token.py                    # Token  (token, lexeme)
│   ├── ast.py                      # ASTNode (name, value, children)
│   ├── errors.py                   # ParserError, UnexpectedTokenError, MissingTokenError
│   ├── automata.py                 # AFD con regex
│   └── parser.py                   # Parser descendente recursivo
│
├── services/                       # Lógica de negocio y algoritmos
│   ├── llm_provider.py             # ABC para proveedores LLM
│   ├── groq_strategy.py            # Estrategia Groq
│   ├── ollama_strategy.py          # Estrategia Ollama
│   ├── llm_factory.py              # Factory de proveedores LLM
│   ├── merge_service.py            # Fusión de tokens AFD + LLM
│   ├── semantic_client.py          # Cliente HTTP para servicio Java
│   ├── syntax_service.py           # Validación sintáctica
│   └── conversion_service.py       # Fórmulas de temperatura
│
├── controllers/
│   └── compiler_controller.py      # Orquesta el pipeline completo
│
├── views/
│   └── lexical_routes.py           # POST /api/analyze
│
├── java_semantic/
│   ├── lib/gson.jar
│   └── src/semantic/
│       ├── SemanticServer.java
│       ├── service/SemanticValidator.java
│       ├── model/AstNode.java
│       └── exception/
│           ├── SemanticException.java
│           ├── SameUnitException.java
│           └── NegativeKelvinException.java
│
├── tests/
│   └── test_syntax_validator.py
│
└── frontend/                       # Angular 20 (standalone)
    └── src/app/
        ├── models/
        ├── core/services/
        └── pages/analyzer/
```

---

## Cómo Ejecutar

### 1. Backend Python (Flask)

```bash
python -m venv venv
source venv/bin/activate              # Linux/Mac
pip install -r requirements.txt

# Configurar .env (ver sección Variables de Entorno)
python app.py
# → http://localhost:5000
```

### 2. Servicio Java (Semántica)

```bash
cd java_semantic
javac -cp "lib/gson.jar" -d out $(find src -name "*.java")
java -cp "out:lib/gson.jar" semantic.SemanticServer
# → http://localhost:8090
```

> Si Java no está corriendo, la API responde con `503`.

### 3. Frontend Angular

```bash
cd frontend
npm install
npm start
# → http://localhost:4200
```

---

## API

### `POST /api/analyze`

```json
{
  "source": "convertir 100 celsius a fahrenheit"
}
```

Respuesta (200):

```json
{
  "valid": true,
  "status": "correct",
  "message": "Instrucción semánticamente correcta.",
  "automata": [
    {"token": "NUMERO", "lexeme": "100", "position": 10, "source": "AFD"},
    {"token": "PREPOSICION_A", "lexeme": "a", "position": 22, "source": "AFD"}
  ],
  "llm": [
    {"token": "CONVERTIR", "lexeme": "convertir", "position": 0, "source": "LLM"},
    {"token": "UNIDAD_ORIGEN_C", "lexeme": "celsius", "position": 14, "source": "LLM"},
    {"token": "UNIDAD_DESTINO_F", "lexeme": "fahrenheit", "position": 24, "source": "LLM"}
  ],
  "merged": [
    {"token": "CONVERTIR", "lexeme": "convertir", "source": "LLM", "position": 0},
    {"token": "NUMERO", "lexeme": "100", "source": "AFD", "position": 10},
    {"token": "UNIDAD_ORIGEN_C", "lexeme": "celsius", "source": "LLM", "position": 14},
    {"token": "PREPOSICION_A", "lexeme": "a", "source": "AFD", "position": 22},
    {"token": "UNIDAD_DESTINO_F", "lexeme": "fahrenheit", "source": "LLM", "position": 24}
  ],
  "syntax": {"valid": true, "message": "Instrucción sintácticamente correcta."},
  "semantic": {
    "valid": true,
    "message": "Instrucción semánticamente correcta.",
    "details": {
      "numero": 100.0,
      "unidad_origen_token": "UNIDAD_ORIGEN_C",
      "unidad_destino_token": "UNIDAD_DESTINO_F",
      "unidad_origen": "CELSIUS",
      "unidad_destino": "FAHRENHEIT"
    }
  },
  "conversion": {
    "value": 212.0,
    "from": {"unit": "CELSIUS", "value": 100.0},
    "to": {"unit": "FAHRENHEIT", "value": 212.0},
    "formula": "100.0 °C × 1.8 + 32 = 212.0 °F"
  },
  "metrics": {"automata_ms": 0.3, "llm_ms": 850.0, "total_ms": 852.0}
}
```

### Códigos HTTP

| Código | Significado |
|--------|-------------|
| **200** | Análisis completado |
| **400** | Body no es JSON |
| **401** | `source` faltante o vacío |
| **502** | Error en servicio Java |
| **503** | Servicio Java no disponible |

---

## Casos de Prueba

| Entrada | Fase que falla | Mensaje |
|---------|---------------|---------|
| `convertir 100 celsius a fahrenheit` | — | ✅ Conversión exitosa |
| `convertir -5 celsius a fahrenheit` | — | ✅ Negativo permitido en °C/°F |
| `convertir 0 celsius a kelvin` | — | ✅ Cero permitido |
| `convertir -10 kelvin a celsius` | Semántica | ❌ Kelvin no admite valores negativos. |
| `convertir 100 celsius a celsius` | Semántica | ❌ La unidad origen y destino son iguales. |
| `convertir a fahrenheit` | Sintaxis | ❌ Falta el número a convertir. |
| `100 celsius a fahrenheit` | Sintaxis | ❌ Falta la palabra 'convertir'. |
| `convertir 100 celsius kelvin` | Sintaxis | ❌ Falta la preposición 'a'. |
| `hola mundo` | Sintaxis | ❌ Falta la palabra 'convertir'. |

---

## Variables de Entorno (`.env`)

| Variable | Obligatorio | Descripción | Ejemplo |
|----------|-------------|-------------|---------|
| `LLM_PROVIDER` | Sí | Proveedor LLM (`groq` o `ollama`) | `groq` |
| `GROQ_API_KEY` | Si `PROVIDER=groq` | API Key de Groq | `gsk_...` |
| `GROQ_MODEL` | Si `PROVIDER=groq` | Modelo Groq | `llama-3.3-70b-versatile` |
| `MODEL_LOCAL_LLAMA` | Si `PROVIDER=ollama` | Modelo local Ollama | `llama3.2:3b` |
| `HOST_MODEL_LOCAL_LLAMA` | Si `PROVIDER=ollama` | URL del servidor Ollama | `http://localhost:11434/api/generate` |
| `JAVA_SEMANTIC_URL` | Sí | URL del servicio Java | `http://localhost:8090/api/validate-semantic` |
| `FLASK_PORT` | No | Puerto Flask (default `5000`) | `5000` |
| `FLASK_DEBUG` | No | Modo debug (default `True`) | `True` |
