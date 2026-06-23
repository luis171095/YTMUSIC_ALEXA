# 🎵 YTMusic Alexa Skill

> Skill de Amazon Alexa que reproduce **audio de YouTube** por voz, desplegada como una función **AWS Lambda** en Python.

[![Python](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Alexa Skills Kit](https://img.shields.io/badge/Alexa-Skills%20Kit-00caff.svg)](https://developer.amazon.com/alexa)

Pídele a tu Echo que ponga cualquier canción, artista o lista de YouTube y la reproduce
como audio en segundo plano, con controles de voz nativos (siguiente, pausa, mezclar, etc.).

---

## ✨ Características

- 🔎 **Búsqueda inteligente de canciones** — prioriza la canción individual sobre compilaciones
  o mixes de varias horas (re-ranking por título y canal `- Topic`).
- ▶️ **Reproducción completa sin cortes** — usa el cliente InnerTube `android_vr` de yt-dlp,
  que entrega URLs sin el candado PO-token/SABR de YouTube (sin el corte a ~2 min).
- 🌐 **Esquiva el bloqueo de IP de AWS** — extracción a través de un proxy datacenter; el audio
  lo descarga el propio Echo desde la URL de `googlevideo`.
- 🎛️ **Controles de voz nativos** — siguiente, anterior, pausa, reanudar, mezclar, repetir,
  "¿qué está sonando?", saltar adelante/atrás, autoplay on/off.
- 📃 **Listas, canales y favoritos** — reproduce playlists, los videos de un canal o tus favoritos.
- 🌍 **Multi-idioma** — `es`, `en`, `fr`, `it`, `de`, `ja`, `pt` (según el locale del dispositivo).

---

## 🏗️ Arquitectura

```
 ┌──────────┐   voz    ┌──────────────┐   evento JSON   ┌────────────────────┐
 │  Echo /  │ ───────► │  Alexa Skills │ ──────────────► │   AWS Lambda       │
 │  Alexa+  │ ◄─────── │  Kit (ASK)    │ ◄────────────── │  lambda_function   │
 └────┬─────┘  audio   └──────────────┘  AudioPlayer.Play└─────────┬──────────┘
      │                                                            │
      │  descarga el audio directo (HTTP 206 por rangos)           │ 1) busca con
      │                                                            │    YouTube Data API
      ▼                                                            ▼ 2) extrae URL con
 ┌─────────────────┐                                    ┌────────────────────────┐
 │ googlevideo.com │ ◄───── URL m4a sin candado ─────── │ yt-dlp + proxy (android_vr) │
 └─────────────────┘                                    └────────────────────────┘
```

1. El usuario habla → Alexa envía un evento JSON al Lambda.
2. El Lambda **busca** el video con la **YouTube Data API v3** (`DEVELOPER_KEY`).
3. **Extrae** la URL de audio con **yt-dlp** (a través de un proxy, cliente `android_vr`).
4. Devuelve una directiva `AudioPlayer.Play`; el **Echo descarga el audio directamente**.

Más detalle en [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 🚀 Puesta en marcha

### Requisitos

- Cuenta de **AWS** (función Lambda, runtime **Python 3.10**, arquitectura x86_64).
- Cuenta de **desarrollador de Amazon** (Alexa Skills Kit).
- Una **API key de YouTube Data API v3** ([Google Cloud Console](https://console.cloud.google.com)).
- (Recomendado) Un **proxy datacenter** — p. ej. el tier gratuito de [Webshare](https://www.webshare.io/).
- Python 3.10+ y `pip` en tu máquina para empaquetar.

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/luis171095/YTMUSIC_ALEXA.git
cd YTMUSIC_ALEXA

# Instala las dependencias COMO WHEELS DE LINUX/PY3.10 (no de tu PC) y arma el .zip:
python build_package.py --install
```

> ⚠️ Las dependencias **no** se versionan en el repo: se regeneran con el comando de arriba,
> que usa los flags `--platform manylinux2014_x86_64 --python-version 3.10 --only-binary=:all:`
> para que las extensiones en C funcionen en el entorno Linux de Lambda.

### 2. Crear la skill en el Alexa Developer Console

1. Crea una skill **Custom** con el modelo de interacción (intents `SearchIntent`, `PlaylistIntent`, etc.).
2. Activa la interfaz **AudioPlayer**: `Build → Interfaces → Audio Player → ON → Save → Build Model`.
3. Define un **nombre de invocación** poco genérico (Alexa+ secuestra nombres comunes; evita "música").

### 3. Crear la función Lambda

1. Runtime **Python 3.10**, handler `lambda_function.lambda_handler`.
2. Sube el `alexa_skill.zip` generado.
3. Configura las **variables de entorno** (ver [`.env.example`](.env.example) y la tabla de abajo).
4. Conecta el ARN del Lambda como endpoint de la skill (trigger *Alexa Skills Kit*).

Guía paso a paso en [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

---

## ⚙️ Variables de entorno

| Variable          | Obligatoria | Descripción                                                                 |
|-------------------|:-----------:|-----------------------------------------------------------------------------|
| `DEVELOPER_KEY`   | ✅          | API key de YouTube Data API v3 (búsqueda de videos).                        |
| `proxy`           | ⭐          | Proxy datacenter `http://user:pass@host:puerto` para extraer el stream.    |
| `proxy_enabled`   | ⭐          | `true` para activar el proxy.                                               |
| `player_clients`  | ⬜          | Clientes yt-dlp; por defecto `android_vr,ios,android,tv,mweb,web`.         |
| `MY_CHANNEL_ID`   | ⬜          | Tu canal de YouTube (para "reproduce mi último video").                    |
| `get_url_service` | ⬜          | Motor de extracción: `youtube_dl` (default), `pytube`, `youtubestream`.    |
| `expires`         | ⬜          | Fecha de caducidad de la skill `YYYYMMDD`.                                  |

⭐ = muy recomendada (sin proxy, YouTube bloquea las IPs de AWS).

---

## 🗣️ Uso

| Quieres…                    | Di…                                                      |
|-----------------------------|----------------------------------------------------------|
| Abrir la skill              | "Alexa, abre **\<nombre de invocación\>**"               |
| Reproducir algo             | "…pon **Bohemian Rhapsody**"                              |
| Siguiente / anterior        | "Alexa, **siguiente**" · "Alexa, **canción anterior**"   |
| Pausar / reanudar           | "Alexa, **pausa**" · "Alexa, **reanuda**"                |
| Mezclar                     | "Alexa, **modo aleatorio**"                              |
| Qué está sonando            | "Alexa, **¿qué está sonando?**"                          |
| Detener                     | "Alexa, **para**"                                        |

Los controles de navegación (siguiente, pausa, etc.) son **comandos nativos del AudioPlayer**:
funcionan mientras suena el audio **sin** volver a abrir la skill.

---

## 🛠️ Desarrollo

```bash
# Tras editar lambda_function.py o strings.py, reconstruye el paquete:
python build_package.py

# Y actualiza el Lambda (requiere AWS CLI configurado):
aws lambda update-function-code \
  --function-name TU_FUNCION \
  --zip-file fileb://../alexa_skill.zip \
  --region us-east-1
```

**Estructura del repo** (solo se versiona el código fuente; las dependencias se regeneran):

```
├── lambda_function.py   # Handler principal: routing, búsqueda, extracción, AudioPlayer
├── strings.py           # Cadenas de respuesta multi-idioma
├── requirements.txt     # Dependencias (requests, yt-dlp, fuzzywuzzy, ...)
├── build_package.py     # Instala deps Linux/Py3.10 + arma el .zip de Lambda
├── .env.example         # Plantilla de variables de entorno
└── docs/                # Arquitectura y guía de despliegue
```

---

## 🔒 Seguridad

- **Nunca** subas `cookies.txt`, tu `DEVELOPER_KEY` ni las credenciales del proxy al repo
  (ya están en `.gitignore`). Toda la configuración sensible vive en variables de entorno.
- Si usas cookies de YouTube, hazlo con una **cuenta secundaria**: contienen tokens de sesión.

---

## 🙏 Créditos

Basado en el proyecto open source [**wes1993/YouTubeForAlexa**](https://github.com/wes1993/YouTubeForAlexa).
El truco del cliente `android_vr` para esquivar el candado PO-token está inspirado en
[OpenTune](https://github.com/Arturo254/OpenTune).

## 📄 Licencia

Este proyecto deriva de `wes1993/YouTubeForAlexa`; respeta los términos de licencia del
proyecto original. Revisa la licencia upstream antes de redistribuir.
