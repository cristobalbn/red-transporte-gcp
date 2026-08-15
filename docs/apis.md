# APIs no oficiales de red.cl

Documentación de los dos endpoints REST no oficiales que expone red.cl (sitio de transporte
público de Santiago), obtenida por pruebas directas con `curl` el 2026-08-15. No hay
documentación oficial pública de estas APIs — es la que consume el propio frontend de red.cl.

---

## 1. `GET /restservice_v2/rest/getservicios/all`

**URL completa**: `https://www.red.cl/restservice_v2/rest/getservicios/all`

Devuelve la lista completa de códigos de servicios (recorridos) de la red de buses.

### Headers requeridos

**Ninguno.** Responde `200 OK` incluso sin `User-Agent` explícito (probado con el UA por
defecto de curl). No exige `Referer`, `X-Requested-With` ni ningún otro header especial.

### Respuesta

- `Content-Type: application/json`
- `Access-Control-Allow-Origin: https://www.red.cl` (CORS restringido a ese origen — solo
  relevante para llamadas desde un navegador; no afecta llamadas server-to-server).
- Es un **array JSON plano de strings**, sin objeto contenedor.

```json
["101", "102", "103", "104", "105", "105c", "106", "107", "107c", "108", "109", "109n",
 "110", "110c", "111", "113", "113c", "113e", "114", ...]
```

- **Total observado**: 417 códigos de servicio.
- Los códigos siguen el patrón `<número><sufijo opcional>`, donde el sufijo indica variante de
  recorrido: `c` (circular / corto?), `e` (expreso), `n` (nocturno), etc. Esto no está
  confirmado por la API, es inferencia a partir de la nomenclatura de Red Metropolitana.
- Este código (`codsint` en la nomenclatura del segundo endpoint) es el identificador a usar
  contra `conocerecorrido`.

---

## 2. `GET /restservice_v2/rest/conocerecorrido?codsint={codigo}`

**URL completa**: `https://www.red.cl/restservice_v2/rest/conocerecorrido?codsint=506`

Devuelve el detalle completo de un recorrido: empresa operadora, ida y regreso, con paraderos
y trazado geográfico.

### Headers requeridos

**Ninguno.** A diferencia de lo esperado, respondió `200 OK` en todas las combinaciones
probadas, incluida una petición sin ningún header adicional (solo lo que curl manda por
defecto: `Host`, `Accept: */*`, sin `User-Agent` custom). Se probó además:

- Solo `User-Agent`
- `User-Agent` + `Referer: https://www.red.cl/`
- `User-Agent` + `Referer` + `X-Requested-With: XMLHttpRequest`
- Set completo tipo navegador (UA de Chrome + Referer de página específica + `Accept:
  application/json...`)

Todas dieron `200`. **El error 400 original probablemente no era por falta de headers**, sino
por el valor de `codsint` usado en la prueba (ver sección de errores más abajo — un `codsint`
con formato inválido, o ausente, da 400 independientemente de los headers).

Conclusión práctica para el pipeline: no hace falta simular un navegador, un `curl` o cliente
HTTP simple sin headers extra funciona.

### Parámetros

| Parámetro | Tipo | Requerido | Descripción |
|---|---|---|---|
| `codsint` | string | Sí | Código del servicio (ver endpoint 1). Debe existir en la lista de `getservicios/all`. |

### Respuesta exitosa (200)

- `Content-Type: application/json`
- Objeto JSON con tres claves de primer nivel: `negocio`, `ida`, `regreso`.

```json
{
  "negocio": {
    "id": 5,
    "nombre": "Buses Metropolitana S.A.",
    "color": "#0093B3",
    "url": "http://www.transantiago.cl/es/empresas/metbus.html"
  },
  "ida": {
    "id": 169,
    "horarios": [
      {"tipoDia": "Sábado", "inicio": "00:00", "fin": "23:59"},
      {"tipoDia": "Lunes a Viernes", "inicio": "00:00", "fin": "23:59"},
      {"tipoDia": "Domingo y Festivos", "inicio": "00:00", "fin": "23:59"}
    ],
    "paraderos": [
      {
        "id": 11212,
        "cod": "PI369",
        "num": 0,
        "pos": [-33.5197199, -70.79466],
        "name": "Avenida Portales esq. La Galaxia",
        "comuna": "MAIPÚ",
        "type": 0,
        "servicios": [],
        "stop": {
          "stopCoordenadaX": "-33.5197199",
          "stopCoordenadaY": "-70.7946600",
          "stopId": 1277039
        },
        "eje": "Avenida Portales",
        "codSimt": "PI369",
        "distancia": 0
      }
    ],
    "path": [[-33.520917, -70.800861], [-33.520887, -70.800852], [-33.520827, -70.800847]],
    "destino": "Peñalolén",
    "itinerario": false
  },
  "regreso": {
    "id": 170,
    "horarios": [ "... misma forma que ida.horarios ..." ],
    "paraderos": [ "... misma forma que ida.paraderos ..." ],
    "path": [ "... misma forma que ida.path ..." ],
    "destino": "Maipú",
    "itinerario": false
  }
}
```

