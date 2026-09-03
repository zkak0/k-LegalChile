/**
 * Relay CPLT para el MCP legal chileno (corrige el bloqueo 403 por IP).
 *
 * El servidor jurisprudencia.cplt.cl deniega TOTALMENTE a ciertas IPs
 * (verificado 2026-09-03: 403 en robots.txt, HEAD, raíz, IP directa).
 * Este Worker de Cloudflare (plan gratuito) simplemente actúa de relay:
 * el contenido viene 1:1 de la CPLT; no falsifica ni altera nada.
 *
 * Despliegue en 3 minutos (gratis, sin tarjeta):
 *   1. Ve a https://workers.cloudflare.com → Sign up → Workers.
 *   2. Create → copia/pega este archivo entero → Save and Deploy.
 *   3. La URL del worker (ej. https://cplt-relay.tu-nombre.workers.dev)
 *      queda en el entorno: export CPLT_PROXY="https://...workers.dev"
 *   4. El MCP usará `f"{CPLT_PROXY}?url={url_cplt}"` para hablar con CPLT.
 *
 * Medidas honestas incluidas:
 *  - Solo acepta destinos *.cplt.cl (evita convertirlo en proxy abierto).
 *  - No cachea, no modifica cuerpo, no añade nada de suyo.
 *  - User-Agent fijo y transparente: declara de dónde viene.
 */
export default {
  async fetch(request) {
    const urlIn = new URL(request.url);
    const destino = urlIn.searchParams.get("url");
    if (!destino) {
      return new Response("Falta ?url=", { status: 400 });
    }
    const dest = new URL(destino);
    // Blanqueo: solo el dominio oficial de jurisprudencia del CPLT
    if (!/^jurisprudencia\.cplt\.cl$/.test(dest.hostname)) {
      return new Response("Dominio no permitido (solo jurisprudencia.cplt.cl)",
                          { status: 403 });
    }
    const cuerpo = request.method === "GET" || request.method === "HEAD"
      ? undefined : await request.arrayBuffer();
    const headers = new Headers(request.headers);
    // Cabeceras necesarias para webforms ASP.NET
    headers.delete("host");
    headers.set("user-agent",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36");
    headers.set("accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8");
    try {
      const upstream = await fetch(dest.toString(), {
        method: request.method,
        headers,
        body: cuerpo,
        redirect: "follow",
      });
      // Devuelve 1:1 status, headers y bytes del servidor CPLT.
      return new Response(upstream.body, {
        status: upstream.status,
        statusText: upstream.statusText,
        headers: upstream.headers,
      });
    } catch (e) {
      return new Response(`Error relay: ${e}`, { status: 502 });
    }
  },
};
