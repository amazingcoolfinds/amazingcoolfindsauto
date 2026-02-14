#!/bin/bash
# 🚀 Script de despliegue ultrarrápido a Cloudflare Pages

# Configuración
PROJECT_DIR="/Users/zoomies/Desktop/liveitupdeals"
AMAZING_DIR="$PROJECT_DIR/amazing"
PROJECT_NAME="amazing-cool-finds" # Corrected name with hyphens

echo "📦 Iniciando despliegue de Amazing Cool Finds..."

# Entrar al directorio de la web
cd "$AMAZING_DIR" || exit

# Verificar si wrangler está instalado
if ! command -v npx &> /dev/null
then
    echo "❌ Error: npx no está instalado."
    exit 1
fi

# Desplegar
echo "☁️ Subiendo archivos a Cloudflare..."
npx wrangler pages deploy . --project-name "$PROJECT_NAME"

if [ $? -eq 0 ]; then
    echo "✅ ¡Despliegue completado con éxito!"
else
    echo "❌ Error durante el despliegue."
    exit 1
fi
