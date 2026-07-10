package semantic.exception;

/** Excepción base para errores semánticos. Almacena el mensaje y la regla violada. */
public class SemanticException extends Exception {
    private String rule;

    public SemanticException(String message, String rule) {
        super(message);
        this.rule = rule;
    }

    public String getRule() { return rule; }
}