### Estructura de campos

**`negocio`** (empresa operadora del servicio):

| Campo | Tipo | Ejemplo |
|---|---|---|
| `id` | number | `5` |
| `nombre` | string | `"Buses Metropolitana S.A."` |
| `color` | string (hex) | `"#0093B3"` |
| `url` | string (URL) | `"http://www.transantiago.cl/es/empresas/metbus.html"` |

**`ida` / `regreso`** (mismo shape para ambos sentidos del recorrido):

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | number | ID interno del tramo (distinto entre ida y regreso). |
| `horarios` | array de objetos | Ventanas horarias por tipo de día. Siempre 3 entradas observadas: Sábado, Lunes a Viernes, Domingo y Festivos. |
| `paraderos` | array de objetos | Paraderos ordenados en el recorrido (91 en `ida`, 92 en `regreso` para el 506; 76/71 para el 101 — varía por servicio). |
| `path` | array de `[lat, lon]` | Polilínea del trazado geográfico, cientos de puntos (850+ observado). Útil para dibujar la ruta en un mapa, no coincide 1:1 con los paraderos. |
| `destino` | string | Nombre del destino final de ese sentido. |
| `itinerario` | boolean | Observado siempre `false` en las pruebas — significado no confirmado. |

**`horarios[]`**:

| Campo | Tipo | Ejemplo |
|---|---|---|
| `tipoDia` | string | `"Lunes a Viernes"`, `"Sábado"`, `"Domingo y Festivos"` |
| `inicio` | string (HH:MM) | `"05:30"` |
| `fin` | string (HH:MM) | `"23:47"` |

**`paraderos[]`**:

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | number | ID interno del paradero. |
| `cod` | string | Código de paradero visible en la vía pública (ej. `"PI369"`). |
| `num` | number | Observado siempre `0` en las muestras — significado no confirmado. |
| `pos` | `[lat, lon]` | Coordenadas del paradero. |
| `name` | string | Nombre/dirección del paradero. |
| `comuna` | string | Comuna en mayúsculas (ej. `"MAIPÚ"`, `"RECOLETA"`). |
| `type` | number | Observado siempre `0` — probablemente distingue tipo de parada (normal, terminal, etc.) pero no se observaron otros valores. |
| `servicios` | array | **Siempre vacío (`[]`) en todas las muestras** — se esperaría que listara otros servicios que pasan por ese paradero, pero no viene poblado en esta respuesta. No confiar en este campo para cruces de servicios por paradero. |
| `stop` | object | Sub-objeto con coordenadas duplicadas (como string) y `stopId`. |
| `eje` | string | Nombre del eje vial donde está el paradero. |
| `codSimt` | string | Código SIMT del paradero (en las muestras, igual a `cod`). |
| `distancia` | number | Observado siempre `0` — probablemente distancia acumulada desde el paradero anterior, no poblada en estas respuestas. |

**`stop`** (sub-objeto de cada paradero):

| Campo | Tipo | Ejemplo |
|---|---|---|
| `stopCoordenadaX` | string (numérico) | `"-33.5197199"` (latitud, duplica `pos[0]`) |
| `stopCoordenadaY` | string (numérico) | `"-70.7946600"` (longitud, duplica `pos[1]`) |
| `stopId` | number | `1277039` |

### Casos de error observados

| Caso | HTTP | Body |
|---|---|---|
| `codsint` ausente | 400 | `Falta el parámetro 'codsint'.` |
| `codsint` con formato inválido (ej. `ZZZZZ`) | 400 | `Formato incorrecto para el parámetro 'codsint'.` |
| `codsint` válido, cualquier combinación de headers | 200 | JSON normal |

