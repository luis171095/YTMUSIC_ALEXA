# Guía de despliegue

Pasos completos para poner la skill en producción en tu propio Echo.

## 1. Requisitos previos

- Cuenta de [AWS](https://aws.amazon.com/) y de [Amazon Developer](https://developer.amazon.com/).
- API key de **YouTube Data API v3** desde [Google Cloud Console](https://console.cloud.google.com):
  crea un proyecto → habilita "YouTube Data API v3" → Credenciales → API key.
- (Recomendado) Un proxy datacenter. El tier gratuito de [Webshare](https://www.webshare.io/)
  da 10 proxies; YouTube no los bloquea como a las IPs de AWS.
- Python 3.10+ y `pip` local para empaquetar.

## 2. Empaquetar

```bash
git clone https://github.com/luis171095/YTMUSIC_ALEXA.git
cd YTMUSIC_ALEXA
python build_package.py --install
```

Genera `../alexa_skill.zip` (un nivel arriba del repo) con el código + dependencias Linux/Py3.10.

> Si ves errores de `ImportError` o `typing_extensions` en CloudWatch, casi siempre es porque
> las dependencias se instalaron para tu PC en vez de para Linux. `build_package.py --install`
> usa los flags correctos (`--platform manylinux2014_x86_64 --python-version 3.10`).

## 3. Crear la función Lambda

1. AWS Console → **Lambda** → *Create function* → *Author from scratch*.
2. Runtime **Python 3.10**, arquitectura **x86_64**.
3. *Code* → *Upload from* → *.zip file* → sube `alexa_skill.zip`.
4. *Runtime settings* → Handler = `lambda_function.lambda_handler`.
5. *Configuration → General* → Timeout ≥ **15 s**, Memory ≥ **512 MB**.
6. *Configuration → Environment variables* → añade las de [`.env.example`](../.env.example):
   - `DEVELOPER_KEY`, `proxy`, `proxy_enabled=true`.
7. *Configuration → Triggers* → *Add trigger* → **Alexa Skills Kit** → pega el Skill ID.

## 4. Crear la skill en Alexa

1. [Alexa Developer Console](https://developer.amazon.com/alexa/console/ask) → *Create Skill*.
2. Modelo **Custom**, hosting **Provision your own**.
3. **Invocation name**: elige algo poco genérico (evita "música"; Alexa+ desvía nombres comunes).
4. Define los **intents** (`SearchIntent` con slot `query`, `PlaylistIntent`, `ChannelIntent`, etc.).
5. `Build → Interfaces → Audio Player` → **ON** → *Save* → *Build Model*.  ← imprescindible.
6. `Endpoint` → **AWS Lambda ARN** → pega el ARN de tu función → *Save*.
7. Copia el **Skill ID** y pégalo en el trigger del Lambda (paso 3.7).

## 5. Probar

- Echo real: "Alexa, abre **\<tu nombre de invocación\>**" → "pon Mozart".
- Revisa los logs en **CloudWatch** → `/aws/lambda/TU_FUNCION`. Busca:
  - `yt-dlp OK con player_client=android_vr`
  - `audio m4a: 140`  (mejor calidad AAC-LC 128 kbps)

## 6. Actualizar tras cambios de código

```bash
python build_package.py
aws lambda update-function-code \
  --function-name TU_FUNCION \
  --zip-file fileb://../alexa_skill.zip \
  --region us-east-1
```

O, manualmente: Lambda → *Code* → *Upload from* → *.zip file*.

## Resolución de problemas

| Síntoma                                          | Causa probable / solución                                              |
|--------------------------------------------------|------------------------------------------------------------------------|
| "Hubo un problema con la respuesta de la Skill"  | Falta activar la interfaz **AudioPlayer** + rebuild del modelo.        |
| Suena pero se **corta a ~2 min**                 | El cliente no es `android_vr` (PO-token/SABR). Revisa `player_clients`.|
| `Requested format is not available`              | Añade `missing_pot` (ya incluido) o el video no está disponible.       |
| Reproduce una **compilación** larga              | Resuelto por el re-ranking de búsqueda; revisa el `videoId` en logs.   |
| `ImportError` al iniciar                         | Dependencias mal compiladas → reempaqueta con `--install`.            |
| El proxy free cae / rota                         | Prueba otra IP de tu lista de Webshare en la var `proxy`.             |
