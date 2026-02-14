#!/usr/bin/env python3
"""
META DOMAIN HELPER - Step-by-step guide for Facebook Developer Console
"""
import webbrowser
import time

def open_facebook_developer_console():
    """Open Facebook Developer Console at the right place"""
    print("🔧 FACEBOOK DEVELOPER CONSOLE - AYUDA CON DOMINIOS")
    print("=" * 60)
    
    # Step 1: Open Developer Console
    print("🌐 PASO 1: Abriendo Facebook Developer Console...")
    dev_url = "https://developers.facebook.com/"
    
    try:
        webbrowser.open(dev_url)
        print("✅ Navegador abierto: https://developers.facebook.com/")
        time.sleep(2)
    except:
        print("⚠️  Por favor, abre manualmente: https://developers.facebook.com/")
    
    print("\n" + "=" * 60)
    
    # Step 2: Find your app
    print("📱 PASO 2: Busca tu aplicación")
    print("   1. En 'My Apps', busca: 'Amazing Cool Finds - Pipeline'")
    print("   2. Si no existe, créala con:")
    print("      - Nombre: Amazing Cool Finds - Pipeline")
    print("      - ID: amazing-cool-finds-pipeline")
    print("      - Tipo: Business")
    print("      - Categoría: Business")
    
    print("\n⏳ Espera 5 segundos para que abras la aplicación...")
    time.sleep(5)
    
    # Step 3: Configure domains
    print("\n🔧 PASO 3: Configurar dominios")
    print("   1. Dentro de tu app, ve a 'Settings' → 'Basic'")
    print("   2. En 'App Domains', agrega:")
    print("      - amazing-cool-finds.com")
    print("      - localhost:8080")
    print("      - [Opcional] 127.0.0.1 (para desarrollo)")
    print("   3. Guarda los cambios")
    
    print("\n⏳ Espera 3 segundos para guardar configuración...")
    time.sleep(3)
    
    # Step 4: OAuth settings
    print("\n🔑 PASO 4: Configurar OAuth")
    print("   1. Ve a 'Products' → 'Facebook Login'")
    print("   2. En 'Settings', configura:")
    print("      - Valid OAuth Redirect URIs:")
    print("      - amazing-cool-finds.com") 
    print("      - https://amazing-cool-finds.com/auth/callback")
    print("      - localhost:8080")
    print("      - https://localhost:8080/auth")
    print("   3. Asegúrate de que 'Client OAuth Login Flow' esté habilitado")
    print("   4. Guarda los cambios")
    
    print("\n⏳ Esperando configuración...")
    time.sleep(3)
    
    # Step 5: Add products
    print("\n📦 PASO 5: Agregar productos a la API")
    print("   1. Ve a 'Products' → 'Facebook Login' → 'Settings'")
    print("   2. En 'App Review', agrega:")
    print("      - Pages API")
    print("      - Instagram Basic Display API")
    print("      - Instagram Graph API")
    print("      - Instagram Shopping Tag Product Catalog Management")
    print("   3. En 'App Details', agrega:")
    print("      - App URL: https://amazing-cool-finds.com")
    print("      - Privacy Policy URL: https://amazing-cool-finds.com/privacy")
    print("      - User Data Deletion URL: https://amazing-cool-finds.com/delete")
    print("   4. Envía para revisión")
    print("   5. Espera aprobación (puede tardar)")
    
    print("\n📋 LISTA DE VERIFICACIÓN FINAL:")
    print("   ✅ App ID: amazing-cool-finds-pipeline")
    print("   ✅ Dominios: amazing-cool-finds.com + localhost:8080")
    print("   ✅ OAuth Configurado")
    print("   ✅ Products de API agregados")
    print("   ✅ URLs de privacidad configuradas")
    
    print("\n🎯 PRÓXIMO PASO: Generar tokens")
    print("   1. Una vez aprobada, genera tokens con:")
    print("      python meta_token_generator.py --create")
    print("   2. O usa: python manual_meta_token.py")
    print("      - Pega el código de autorización")
    print("      - Los tokens se guardarán automáticamente")
    
    print("\n" + "=" * 60)
    print("📱 ESTADO ACTUAL:")
    print("✅ Facebook Developer Console: ABIERTA")
    print("✅ Guía paso a paso: MOSTRADA")
    print("✅ Lista de configuración: PREPARADA")
    
    print("\n🔄 Volviendo a abrir la consola en 10 segundos...")
    print("📋 Puedes cerrar esta ventana cuando termines")
    print("📋 La consola permanecerá abierta")
    
    # Keep browser open
    time.sleep(10)
    print("🌐 Reabriendo Facebook Developer Console...")
    try:
        webbrowser.open(dev_url)
        print("✅ Facebook Developer Console abierto de nuevo")
        print("📋 Sigue las instrucciones de arriba")
        print("📋 Esta ventana se cerrará en 30 segundos")
        time.sleep(30)
        print("✅ Ejecución completada")
        
    except KeyboardInterrupt:
        print("\n👤 Ejecución cancelada por el usuario")
    
    print("\n🎯 RESUMEN PARA TUS NOTAS:")
    print("1. Configura dominios en App Domains")
    print("2. Configura OAuth en Facebook Login")
    print("3. Agrega productos de API")
    print("4. Envía para revisión")
    print("5. Una vez aprobado, genera tokens")

if __name__ == "__main__":
    open_facebook_developer_console()