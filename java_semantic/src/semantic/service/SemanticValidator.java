package semantic.service;

import semantic.model.AstNode;
import semantic.exception.*;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * Validador semántico (reglas de negocio).
 *
 * Reglas:
 *   Regla 1: No convertir una unidad a sí misma (ej: celsius -> celsius).
 *   Regla 2: Kelvin no admite valores negativos.
 */
public class SemanticValidator {

    /** Mapeo de tokens de unidad a nombre canónico. */
    private static final Map<String, String> UNIT_MAP = new HashMap<>();

    static {
        UNIT_MAP.put("UNIDAD_ORIGEN_C", "CELSIUS");
        UNIT_MAP.put("UNIDAD_ORIGEN_F", "FAHRENHEIT");
        UNIT_MAP.put("UNIDAD_ORIGEN_K", "KELVIN");
        UNIT_MAP.put("UNIDAD_DESTINO_C", "CELSIUS");
        UNIT_MAP.put("UNIDAD_DESTINO_F", "FAHRENHEIT");
        UNIT_MAP.put("UNIDAD_DESTINO_K", "KELVIN");
    }

    /**
     * Valida el AST completo aplicando todas las reglas semánticas.
     * @param ast Árbol generado por el parser (Python).
     * @return Mapa con valid, message, details/rule.
     */
    public Map<String, Object> validate(AstNode ast) {
        try {
            Map<String, Object> data = extractData(ast);

            validateSameUnit(data);
            validateKelvinNotNegative(data);

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("valid", true);
            result.put("message", "Instrucción semánticamente correcta.");
            result.put("details", data);
            return result;

        } catch (SemanticException e) {
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("valid", false);
            result.put("message", e.getMessage());
            result.put("rule", e.getRule());
            return result;
        }
    }

    /** Extrae número, unidad_origen y unidad_destino del AST. */
    private Map<String, Object> extractData(AstNode ast) throws SemanticException {
        AstNode programa = ast;
        if (programa.getChildren().isEmpty()) {
            throw new SemanticException("AST vacío.", null);
        }
        AstNode instruccion = programa.getChildren().get(0);
        if (instruccion.getChildren().size() < 5) {
            throw new SemanticException("AST incompleto: faltan nodos en Instruccion.", null);
        }

        AstNode numeroNode = instruccion.getChildren().get(1);
        AstNode origenNode = instruccion.getChildren().get(2);
        AstNode destinoNode = instruccion.getChildren().get(4);

        double numero;
        try {
            numero = Double.parseDouble(numeroNode.getValue());
        } catch (NumberFormatException e) {
            throw new SemanticException("El valor numérico no es válido: " + numeroNode.getValue(), null);
        }

        String origenToken = origenNode.getValue();
        String destinoToken = destinoNode.getValue();

        String unidadOrigen = UNIT_MAP.getOrDefault(origenToken, origenToken);
        String unidadDestino = UNIT_MAP.getOrDefault(destinoToken, destinoToken);

        Map<String, Object> data = new LinkedHashMap<>();
        data.put("numero", numero);
        data.put("unidad_origen_token", origenToken);
        data.put("unidad_destino_token", destinoToken);
        data.put("unidad_origen", unidadOrigen);
        data.put("unidad_destino", unidadDestino);

        return data;
    }

    /** Regla 1: No convertir una unidad a sí misma. */
    private void validateSameUnit(Map<String, Object> data) throws SameUnitException {
        String origen = (String) data.get("unidad_origen");
        String destino = (String) data.get("unidad_destino");
        if (origen != null && origen.equals(destino)) {
            throw new SameUnitException();
        }
    }

    /** Regla 2: Kelvin no admite valores negativos (cero absoluto). */
    private void validateKelvinNotNegative(Map<String, Object> data) throws NegativeKelvinException {
        String unidadOrigen = (String) data.get("unidad_origen");
        double numero = (double) data.get("numero");
        if ("KELVIN".equals(unidadOrigen) && numero < 0) {
            throw new NegativeKelvinException();
        }
    }
}
