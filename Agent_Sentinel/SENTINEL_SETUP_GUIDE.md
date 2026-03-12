Sigue estos pasos para activar a **Sentinel** y poder hablar con él directamente por Telegram o por los Issues de GitHub.

## Opción A: Sentinel vive en GitHub (Gratis y sin Servidor) 🐙
Esta es la opción más sencilla si quieres que Sentinel viva 100% en GitHub.
1. Ve a la pestaña **Issues** de tu repositorio.
2. Crea un nuevo Issue o comenta en uno existente.
3. Empieza tu comentario con **"Sentinel,"** o etiqueta a **"@sentinel"**.
   - Ejemplo: *"Sentinel, dime cómo fue el pipeline de hoy"*
4. GitHub Actions se activará automáticamente y Sentinel te responderá en unos segundos como un comentario.
   - **Nota**: Asegúrate de que el secreto `NVIDIA_API_KEY` esté configurado en `Settings > Secrets and variables > Actions`.

## Opción B: Sentinel en Telegram (24/7 con Servidor) 🤖📱
Si prefieres Telegram por comodidad, sigue estos pasos:
1. Abre tu terminal de OpenClaw o accede a tu servidor.
2. Ejecuta el comando de configuración:
   ```bash
   openclaw onboard
   ```
3. Selecciona **Telegram** como canal de comunicación cuando te lo pregunte.
4. Pega el **API Token** que copiaste de BotFather.
5. (Opcional) Si OpenClaw te pide tu `User ID` de Telegram para mayor seguridad, puedes obtenerlo usando el bot `@userinfobot`.

## Paso 3: Cargar las Instrucciones de Sentinel
Ahora debemos darle su "personalidad" y conocimientos técnicos:
1. Ve a la configuración de tu agente en el dashboard de OpenClaw.
2. Busca la sección de **System Prompt** o **Instrucciones**.
3. Copia TODO el contenido del archivo que creamos: [openclaw_instructions.md](file:///Users/zoomies/Desktop/liveitupdeals/openclaw_instructions.md) y pégalo allí.
4. Asegúrate de que la configuración del modelo esté apuntando a tu API de NVIDIA (Kimi k2.5).

## Paso 4: Emparejar y Probar
1. Busca el nombre de tu nuevo bot en Telegram (el que creaste en el Paso 1).
2. Haz clic en **Iniciar** o envía `/start`.
3. OpenClaw te pedirá un código de emparejamiento (pairing code) en la consola o te enviará instrucciones.
4. Una vez emparejado, ¡intenta hablarle!
   - Dile: *"Sentinel, ¿estás activo?"*
   - O pregúntale: *"Sentinel, ¿cómo fue el pipeline de hoy?"*

## Troubleshooting
- **No responde**: Verifica que el servicio de OpenClaw esté corriendo (`openclaw start`).
- **Error de API**: Asegúrate de que la `NVIDIA_API_KEY` esté bien puesta en tus secretos de GitHub o en el archivo `.env` del servidor donde corras el pipeline.

## IMPORTANTE: ¿Sentinel duerme si apago mi laptop? 😴
- **Ejecución Local**: Si corres `openclaw start` en tu laptop, **sí**, Sentinel se apagará cuando cierres la tapa o apagues la computadora.
- **Ejecución 24/7 (Recomendado)**: Para que Sentinel esté siempre despierto y te responda por Telegram en cualquier momento, lo ideal es instalar OpenClaw en un pequeño servidor (VPS) como **Amazon Lightsail**, **DigitalOcean** o incluso una **Raspberry Pi** que siempre esté encendida.
- **El Pipeline**: Tu pipeline de GitHub Actions seguirá funcionando automáticamente cada 12h aunque tu laptop esté apagada.
- **Sentinel en GitHub Issues**: Esta versión de Sentinel **siempre funciona** (vive en GitHub) sin que tengas que pagar nada ni dejar tu laptop encendida.
- **Sentinel en Telegram**: Para esta versión, sí necesitas el servidor encendido.
