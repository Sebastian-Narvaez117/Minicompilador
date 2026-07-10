package semantic.model;

import java.util.ArrayList;
import java.util.List;

/**
 * Nodo del AST (Árbol de Sintaxis Abstracta).
 * Refleja la misma estructura que models/ast.py en Python.
 * Esperado: Programa -> Instruccion -> [CONVERTIR, NUMERO, UnidadOrigen, PREPOSICION_A, UnidadDestino]
 */
public class AstNode {
    private String type;
    private String name;
    private String value;
    private List<AstNode> children = new ArrayList<>();

    public AstNode() {}

    public AstNode(String name, String value) {
        this.name = name;
        this.type = name;
        this.value = value;
    }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getValue() { return value; }
    public void setValue(String value) { this.value = value; }
    public List<AstNode> getChildren() { return children; }
    public void setChildren(List<AstNode> children) { this.children = children; }
    public void addChild(AstNode child) { this.children.add(child); }
}
