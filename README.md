# Fichaje Automático CADATA - COMARB

Automatiza el registro de **entrada** y **salida** diario en el sistema CADATA de COMARB usando GitHub Actions.

## Cómo funciona

- **Entrada** → POST a `ciFichajeList.do` con `method=add` (simula clic en "ENTRADA DE FICHAJE")
- **Salida** → GET a `ciFichajeList.do?method=close` (simula clic en "SALIDA DE FICHAJE")
- Excluye fines de semana y feriados nacionales argentinos (2025-2026)

## Configuración paso a paso

### 1. Crear repositorio privado en GitHub

1. Ir a [github.com/new](https://github.com/new)
2. Nombre: `fichaje-comarb` (o el que prefieras)
3. **Marcarlo como Privado**
4. Crear repositorio

### 2. Subir los archivos

La estructura debe ser:

```
fichaje-comarb/
├── .github/
│   └── workflows/
│       ├── fichaje_entrada.yml
│       └── fichaje_salida.yml
├── fichaje_comarb.py
├── requirements.txt
└── README.md
```

Por terminal:

```bash
git clone https://github.com/TU_USUARIO/fichaje-comarb.git
cd fichaje-comarb
# Copiar los archivos respetando la estructura
git add .
git commit -m "Configuración inicial del fichaje automático"
git push
```

### 3. Configurar credenciales (Secrets)

1. En el repositorio → **Settings → Secrets and variables → Actions**
2. Crear dos secrets:

| Nombre            | Valor          |
|-------------------|----------------|
| `CADATA_USUARIO`  | tu usuario     |
| `CADATA_CLAVE`    | tu contraseña  |

### 4. Probar manualmente

1. Ir a la pestaña **Actions**
2. Seleccionar **"Fichaje COMARB - Entrada"**
3. Clic en **Run workflow → Run workflow**
4. Revisar los logs para confirmar que funcionó

## Horarios configurados

| Acción  | Hora Argentina | Hora UTC (cron)       |
|---------|----------------|-----------------------|
| Entrada | 10:00          | `0 13 * * 1-5`       |
| Salida  | 18:00          | `0 21 * * 1-5`       |

Para cambiar horarios, editar los archivos en `.github/workflows/`. La conversión es: **Hora UTC = Hora Argentina + 3**.

## Notas

- **Demora de GitHub Actions:** Los cron pueden tener un retraso de 5 a 30 minutos. Si necesitás más precisión, programá un poco antes.
- **Feriados:** Incluidos los de 2025 y 2026. Actualizar anualmente en `fichaje_comarb.py`.
- **Límite gratuito:** GitHub Actions ofrece 2,000 min/mes gratis en repos privados. Cada ejecución usa ~1 minuto (~44 min/mes con entrada y salida).
- **Logs:** Visibles en la pestaña Actions de tu repositorio.
