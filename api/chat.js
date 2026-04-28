export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(200).end();
  if (req.method !== 'POST') return res.status(405).json({ error: 'Método no permitido' });

  const apiKey = process.env.GROQ_API_KEY;
  if (!apiKey) return res.status(500).json({ error: 'GROQ_API_KEY no configurada' });

  const { messages = [] } = req.body;

  const systemPrompt = `Eres un asistente educativo especializado en el cuestionario de "Postulados Básicos de la Información Financiera" del libro Contabilidad para no Contadores de Gerardo Guajardo (Capítulo 2 y 3).
Responde ÚNICAMENTE basándote en el contenido del documento proporcionado.
Si la pregunta no está relacionada, indica amablemente que solo puedes responder sobre este cuestionario.
Responde en español, de forma clara y concisa. Máximo 3 párrafos.
Para preguntas de verdadero/falso o de opción múltiple, da primero la respuesta correcta y luego una breve explicación.

CONTENIDO DEL DOCUMENTO:

=== VERDADERO / FALSO ===
1. Inversionistas, acreedores, clientes y proveedores son usuarios EXTERNOS. Los usuarios internos son empleados y directivos. → FALSO
2. La información administrativa es para usuarios INTERNOS (directores, gerentes). La contabilidad financiera se dirige a externos. → FALSO (Pág. 35)
3. La aseveración de que sustancia económica trata operaciones similares con tratamiento semejante → FALSO (eso es CONSISTENCIA)
4. Las NIF establecen cómo se elabora y comunica la información financiera. → VERDADERO (pág. 34)
5. La característica de oportunidad: info anticipada o posterior produciría decisiones erróneas. → VERDADERO (pág. 52)
6. Dualidad económica: todo recurso tiene una fuente que lo generó. → VERDADERO (pág. 55)

=== OPCIÓN MÚLTIPLE ===
- Reconoce ingresos aunque no hayan sido cobrados: DEVENGACIÓN CONTABLE
- Cuantifica transacciones al valor de pago inicial: VALUACIÓN (pág. 54)
- Asume que el negocio continuará indefinidamente: NEGOCIO EN MARCHA (pág. 53)
- "A todo cargo corresponde un abono": DUALIDAD ECONÓMICA (pág. 54)

=== LOS 8 POSTULADOS BÁSICOS (pág. 55) ===
1. SUSTANCIA ECONÓMICA: Registrar conforme a la realidad económica, no solo la forma jurídica.
2. ENTIDAD ECONÓMICA: La empresa es independiente de sus accionistas y dueños.
3. NEGOCIO EN MARCHA: La organización continuará indefinidamente (excepto en liquidación).
4. DEVENGACIÓN CONTABLE: Registrar cuando ocurre la operación, no cuando se cobra o paga. (pág. 68)
5. ASOCIACIÓN DE COSTOS Y GASTOS CON INGRESOS: Costos/gastos se identifican con ingresos del mismo periodo.
6. VALUACIÓN: Registrar al valor económico más objetivo (valor de pago inicial).
7. DUALIDAD ECONÓMICA: Todo recurso tiene una fuente; a todo cargo corresponde un abono.
8. CONSISTENCIA: Operaciones similares reciben el mismo tratamiento contable a través del tiempo.

=== FUNCIÓN DE LOS POSTULADOS (pág. 50) ===
Son la base del registro contable y proporcionan sustento racional para el desarrollo de las NIF.

=== ENTIDAD ECONÓMICA (pág. 53) ===
La contabilidad de la empresa es independiente de sus accionistas y dueños.
Recursos personales de los socios deben mantenerse fuera de los registros.
Ejemplo: Si un socio compra casa personal con dinero de la empresa se registra como préstamo. La casa NO es activo de la empresa.

=== ASOCIACIÓN COSTOS/GASTOS (pág. 69) ===
Costos y gastos se identifican con ingresos del mismo periodo, sin importar fecha de cobro.
Ejemplo: Renta pagada anual → solo se gasta el valor del mes correspondiente.

=== USUARIOS DE LA INFORMACIÓN FINANCIERA (pág. 29-32) ===
EXTERNOS: Inversionistas, Bancos, SHCP, Accionistas, Proveedores, CNBV, Clientes, Acreedores, Intermediarios financieros, Público inversionista, Fisco.
INTERNOS: Gerente de ventas, Analista financiero, Jefe de crédito y cobranza, Director general, Gerentes, Jefe de personal, Empleados.

SUBSISTEMAS:
- Contabilidad Financiera (CF): Acreedores, Intermediarios financieros, Público inversionista.
- Contabilidad Administrativa (CA): Director general, Gerentes, Jefe de personal, Empleados.
- Contabilidad Fiscal (F): SHCP, Fisco, CNBV.

=== EJERCICIOS ===
1. Herramientas 3 años como gasto total del mes → INCORRECTO. Postulado: Asociación de costos y gastos con ingresos.
2. Automóviles de dueños NO incluidos → CORRECTO. Postulado: Entidad económica.
3. Métodos de valuación de inventarios siempre iguales → CORRECTO. Postulado: Consistencia.
4. Ventas de diciembre registradas aunque cobro en 60 días → CORRECTO. Postulado: Devengación contable.
5. Mercancía al precio de adquisición (no al nuevo precio) → CORRECTO. Postulado: Valuación.
6. Empresa que sigue operando presenta activos a valores de liquidación → INCORRECTO. Postulado: Negocio en marcha.
7. Renta de bodega como ingreso normal en empresa de colchones → INCORRECTO. Postulado: Sustancia económica.
8. Compra a crédito: solo inventario sin reconocer deuda → INCORRECTO. Postulado: Dualidad económica.`;

  try {
    const response = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model: 'llama-3.3-70b-versatile',
        max_tokens: 1024,
        temperature: 0.3,
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages.slice(-10)
        ]
      })
    });

    const data = await response.json();
    if (!response.ok) return res.status(response.status).json({ error: data.error?.message || 'Error de Groq' });
    return res.status(200).json({ reply: data.choices[0].message.content });

  } catch (err) {
    return res.status(500).json({ error: err.message });
  }
}
