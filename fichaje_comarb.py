"""
Fichaje automático - CADATA COMARB
====================================
Automatiza el registro de ENTRADA y SALIDA en:
https://cadata.comarb.gob.ar/cadata/ciFichajeList.do

Uso:
    python fichaje_comarb.py entrada
    python fichaje_comarb.py salida
"""

import os
import sys
import logging
from datetime import date, datetime, timezone, timedelta

import requests

# ─── Configuración de logging ───────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ─── Zona horaria Argentina (UTC-3) ─────────────────────────────────────────
TZ_AR = timezone(timedelta(hours=-3))

# ─── URLs ────────────────────────────────────────────────────────────────────
URL_LOGIN_PAGE = "https://cadata.comarb.gob.ar/cadata/login.jsp"
URL_LOGIN_POST = "https://cadata.comarb.gob.ar/cadata/j_security_check"
URL_FICHAJE_ENTRADA = "https://cadata.comarb.gob.ar/cadata/ciFichajeList.do"
URL_FICHAJE_SALIDA = "https://cadata.comarb.gob.ar/cadata/ciFichajeList.do?method=close"

# ─── Feriados Argentina 2025 y 2026 ─────────────────────────────────────────
FERIADOS = {
    # 2026
    date(2026, 1, 1),    # Año Nuevo
    date(2026, 2, 16),   # Carnaval
    date(2026, 2, 17),   # Carnaval
    date(2026, 3, 23),
    date(2026, 3, 24),   # Día de la Memoria
    date(2026, 4, 2),    # Día del Veterano y de los Caídos de Malvinas
    date(2026, 4, 3),
    date(2026, 4, 9),    # Viernes Santo
    date(2026, 5, 1),    # Día del Trabajador
    date(2026, 5, 4),
    date(2026, 5, 25),   # Día de la Revolución de Mayo
    date(2026, 6, 15),   # Paso a la Inmortalidad del Gral. Güemes
    date(2026, 6, 20),   # Día de la Bandera
    date(2026, 7, 9),
    date(2026, 7, 10),  # Día de la Independencia
    date(2026, 8, 17),   # Paso a la Inmortalidad del Gral. San Martín
    date(2026, 10, 12),  # Día del Respeto a la Diversidad Cultural
    date(2026, 11, 23),  # Día de la Soberanía Nacional
    date(2026, 12, 7), 
    date(2026, 12, 8),   # Inmaculada Concepción de María
    date(2026, 12, 25),  # Navidad
}


def es_dia_laborable() -> bool:
    """Retorna True si hoy (hora Argentina) es día laborable."""
    hoy = datetime.now(TZ_AR).date()
    if hoy.weekday() >= 5:
        log.info(f"Hoy es fin de semana ({hoy.strftime('%A %d/%m/%Y')}). No se ficha.")
        return False
    if hoy in FERIADOS:
        log.info(f"Hoy es feriado ({hoy.strftime('%d/%m/%Y')}). No se ficha.")
        return False
    log.info(f"Hoy es día laborable: {hoy.strftime('%d/%m/%Y')}")
    return True


def login(session: requests.Session) -> None:
    """Inicia sesión en CADATA y mantiene la sesión activa."""
    usuario = os.getenv("CADATA_USUARIO")
    clave = os.getenv("CADATA_CLAVE")

    if not usuario or not clave:
        log.error("No se encontraron las credenciales (CADATA_USUARIO / CADATA_CLAVE).")
        sys.exit(1)

    # 1. GET login page para obtener cookies (JSESSIONID)
    log.info("Accediendo a la página de login...")
    resp = session.get(URL_LOGIN_PAGE)
    resp.raise_for_status()
    log.info(f"Cookies obtenidas: {list(session.cookies.keys())}")

    # 2. POST login con credenciales
    log.info("Enviando credenciales...")
    resp = session.post(URL_LOGIN_POST, data={
        "j_username": usuario,
        "j_password": clave,
    }, allow_redirects=True)
    resp.raise_for_status()

    # Verificar login exitoso
    if "login.jsp" in resp.url:
        log.error("❌ Login fallido. Verificá usuario y contraseña.")
        sys.exit(1)

    log.info(f"✅ Login exitoso. URL: {resp.url}")

    # 3. Aceptar acuerdo de confidencialidad si aparece
    if "confidencialidad" in resp.text.lower():
        log.info("Aceptando acuerdo de confidencialidad...")
        resp = session.post(resp.url, data={"acepta": "true"}, allow_redirects=True)
        resp.raise_for_status()
        log.info("Acuerdo aceptado.")


def fichar_entrada(session: requests.Session) -> None:
    """Registra la ENTRADA de fichaje (POST con method=add)."""
    log.info("Registrando ENTRADA de fichaje...")

    # Primero verificar que el botón de entrada está disponible
    resp = session.get(URL_FICHAJE_ENTRADA, params={"method": "list"})
    resp.raise_for_status()

    if "ENTRADA DE FICHAJE" not in resp.text:
        log.warning("⚠️ No se encontró el botón 'ENTRADA DE FICHAJE'.")
        log.warning("Puede que ya se haya fichado la entrada hoy.")
        return

    # POST para registrar entrada (form ciFichajeListAdd con method=add)
    resp = session.post(URL_FICHAJE_ENTRADA, data={
        "method": "add",
    }, allow_redirects=True)
    resp.raise_for_status()

    ahora = datetime.now(TZ_AR).strftime("%d/%m/%Y %H:%M:%S")
    log.info(f"✅ ENTRADA registrada exitosamente - {ahora}")


def fichar_salida(session: requests.Session) -> None:
    """Registra la SALIDA de fichaje (GET a method=close)."""
    log.info("Registrando SALIDA de fichaje...")

    # GET para registrar salida (botón onclick -> location.href='ciFichajeList.do?method=close')
    resp = session.get(URL_FICHAJE_SALIDA, allow_redirects=True)
    resp.raise_for_status()

    # Verificar que se procesó (la página muestra "Registro de salida guardado")
    if "salida guardado" in resp.text.lower() or "salida" in resp.text.lower():
        ahora = datetime.now(TZ_AR).strftime("%d/%m/%Y %H:%M:%S")
        log.info(f"✅ SALIDA registrada exitosamente - {ahora}")
    else:
        log.warning("⚠️ No se pudo confirmar el registro de salida. Revisar manualmente.")


def main():
    # Determinar acción: entrada o salida
    if len(sys.argv) < 2 or sys.argv[1] not in ("entrada", "salida"):
        print("Uso: python fichaje_comarb.py [entrada|salida]")
        sys.exit(1)

    accion = sys.argv[1]

    log.info("=" * 60)
    ahora = datetime.now(TZ_AR).strftime("%d/%m/%Y %H:%M:%S")
    log.info(f"Fichaje {accion.upper()} - {ahora} (hora Argentina)")
    log.info("=" * 60)

    if not es_dia_laborable():
        log.info("No es día laborable. Finalizando.")
        return

    # Crear sesión HTTP
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    })

    try:
        login(session)

        if accion == "entrada":
            fichar_entrada(session)
        else:
            fichar_salida(session)

    except requests.RequestException as e:
        log.error(f"❌ Error de conexión: {e}")
        sys.exit(1)
    except Exception as e:
        log.error(f"❌ Error inesperado: {e}")
        sys.exit(1)

    log.info("Proceso finalizado.")


if __name__ == "__main__":
    main()
