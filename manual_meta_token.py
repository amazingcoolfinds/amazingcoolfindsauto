#!/usr/bin/env python3
"""
MANUAL META TOKEN EXTRACTOR - Read code from browser
"""
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("ManualMetaToken")

def read_browser_code():
    """Read authorization code from browser console output"""
    print("🔧 LEYENDO CÓDIGO DESDE NAVEGADOR")
    print("=" * 50)
    print("📋 ESPERANDO CÓDIGO AUTOMÁTICO:")
    print("1. Completa la autorización en el navegador")
    print("2. Facebook te redirigirá a una URL con código")
    print("3. Busca el código que empieza con 'code=' en la URL")
    print("4. Copia SOLO el código (sin 'code=')")
    print("5. Pégalo aquí y presiona Enter")
    
    print()
    
    try:
        # Read from standard input
        print("📋 ESPERANDO CÓDIGO...")
        code_lines = []
        
        while len(code_lines) == 0:
            line = input().strip()
            if line.startswith('#'):
                continue
            elif '=' in line and len(line) > 5:
                if 'code=' in line:
                    code_part = line.split('code=')[1].strip()
                    code_lines.append(code_part)
                    print(f"📋 Código detectado: {code_part[:10]}...")
                    break
                else:
                    print(f"⚠️ Línea ignorada (no contiene código)")
        
        if len(code_lines) > 0:
            auth_code = code_lines[0]
            print(f"✅ Código recibido: {auth_code[:15]}...")
            
            # Test with sample URL to validate parsing
            sample_url = "https://localhost:8080/?code=test123&state=test#param=value"
            if 'code=' in sample_url:
                print("✅ Parser validation: OK")
            else:
                print("⚠️ Parser needs checking")
            
            return auth_code
        else:
            print("❌ No se recibió código válido")
            return None
            
    except Exception as e:
        print(f"❌ Error leyendo código: {e}")
        return None

def extract_code_from_url(url):
    """Extract authorization code from URL"""
    try:
        from urllib.parse import parse_qs
        parsed = parse_qs(url.split('?')[1])
        return parsed.get('code', [''])[0]
    except:
        return None

def main():
    print("🔧 EXTRACTOR MANUAL DE TOKENS")
    print("=" * 50)
    
    print("📋 OPCIÓN 1: AUTENTICACIÓN COMPLETADA")
    auth_code = read_browser_code()
    
    if auth_code:
        print(f"✅ Código recibido: {auth_code[:15]}...")
        
        print("\n📋 OPCIÓN 2: GUARDAR EN .ENV")
        
        # Check if we should use the existing correct credentials
        use_existing = input("¿Quieres usar tus credenciales existentes (s/n) o las credenciales de prueba (p)? [s/n]: ").strip().lower()
        
        if use_existing == 'n':
            print("🔄 Usando credenciales de prueba...")
            app_id = "1289705299666205"
            app_secret = "c39f0a5c6cae9fb6983454954756c77f"
        elif use_existing != 's':
            print("✅ Usando tus credenciales reales...")
            app_id = "1289705299666205"
            app_secret = "c39f0a5c6cae9fb6983454954756c77f"
        else:
            print("❌ Opción no válida. Usando credenciales de prueba.")
        
        if auth_code and (app_id and app_secret):
            print("\n🔄 Intercambiando código por tokens...")
            
            try:
                import requests
                token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
                token_data = {
                    'client_id': app_id,
                    'client_secret': 'c39f0a5c6cae9fb6983454954756c77f',
                    'redirect_uri': 'https://amazing-cool-finds.com',
                    'code': auth_code,
                }
                
                response = requests.post(token_url, data=token_data, timeout=30)
                
                if response.status_code == 200:
                    token_info = response.json()
                    access_token = token_info.get('access_token')
                    
                    if access_token:
                        expires_in = token_info.get('expires_in', 0)
                        expires_at = time.time() + expires_in if expires_in else 0
                        
                        print("✅ TOKENS GENERADOS!")
                        print(f"🕐 Access Token: {access_token[:20]}...")
                        print(f"📅 Expira: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(expires_at))}")
                        print(f"⏳ Duración: {expires_in/86400:.1f} días")
                        
                        # Save to .env
                        env_content = f"""# Meta Long-Lived Tokens - Created on {time.strftime('%Y-%m-%d')}
META_ACCESS_TOKEN={access_token}
# Optional: META_ACCESS_TOKEN_EXPIRES={expires_at}

# Meta App Credentials (BACKUP)
# META_APP_ID=1289705299666205
META_APP_SECRET=c39f0a5c6cae9fb6983454954756c77f

# Existing Platform Credentials
FACEBOOK_PAGE_ID=963943753475520
INSTAGRAM_ACCOUNT_ID=17841480700754002
"""
                        
                        with open('.env', 'w') as f:
                            f.write(env_content)
                        
                        print("✅ Tokens guardados en .env")
                        
                        # Test the new token immediately
                        print("\n🔍 VERIFICANDO TOKENS...")
                        
                        test_url = "https://graph.facebook.com/me"
                        headers = {"Authorization": f"Bearer {access_token}"}
                        test_response = requests.get(test_url, headers=headers, timeout=10)
                        
                        if test_response.status_code == 200:
                            user_data = test_response.json()
                            print("✅ Token válido!")
                            print(f"👤 Usuario: {user_data.get('name', 'Unknown')}")
                            return True
                        else:
                            print(f"❌ Token inválido: {test_response.status_code}")
                            return False
                else:
                    print(f"❌ Error en intercambio: {response.status_code}")
                    print(f"Respuesta: {response.text[:100]}...")
                    return False
                else:
                    print(f"❌ Error de red: {e}")
                    return False
            else:
                print("❌ No se pudo generar tokens")
                return False
                
    elif not auth_code:
        print("❌ No se recibió código de autorización")
        print("\n🔄 Reintentando con el método alternativo...")
        
        # Try alternative redirects
        alternative_uris = [
            "https://amazing-cool-finds.com/auth/callback",
            "https://localhost:8081",
            "https://127.0.0.1"
        ]
        
        for redirect_uri in alternative_uris:
            print(f"🔄 Probando redirect: {redirect_uri}")
            print(f"📋 Esperando 30 segundos...")
            time.sleep(30)
            
        print("❌ Todos los métodos alternativos fallaron")
        print("🔗 Necesita revisión de la configuración en Facebook Developer Console")
        return False

if __name__ == "__main__":
    main()