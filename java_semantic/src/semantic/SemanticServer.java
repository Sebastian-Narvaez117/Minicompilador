package semantic;

import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;

import semantic.model.AstNode;
import semantic.service.SemanticValidator;

import java.io.*;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/**
 * Servidor HTTP para validación semántica.
 * Recibe el AST en JSON desde Python y aplica reglas semánticas.
 * Endpoint: POST /api/validate-semantic
 * Puerto: 8090
 */
public class SemanticServer {

    private static final int PORT = 8090;
    private static final Gson gson = new Gson();
    private static final SemanticValidator validator = new SemanticValidator();

    public static void main(String[] args) throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(PORT), 0);

        server.createContext("/api/validate-semantic", SemanticServer::handleValidate);
        server.setExecutor(null);

        System.out.println("[Java-Semantic] Servidor iniciado en puerto " + PORT);
        server.start();
    }

    /** Maneja la petición POST: recibe {"tree": {...}}, valida y responde. */
    private static void handleValidate(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendJson(exchange, 405, "{\"error\":\"Método no permitido\"}");
            return;
        }

        try {
            String body = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            JsonObject json = JsonParser.parseString(body).getAsJsonObject();

            if (!json.has("tree")) {
                sendJson(exchange, 400, "{\"error\":\"Campo 'tree' requerido\"}");
                return;
            }

            AstNode ast = gson.fromJson(json.get("tree"), AstNode.class);
            Map<String, Object> result = validator.validate(ast);

            String response = gson.toJson(result);
            sendJson(exchange, 200, response);

        } catch (Exception e) {
            e.printStackTrace();
            String error = gson.toJson(Map.of(
                "valid", false,
                "message", "Error interno: " + e.getMessage()
            ));
            sendJson(exchange, 500, error);
        }
    }

    /** Envía una respuesta JSON con el código HTTP indicado. */
    private static void sendJson(HttpExchange exchange, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", "application/json; charset=UTF-8");
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }
}
