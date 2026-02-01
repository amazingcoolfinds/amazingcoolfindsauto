# 🚀 Guía de Deployment - LivItUpDeals

Esta guía te ayudará a subir tu proyecto a hosting paso a paso.

---

## 📋 Prerequisitos

Antes de comenzar, asegúrate de tener:
- [x] Cuenta de hosting (Bluehost, GoDaddy, HostGator, etc.)
- [x] Dominio configurado (ej: liveitupdeals.com)
- [x] Acceso FTP/SFTP o panel de control (cPanel)
- [x] API Keys de Amazon y Gemini configuradas

---

## 🎯 Arquitectura de Deployment

Tu proyecto tiene **dos componentes**:

### 1. **Frontend (Landing Page)** 
- Archivo: `index.html`
- Va en: `/public_html/` o `/www/` de tu hosting
- **NO requiere Python** - funciona en cualquier hosting

### 2. **Backend (Pipeline Python)**
- Archivo: `pipeline.py` + dependencias
- **REQUIERE** hosting con Python o ejecución local
- Genera el archivo `data/products.json` que usa la landing page

---

## 🌐 Opción 1: Hosting Compartido SIN Python

**Situación:** Tu hosting NO soporta Python (hosting básico, solo HTML/PHP)

### Solución: Pipeline Local + Upload Manual

1. **Ejecuta el pipeline en tu computadora:**
   ```bash
   cd ~/Desktop/liveitupdeals
   python pipeline.py --update-website
   ```
   Esto genera `data/products.json`

2. **Sube archivos a tu hosting vía FTP:**
   - Usa FileZilla, Cyberduck o el File Manager de cPanel
   - **Sube estos archivos:**
     ```
     public_html/
     ├── index.html          ← Landing page
     └── data/
         └── products.json   ← Datos de productos
     ```

3. **Automatiza con script de deployment:**
   ```bash
   # Edita deploy.sh con tus credenciales FTP
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **Configura ejecución diaria en tu Mac:**
   ```bash
   # Edita crontab local
   crontab -e
   
   # Agrega esta línea (ejecuta a las 9 AM diariamente):
   0 9 * * * cd ~/Desktop/liveitupdeals && python pipeline.py --update-website && ./deploy.sh
   ```

### ✅ Ventajas
- Funciona en cualquier hosting barato ($3-10/mes)
- Sin configuración compleja en servidor

### ⚠️ Desventajas
- Tu computadora debe estar encendida para actualizaciones diarias
- Requiere upload manual o automatizado desde local

---

## 🖥️ Opción 2: Hosting con Python (VPS o Hosting Avanzado)

**Situación:** Tienes acceso SSH y Python en tu servidor

### Paso 1: Conectar por SSH
```bash
ssh tu_usuario@tu_dominio.com
# O usa PuTTY en Windows
```

### Paso 2: Verificar Python
```bash
python3 --version
# Debe ser Python 3.8 o superior
```

### Paso 3: Subir Archivos al Servidor
```bash
# Desde tu computadora local:
scp -r ~/Desktop/liveitupdeals tu_usuario@tu_dominio.com:~/
```

### Paso 4: Instalar Dependencias en el Servidor
```bash
# Ya en el servidor (SSH):
cd ~/liveitupdeals
pip3 install -r requirements.txt --user
```

### Paso 5: Configurar Variables de Entorno
```bash
# Crea tu archivo .env en el servidor:
nano .env

# Pega tus API keys (igual que .env.example):
AMAZON_ACCESS_KEY=tu_key_aqui
AMAZON_SECRET_KEY=tu_secret_aqui
AMAZON_ASSOCIATE_TAG=tu_tag-20
GEMINI_API_KEY=tu_gemini_key
DATA_DIR=/home/tu_usuario/public_html/data

# Guarda con Ctrl+O, Enter, Ctrl+X
```

### Paso 6: Crear Directorio para Website
```bash
mkdir -p ~/public_html/data
```

### Paso 7: Copiar Landing Page
```bash
cp ~/liveitupdeals/index.html ~/public_html/
```

### Paso 8: Probar el Pipeline
```bash
cd ~/liveitupdeals
python3 pipeline.py --setup     # Verificar configuración
python3 pipeline.py --update-website  # Generar productos
```

### Paso 9: Configurar Cron Job (Ejecución Diaria)
```bash
crontab -e

