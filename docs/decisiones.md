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