⚠️ **Comportamiento anómalo detectado**: al pedir el endpoint **sin el parámetro `codsint`**,
el cuerpo de la respuesta viene con dos mensajes de error concatenados sin separador, como si
el backend hubiera pegado la respuesta cruda de una segunda llamada interna dentro del body de
la primera:

```
Falta el parámetro 'codsint'.HTTP/1.0 400 Bad Request
Server: BaseHTTP/0.6 Python/3.12.3
Date: Sat, 15 Aug 2026 05:02:40 GMT
Access-Control-Allow-Origin: https://www.red.cl
Content-Type: text/plain

Formato incorrecto para el parámetro 'codsint'.
```

Esto se reprodujo de forma consistente en 3 intentos separados, con el mismo timestamp `Date`
en cada uno (05:02:40 GMT) pese a estar espaciados en el tiempo — sugiere que esa respuesta de
error específica está **cacheada** en algún proxy/CDN delante del backend, y que el backend
(`BaseHTTP/0.6 Python/3.12.3`, un servidor HTTP muy básico escrito a mano, no un framework
como Flask/Django) tiene un bug donde bajo ciertas condiciones concatena texto de otra
respuesta HTTP cruda dentro del body. **Implicación para el pipeline**: el parseo de errores
no debe asumir que el body de un 400 es un mensaje de texto simple y único; hay que tratarlo
como texto libre y no intentar parsearlo como JSON.

### Headers de respuesta (ambos endpoints)

```
HTTP/1.1 200 OK
Server: BaseHTTP/0.6 Python/3.12.3
X-Frame-Options: SAMEORIGIN
Strict-Transport-Security: max-age=86400; includeSubDomains
Access-Control-Allow-Origin: https://www.red.cl
Content-Type: application/json
Transfer-Encoding: chunked
```

No hay headers de `Cache-Control`, `ETag`, `Last-Modified` ni ningún header de rate limiting
(`X-RateLimit-*`, `Retry-After`) en ninguna respuesta observada.

El servidor (`BaseHTTP/0.6 Python/3.12.3`) es el servidor HTTP mínimo de la librería estándar
de Python (`http.server`), no un servidor de producción típico (nginx, gunicorn, etc.). Esto
explica el comportamiento anómalo del punto anterior y sugiere que el backend es bastante
simple/artesanal — vale la pena que el pipeline sea tolerante a errores inesperados y no
asuma alta disponibilidad ni consistencia estricta.

### Rate limiting

**No se detectó rate limiting** en las pruebas:

- 10 llamadas consecutivas a `getservicios/all` (~200ms de intervalo entre cada una): las 10
  devolvieron `200`.
- 15 llamadas a `conocerecorrido` con `codsint` distintos: las 15 devolvieron `200`.
- 20 llamadas consecutivas al mismo `codsint=506`: las 20 devolvieron `200`, sin variación.

No se observaron headers `Retry-After` ni respuestas `429`. Esto no descarta que exista un
límite más alto (por IP, por ventana de tiempo mayor) no alcanzado en estas pruebas — para un
pipeline de producción igual conviene aplicar throttling propio (ej. 1 request/segundo) por
buena práctica y para no depender de un comportamiento no garantizado ni documentado
oficialmente por red.cl.

---

## Resumen para diseño del pipeline de ingesta

1. **Sin autenticación ni headers especiales** — un cliente HTTP simple (Cloud Run + `requests`
   o similar) basta, sin necesidad de simular navegador.
2. **Flujo natural**: `getservicios/all` → iterar sobre los 417 códigos → `conocerecorrido?codsint=X`
   por cada uno para obtener el detalle.
3. **Tolerancia a errores**: tratar el body de un 400 como texto plano (no JSON), y estar
   preparado para respuestas malformadas/concatenadas del backend.
4. **Sin rate limit conocido**, pero aplicar throttling propio por buena práctica y para evitar
   sobrecargar un backend que ya se ve frágil (`http.server` de Python, sin balanceo aparente).
5. Campos como `servicios`, `distancia`, `num`, `type` e `itinerario` vinieron sin poblar
   (vacíos o en `0`/`false`) en todas las muestras — no diseñar lógica de negocio que dependa
   de ellos sin antes confirmar con más muestras que alguna vez traen datos reales.
6. No hay `Cache-Control` — si se quiere evitar pegarle al mismo endpoint repetidamente en
   testing/desarrollo, cachear las respuestas del lado del pipeline (ej. en el propio bucket de
   staging), no confiar en cache HTTP.