# Agrega esta línea (ejecuta diariamente a las 9 AM):
0 9 * * * cd ~/liveitupdeals && /usr/bin/python3 pipeline.py --update-website >> ~/logs/pipeline_cron.log 2>&1
```

### ✅ Ventajas
- Totalmente automatizado
- Servidor ejecuta pipeline 24/7
- No depende de tu computadora local

### ⚠️ Requisitos
- Hosting con acceso SSH (VPS, DigitalOcean, Linode, etc.)
- Costo: $5-20/mes típicamente

---

## 📱 Configuración Específica: Bluehost

### Si tienes Bluehost Básico (sin Python):
→ Usa **Opción 1** (Pipeline Local)

### Si tienes Bluehost VPS o Dedicated:

1. **Acceso SSH:**
   - Activa SSH desde cPanel → SSH Access
   - Conecta: `ssh tu_usuario@tu_dominio.com`

2. **Instalar Python 3.8+ (si no está):**
   ```bash
   # Verificar versión
   python3 --version
   
   # Si es menor a 3.8, contacta soporte de Bluehost
   # O usa Python Environment de cPanel
   ```

3. **Ruta de public_html:**
   ```bash
   # Tu landing page va en:
   /home/tu_usuario/public_html/index.html
   /home/tu_usuario/public_html/data/products.json
   ```

4. **Configurar DATA_DIR en .env:**
   ```bash
   DATA_DIR=/home/tu_usuario/public_html/data
   ```

---

## 🔧 Troubleshooting Común

### Problema: "Permission denied" al ejecutar pipeline
**Solución:**
```bash
chmod +x pipeline.py
```

### Problema: "Module not found" en servidor
**Solución:**
```bash
# Instala con --user si no tienes permisos de root
pip3 install -r requirements.txt --user

# O crea un virtual environment:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Problema: products.json no se actualiza en website
**Solución:**
```bash
# Verifica que DATA_DIR apunte a public_html:
echo $DATA_DIR  # En .env

# Verifica permisos:
ls -la ~/public_html/data/
chmod 755 ~/public_html/data
```

### Problema: Cron job no ejecuta
**Solución:**
```bash
# Verifica logs de cron:
grep CRON /var/log/syslog  # Linux
tail -f ~/logs/pipeline_cron.log  # Tu log

# Usa rutas ABSOLUTAS en crontab:
0 9 * * * /usr/bin/python3 /home/tu_usuario/liveitupdeals/pipeline.py --update-website
```

---

## ✅ Checklist de Verificación Post-Deployment

- [ ] Acceder a `http://tu_dominio.com` - landing page carga
- [ ] Verificar que productos se muestran (no demo data)
- [ ] Links de afiliados funcionan (redirigen a Amazon)
- [ ] `data/products.json` existe y tiene productos reales
- [ ] Cron job configurado (esperar 24hrs para confirmar)
- [ ] Logs no muestran errores críticos

---

## 📊 Monitoreo Post-Deployment

### Ver logs del pipeline:
```bash
tail -f ~/liveitupdeals/logs/pipeline.log
```

### Verificar última actualización:
```bash
ls -lh ~/public_html/data/products.json
# Verifica timestamp de última modificación
```

### Test manual desde servidor:
```bash
cd ~/liveitupdeals
python3 pipeline.py --update-website
```

---

## 🎯 Próximos Pasos (Opcional)

1. **Analytics:** Agrega Google Analytics a `index.html`
2. **SEO:** Mejora meta tags para posicionamiento
3. **Videos:** Implementa generación automática de videos con FFmpeg
4. **YouTube:** Configura upload automático a YouTube Shorts
5. **CDN:** Usa Cloudflare para acelerar carga de página

---

## 🆘 Soporte

Si encuentras problemas:
1. Revisa logs: `~/liveitupdeals/logs/pipeline.log`
2. Ejecuta validación: `python3 pipeline.py --setup`
3. Verifica que todas las API keys sean correctas en `.env`

---

**¡Listo! 🎉** Tu sitio debería estar funcionando en `http://tu_dominio.com`
