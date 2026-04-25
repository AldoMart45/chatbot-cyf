from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.request
import urllib.error

PDF_CONTEXT = """
CUESTIONARIO: POSTULADOS BÁSICOS DE LA INFORMACIÓN FINANCIERA

=== VERDADERO / FALSO ===
1. Inversionistas, acreedores, clientes y proveedores son usuarios EXTERNOS (no internos). Los usuarios internos son empleados y directivos. FALSO
2. La información administrativa es para usuarios INTERNOS (directores, gerentes, jefes de dpto). La contabilidad financiera se dirige a externos. FALSO (Pág. 35)
3. La aseveración que dice que el postulado de sustancia económica trata sobre operaciones similares con tratamiento semejante es FALSO (eso describe la CONSISTENCIA, no la sustancia económica)
4. Las NIF establecen la manera en que se elabora y comunica la información financiera. VERDADERO (pág. 34)
5. La característica de oportunidad indica que información anticipada o posterior produciría decisiones erróneas. VERDADERO (pág. 52)
6. El postulado de dualidad económica establece que todo recurso tiene una fuente que lo generó. VERDADERO (pág. 55)

=== OPCIÓN MÚLTIPLE ===
- Postulado que reconoce ingresos aunque no hayan sido cobrados: DEVENGACIÓN CONTABLE
- Postulado que cuantifica transacciones en términos monetarios al valor de pago inicial: VALUACIÓN (pág. 54)
- Postulado que asume que el negocio continuará indefinidamente: NEGOCIO EN MARCHA (pág. 53)
- Postulado "todo recurso tiene una fuente / a todo cargo corresponde un abono": DUALIDAD ECONÓMICA (pág. 54)

=== LOS 8 POSTULADOS BÁSICOS (pág. 55) ===
1. SUSTANCIA ECONÓMICA: Registrar transacciones conforme a su realidad económica, no solo su forma jurídica.
2. ENTIDAD ECONÓMICA: Las operaciones de la empresa son independientes de sus accionistas y dueños.
3. NEGOCIO EN MARCHA: Se asume que la organización continuará indefinidamente (excepto en liquidación).
4. DEVENGACIÓN CONTABLE: El ingreso/gasto se registra cuando ocurre la operación, no cuando se cobra/paga. (pág. 68)
5. ASOCIACIÓN DE COSTOS Y GASTOS CON INGRESOS: Costos y gastos deben identificarse con los ingresos del mismo periodo.
6. VALUACIÓN: Se registra el valor económico más objetivo. En reconocimiento inicial: valor original de pago.
7. DUALIDAD ECONÓMICA: Todo recurso tiene una fuente que lo generó. En contabilidad: todo cargo tiene un abono.
8. CONSISTENCIA: Ante operaciones similares, debe aplicarse el mismo tratamiento contable a través del tiempo.

=== FUNCIÓN DE LOS POSTULADOS ===
Son la base sobre la que se efectúa el registro contable. Proporcionan sustento racional y teórico para el desarrollo de las NIF. (pág. 50)

=== POSTULADO DE ENTIDAD ECONÓMICA (detalle, pág. 53) ===
La contabilidad de la empresa es independiente de sus accionistas y dueños.
Los recursos personales de los socios (inmuebles, vehículos) deben mantenerse fuera de los registros.
Si un socio compra casa personal con dinero de la empresa se registra como préstamo, la casa NO es activo de la empresa.

=== POSTULADO DE ASOCIACIÓN COSTOS/GASTOS (detalle, pág. 69) ===
Los costos y gastos deben identificarse con los ingresos que se generen en el mismo periodo,
independientemente de la fecha de cobro. Es fundamento del estado de resultados.

=== USUARIOS DE LA INFORMACIÓN FINANCIERA (pág. 29-32) ===
USUARIOS EXTERNOS: Inversionistas, Bancos, SHCP, Accionistas, Proveedores, CNBV, Clientes, Acreedores, Intermediarios financieros, Público inversionista, Fisco.
USUARIOS INTERNOS: Gerente de ventas, Analista financiero, Jefe de crédito y cobranza, Director general, Gerentes, Jefe de personal, Empleados.

SUBSISTEMAS CONTABLES:
- Contabilidad Financiera (CF): para Acreedores, Intermediarios financieros, Público inversionista.
- Contabilidad Administrativa (CA): para Director general, Gerentes, Jefe de personal, Empleados.
- Contabilidad Fiscal (F): para SHCP, Fisco, CNBV.

=== EJERCICIOS DE APLICACIÓN ===
1. Herramientas con vida de 3 años registradas como gasto total del mes. INCORRECTO. Postulado: Asociación de costos y gastos con ingresos.
2. Automóviles de dueños NO incluidos en estados financieros. CORRECTO. Postulado: Entidad económica.
3. Métodos de valuación de inventarios siempre iguales. CORRECTO. Postulado: Consistencia.
4. Ventas de diciembre registradas aunque cobro sea en 60 días. CORRECTO. Postulado: Devengación contable.
5. Mercancía registrada al precio de adquisición (no al nuevo precio anunciado). CORRECTO. Postulado: Valuación.
6. Empresa que planea seguir operando presenta activos a valores de liquidación. INCORRECTO. Postulado: Negocio en marcha.
7. Renta de bodega como ingreso normal en empresa de colchones. INCORRECTO. Postulado: Sustancia económica.
8. Compra a crédito: solo se registra inventario, sin reconocer deuda. INCORRECTO. Postulado: Dualidad económica.

=== OBLIGACIONES FISCALES (SAT México) ===
Impuestos: ISR, IVA, IEPS, ISAN.
Sanciones: Multas (Art. 70-91 CFF), Actualizaciones y Recargos (Art. 21 CFF), Penas privativas de libertad, Gastos de ejecución.
"""

SYSTEM_PROMPT = f"""Eres un asistente educativo especializado en el cuestionario de "Postulados Básicos de la Información Financiera".
Responde ÚNICAMENTE basándote en el siguiente contenido del documento.
Si la pregunta no está relacionada con el documento, indica amablemente que solo puedes responder sobre este cuestionario.
Responde en español, de forma clara y concisa. Máximo 3 párrafos cortos.
Para preguntas de verdadero/falso o de opción múltiple, da primero la respuesta correcta y luego una breve explicación.

CONTENIDO DEL DOCUMENTO:
{PDF_CONTEXT}"""


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            messages = body.get("messages", [])

            api_key = os.environ.get("GEMINI_API_KEY", "")
            if not api_key:
                self._respond(500, {"error": "GEMINI_API_KEY no configurada en el servidor."})
                return

            # Convertir historial al formato de Gemini
            gemini_contents = []
            for msg in messages[-10:]:
                role = "user" if msg["role"] == "user" else "model"
                gemini_contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })

            payload = json.dumps({
                "system_instruction": {
                    "parts": [{"text": SYSTEM_PROMPT}]
                },
                "contents": gemini_contents,
                "generationConfig": {
                    "maxOutputTokens": 1024,
                    "temperature": 0.3
                }
            }).encode()

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())

            reply = data["candidates"][0]["content"]["parts"][0]["text"]
            self._respond(200, {"reply": reply})

        except urllib.error.HTTPError as e:
            err = e.read().decode()
            self._respond(e.code, {"error": f"Error de API: {err}"})
        except Exception as e:
            self._respond(500, {"error": str(e)})

    def _respond(self, code, body):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args):
        pass
