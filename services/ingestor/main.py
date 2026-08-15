import requests
import time
import json
from google.cloud import storage
from datetime import datetime
from zoneinfo import ZoneInfo

def obtener_fecha_ejecucion() -> str:
    # obtiene la fecha de hoy en la zona horaria de Chile, no la del servidor
    ahora_chile = datetime.now(ZoneInfo("America/Santiago"))
    return ahora_chile.strftime("%Y-%m-%d")

def obtener_lista_servicios() -> list[str]:
    url = "https://www.red.cl/restservice_v2/rest/getservicios/all"
    headers = {"User-Agent": "red-transporte-gcp-portfolio-project/1.0"}

    respuesta = requests.get(url, headers=headers, timeout=10)
    respuesta.raise_for_status()

    return respuesta.json()

def obtener_recorrido(codigo: str, intentos_maximos: int = 3) -> dict | None:
    url = "https://www.red.cl/restservice_v2/rest/conocerecorrido"
    headers = {"User-Agent": "red-transporte-gcp-portfolio-project/1.0"}
    params = {"codsint": codigo}

    for intento in range(1, intentos_maximos + 1):
        try:
            respuesta = requests.get(url, headers=headers, params=params, timeout=10)
            respuesta.raise_for_status()
            return respuesta.json()

        except requests.exceptions.HTTPError as error:
            if respuesta.status_code == 400:
                print(f"[{codigo}] codigo invalido (400), no se reintenta")
                return None

            print(f"[{codigo}] intento {intento}/{intentos_maximos} fallo: {error}")
            if intento < intentos_maximos:
                time.sleep(2 ** intento)

        except requests.exceptions.RequestException as error:
            print(f"[{codigo}] intento {intento}/{intentos_maximos} fallo: {error}")
            if intento < intentos_maximos:
                time.sleep(2 ** intento)

    print(f"[{codigo}] fallo definitivamente tras {intentos_maximos} intentos")
    return None

def guardar_json_en_bucket(bucket_nombre: str, ruta: str, contenido) -> None:
    cliente = storage.Client()
    bucket = cliente.bucket(bucket_nombre)
    blob = bucket.blob(ruta)

    blob.upload_from_string(
        data=json.dumps(contenido, ensure_ascii=False, indent=2),
        content_type="application/json",
    )

    print(f"guardado: gs://{bucket_nombre}/{ruta}")

def leer_metadata(bucket_nombre: str, fecha: str) -> dict | None:
    cliente = storage.Client()
    bucket = cliente.bucket(bucket_nombre)
    ruta = f"recorridos/fecha_ejecucion={fecha}/_metadata.json"
    blob = bucket.blob(ruta)

    if not blob.exists():
        return None

    contenido = blob.download_as_text()
    return json.loads(contenido)


def escribir_metadata(bucket_nombre: str, fecha: str, metadata: dict) -> None:
    ruta = f"recorridos/fecha_ejecucion={fecha}/_metadata.json"
    guardar_json_en_bucket(bucket_nombre, ruta, metadata)