# Flask Auth + Calculadora (Villarroel)

Aplicacion Flask minimal con registro/login en memoria y calculadora con interpretacion de lenguaje natural. Incluye contenedor, pruebas y pipeline CI/CD para GHCR y despliegue en un stack remoto.

## Uso local
1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
2. Ejecuta:
   ```bash
   python app.py
   ```
3. Endpoints utiles:
   - `POST /api/register` -> `{"username": "ana", "password": "secreto"}`
   - `POST /api/login`
   - `POST /api/calc`
   - `GET /health`

## Pruebas
```bash
pytest
```

## Contenedor
El Dockerfile requerido por la consigna se llama `villarroel`. Para construir la version 3.0.0:
```bash
docker build -f villarroel -t ghcr.io/<owner>/villarroel:3.0.0 .
docker run -p 5000:5000 ghcr.io/<owner>/villarroel:3.0.0
```

## Pipeline CI/CD (GitHub Actions)
- Rama de trabajo: `villarroel`.
- Flujo:
  1) `test`: instala dependencias y ejecuta `pytest`.
  2) `build_and_push`: construye y publica la imagen en GHCR con tags `3.0.0` y `latest` (`ghcr.io/<owner>/villarroel`), usando el Dockerfile `villarroel`.
  3) `deploy`: copia `villarroel.yml` al VPS y hace `docker stack deploy` contra el stack remoto.

### Secrets requeridos
- `GHCR_PAT`: token con `packages:write` (lo usa GHCR y el VPS).
- `VPS_HOST`, `VPS_USER`, `VPS_PASSWORD`, `VPS_SSH_PORT`: acceso SSH al VPS.
- `STACK_NAME`: nombre del stack swarm preexistente (ej. `villarroel-stack`).

### Variables en runtime del pipeline
- `IMAGE_VERSION` (default `3.0.0`), `APP_NAME` (`villarroel`), `GH_OWNER` (dueño del repo en lower-case), `DOCKERFILE` (`villarroel`), `STACK_FILE` (`villarroel.yml`).

## Stack de despliegue
`villarroel.yml` usa `GH_OWNER` e `IMAGE_VERSION` para apuntar a la imagen publicada y expone el servicio por Traefik con el host `villarroel.byronrm.com`. Ejemplo manual (el pipeline ya lo hace):
```bash
IMAGE_VERSION=3.0.0 GH_OWNER=<owner> docker stack deploy -c villarroel.yml <STACK_NAME>
```

## Subdominio
El subdominio de ejemplo `villarroel.byronrm.com` debe apuntar al VPS donde corre el stack. Verifica con `dig +short villarroel.byronrm.com` que resuelva a la IP del VPS y que Traefik tenga los certificados listos.
