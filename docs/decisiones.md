# Decisiones de Arquitectura

Registro de decisiones técnicas tomadas durante el desarrollo del proyecto, con su justificación.

---

## 1. Ambientes separados: dev y prod como proyectos GCP distintos

**Decisión**: usar dos proyectos GCP separados (`red-transporte-gcp-dev` y `red-transporte-gcp-prod`) en vez de un solo proyecto con recursos diferenciados por nombre.

**Alternativa considerada**: un único proyecto con sufijos de ambiente en cada recurso (ej. `bucket-dev`, `bucket-prod`).

**Por qué**: proyectos separados dan aislamiento real de IAM, billing y recursos — un error en dev no puede afectar prod porque ni siquiera comparten espacio de nombres. Es el patrón que se usa en empresas reales, aunque implique más configuración duplicada (mitigable a futuro con Infraestructura como Código).

---

## 2. Región: southamerica-west1 (Santiago)

**Decisión**: todos los recursos se despliegan por defecto en `southamerica-west1` (Santiago, Chile).

**Por qué**: los datos son de transporte público de Santiago — coherencia geográfica, menor latencia, y es la única región de GCP físicamente en Chile. Nota: algunos servicios podrían no estar disponibles ahí; si ocurre, se evalúa `southamerica-east1` (São Paulo) como alternativa puntual.

---

## 3. Orquestación: Workflows en vez de Cloud Composer para el pipeline principal

**Decisión**: el pipeline productivo se orquesta con **Workflows**, no Cloud Composer.

**Alternativa considerada**: Cloud Composer (Airflow administrado).

**Por qué**: Composer tiene un costo base fijo por tener el entorno corriendo 24/7, injustificado para un pipeline simple y de bajo volumen como este. Workflows es serverless, se paga por ejecución, y es suficiente para un flujo lineal de pasos. Composer se explora aparte, de forma acotada, solo con fines de aprendizaje.

---

## 4. Ingesta desacoplada con Pub/Sub (patrón productor/consumidor)

**Decisión**: separar la ingesta cruda (Cloud Run "ingestor") del procesamiento (Cloud Run "processor") mediante un tópico de Pub/Sub entre ambos.

**Alternativa considerada**: un solo servicio que llama las APIs y procesa todo en la misma ejecución.

**Por qué**: aunque las APIs son de datos relativamente estáticos, este patrón refleja el diseño real usado en producción (desacople, resiliencia a fallos, posibilidad de agregar consumidores futuros sin tocar la ingesta). Es también uno de los patrones más preguntados en entrevistas de Data Engineering.

---

## 5. Autenticación GitHub: SSH dedicado con alias de host

**Decisión**: usar una llave SSH exclusiva para la cuenta personal `cristobalbn`, con un alias de host (`github.com-cristobalbn`) definido en `~/.ssh/config`, en vez de usar la configuración global de Git (que está vinculada a la cuenta de trabajo).

**Por qué**: permite tener múltiples identidades de GitHub en la misma máquina sin conflicto, sin alterar la configuración usada para repos de trabajo.

---

## 6. Docker como base para Cloud Run

**Decisión**: todos los servicios de Cloud Run se empaquetan como imágenes Docker, gestionadas vía Artifact Registry.

**Por qué**: es un requisito técnico de Cloud Run (ejecuta contenedores, no código suelto), y además garantiza reproducibilidad entre entorno local y GCP, además de ser una habilidad transversal muy demandada en el mercado.

---

## 7. Cloud Run Jobs (no Service) para el ingestor

**Decisión**: el ingestor se implementa como **Cloud Run Job**, no como Cloud Run Service.

**Alternativa considerada**: Cloud Run Service, disparado por HTTP desde Cloud Scheduler.

**Por qué**: el ingestor necesita llamar el endpoint `conocerecorrido` una vez por cada uno de
los 417 códigos de servicio, aplicando throttling de ~1 request/segundo por respeto al backend
de red.cl (ver sección "Buenas prácticas hacia la API de red.cl" más abajo). Esto implica una
ejecución de varios minutos, lo cual no calza con el modelo request/response de Cloud Run
Service (pensado para respuestas rápidas). Cloud Run Jobs está diseñado para tareas tipo batch
de duración variable, sin el límite de timeout ajustado de un servicio HTTP, y de todas formas
puede ser disparado por Cloud Scheduler (vía la API de Jobs).

---

## Buenas prácticas hacia la API de red.cl

Como red.cl no es una API pública oficial (es un endpoint interno reverse-engineered del
propio sitio, corriendo sobre un servidor HTTP básico y aparentemente frágil), el pipeline
sigue estas reglas de "buen ciudadano":

1. **Throttling**: máximo 1 request/segundo, aunque no se haya detectado un límite explícito.
2. **Identificación honesta**: User-Agent propio (`red-transporte-gcp-portfolio-project/1.0`),
   sin simular ser un navegador.
3. **Frecuencia de ingesta baja**: el pipeline completo corre a lo sumo una vez al día (a
   evaluar si incluso menos, dado que los datos de rutas/paraderos cambian poco).
4. **Caché propio**: no se vuelve a pedir un recorrido ya obtenido en la ejecución del día,
   ya que la API no expone headers de `Cache-Control`.
5. **Horario fuera de peak**: ejecución programada de madrugada (hora Chile).
6. **Backoff en fallos**: reintentos con backoff exponencial, nunca reintento agresivo en loop.

---

## 8. Monitoreo y alertas: Cloud Logging + Monitoring (no un agente LLM, por ahora)

**Decisión**: las alertas de fallos del pipeline se implementan con **Cloud Logging +
Cloud Monitoring (log-based alerting)**, notificando por correo electrónico.

**Alternativa considerada**: un agente basado en LLM que lea los logs y genere un
diagnóstico/resumen inteligente de fallos.

**Por qué**: el mecanismo nativo de GCP (logs estructurados -> alerting policy -> notificación)
cubre el caso real necesario ("avisar cuando algo falla") de forma robusta, gratuita (dentro de
la cuota gratis de Cloud Logging, 50 GB/mes) y sin agregar complejidad adicional al pipeline
core. Es además el patrón estándar usado en la industria para monitoreo básico.

**Pendiente futuro (fuera del alcance actual)**: un agente de diagnóstico de logs basado en
LLM (Vertex AI/Gemini o API de Claude) que interprete fallos recurrentes y sugiera causas
(ej. "el código 506 lleva 3 días fallando con timeout, posible cambio en el endpoint de
origen"). Técnicamente viable sin tocar el crédito principal de GCP (Vertex AI tiene cuota
gratuita separada), pero se deja como extensión posterior al pipeline base, para no mezclar
la construcción del sistema principal con la de un segundo sistema de diagnóstico.