# Arquitectura

## Flujo de una petición

1. **Voz → Alexa**: el usuario habla; el Alexa Skills Kit (ASK) reconoce el intent y envía
   un evento JSON al Lambda (`lambda_handler`).
2. **Routing** (`lambda_function.py`):
   - `LaunchRequest` → `get_welcome_response`.
   - `IntentRequest` → `on_intent` despacha al handler del intent.
   - `AudioPlayer.*` → `handle_playback` (encola la siguiente pista, etc.).
3. **Búsqueda** (`search` → `video_search`): consulta la **YouTube Data API v3** con
   `DEVELOPER_KEY` y re-rankea los resultados para preferir una canción individual.
4. **Extracción** (`get_url_and_title_youtube_dl`): yt-dlp obtiene la URL de audio directa
   (`m4a`) usando el cliente `android_vr` a través de un proxy.
5. **Respuesta**: el Lambda devuelve una directiva `AudioPlayer.Play` con la URL; el **Echo
   descarga el audio directamente** desde `googlevideo.com` (no pasa por el Lambda ni el proxy).

## Decisiones de diseño clave

### Por qué un proxy
Las IPs de los datacenters de AWS están bloqueadas por YouTube ("Sign in to confirm you're not
a bot"). Un proxy datacenter (Webshare) hace la **extracción** (unos KB). La URL resultante de
`googlevideo` se reproduce desde cualquier IP, así que el audio lo baja el Echo directo.

### Por qué el cliente `android_vr`
YouTube protege los streams con **PO-token / SABR**: con los clientes `ios`/`android` el stream
se corta a ~1 MB (≈2 min) con HTTP 403, desde cualquier IP. El cliente **`android_vr`** (InnerTube
de Oculus Quest, `clientId 28`) devuelve URLs **sin** ese candado, y el `m4a` se reproduce completo
por rangos HTTP. Idea tomada de [OpenTune](https://github.com/Arturo254/OpenTune).

### Selección de canción (anti-compilación)
`video_search` re-rankea los resultados de la API con `_song_rank`:
- **Penaliza** títulos que parecen compilación/mix/álbum largo (regex con límites de palabra,
  para no afectar "remix"/"mixed").
- **Premia** canales `Artista - Topic` (audio individual oficial autogenerado por YouTube) y
  títulos con "official audio/video".
- Orden **estable**: en empates conserva la relevancia original de YouTube.
- Solo aplica a búsquedas por texto (no a "más como esta" ni búsqueda por canal).

### Selección de formato de audio
`pick_url` elige el mejor `m4a` por bitrate (`abr`): itag **140** (AAC-LC 128 kbps) sobre el
itag 139 (HE-AAC 48 kbps). AAC/m4a es el formato que mejor reproduce el AudioPlayer de Alexa.

## Componentes

| Archivo              | Rol                                                                    |
|----------------------|------------------------------------------------------------------------|
| `lambda_function.py` | Handler, routing de intents, búsqueda, extracción, lógica de AudioPlayer. |
| `strings.py`         | Cadenas de respuesta por idioma (`strings_es`, `strings_en`, ...).     |
| `requirements.txt`   | Dependencias de runtime.                                               |
| `build_package.py`   | Instala dependencias Linux/Py3.10 y arma el `.zip`.                    |

## Restricciones del entorno

- **Lambda**: paquete ≤ 250 MB descomprimido. Por eso se quitó `pytubefix` (arrastraba ~200 MB
  de `nodejs_wheel`); el fallback es `pytube` ligero.
- **AudioPlayer**: la respuesta del Lambda debe llegar en pocos segundos; el cliente `android_vr`
  también reduce la latencia inicial.
- **Dependencias en C** (rapidfuzz/Levenshtein): deben ser wheels `manylinux2014_x86_64` cp310.
