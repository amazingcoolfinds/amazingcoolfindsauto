#!/usr/bin/env python3
"""
CORRECTED META TOKEN GENERATOR - With HTTPS redirect
"""
import os
import json
import time
import logging
import requests
import webbrowser
from urllib.parse import urlencode, parse_qs

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("CorrectedMetaTokenGen")

def generate_meta_tokens():
    """Generate Meta long-lived tokens using HTTPS redirect"""
    print("🎯 META TOKENS DE LARGA DURACIÓN - CORREGIDO")
    print("=" * 60)
    
    # Your actual credentials
    app_id = "1289705299666205"
    app_secret = "c39f0a5c6cae9fb6983454954756c77f"
    
    # CORRECTED redirect URI - HTTPS + HTTPS fallback
    redirect_uris = [
        "https://amazing-cool-finds.com/auth/callback",
        "https://localhost:8080",
        "https://127.0.0.1:8080",
        "https://0.0.0.0:8080"
    ]
    primary_redirect = redirect_uris[0]  # HTTPS external redirect
    
    # Long-lived permissions (corrected case)
    scopes = [
        "pages_show_list",
        "pages_read_engagement",
        "pages_read_engagement", 
        "pages_manage_posts",
        "pages_manage_engagement",
        "instagram_basic", 
        "instagram_content_publish",
        "instagram_manage_insights",
        "instagram_shopping_tag_product_catalog_management",
        "pages_read_user_content",
        "pages_read_user_posts",
        "pages_show_lists",
        "business_management",
        "instagram_manage_comments"
    ]
    
    # Generate authorization URL with HTTPS redirect
    auth_params = {
        'client_id': app_id,
        'redirect_uri': primary_redirect,
        'scope': ' '.join(scopes),
        'response_type': 'code',
        'access_type': 'offline',
        'state': 'pipeline_auth_' + str(int(time.time()))
    }
    
    auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(auth_params)}"
    
    print(f"🌐 ABIENDO NAVEGADOR...")
    print(f"📋 Redirect Principal: {primary_redirect}")
    print(f"🔑 Permisos: {len(scopes)} (long-lived)")
    print(f"📅 Fallback redirects: {redirect_uris[1:]}")
    print()
    
    # Open browser
    try:
        webbrowser.open(auth_url)
        print("✅ Navegador abierto automáticamente")
    except:
        print("⚠️  Por favor, abre manualmente la URL de arriba")
    
    print()
    print("🔑 INSTRUCCIONES SIMPLIFICADAS:")
    print("=" * 50)
    print("1. Inicia sesión en Facebook")
    print("2. Acepta todos los permisos solicitados")
    print("3. Serás redirigido (puede mostrar error - es normal)")
    print("4. Copia el código de la URL")
    print("5. Pega el código aquí:")
    print()
    
    # Wait for manual code input with timeout protection
    print("⏳ Esperando 30 segundos o ingresa manualmente...")
    
    import sys
    
            import sys
    if __name__ == "__main__":
        parser = argparse.ArgumentParser(description="Corrected Meta Token Generator")
        parser.add_argument("--create", action="store_true", help="Generate new long-lived tokens")
        parser.add_argument("--test", action="store_true", help="Test current tokens")
        parser.add_argument("--alt", action="store_true", help="Try alternative redirect methods")
        
        args = parser.parse_args()
            if auth_code and len(auth_code) > 10:
                break
        time.sleep(0.1)
    
    auth_code = auth_code.strip() if auth_code else None
    
    if not auth_code:
        print("❌ No se proporcionó código de autorización")
        print("\n🔄 OPCIÓN: Intentar con el método alternativo...")
        return try_alternative()
    
    print(f"🔄 Procesando código: {auth_code[:10]}...")
    
    try:
        token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
        token_data = {
            'client_id': app_id,
            'client_secret': app_secret,
            'redirect_uri': primary_redirect,
            'code': auth_code
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
                print(f"📅 Expira en: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(expires_at))}")
                print(f"⏳ Duración: {expires_in/86400:.1f} días")
                
                # Save to .env with backup
                backup_env_content = f"""
# Backup original - {time.strftime('%Y-%m-%d %H:%M:%S')}
# OLD META_ACCESS_TOKEN={os.getenv('META_ACCESS_TOKEN', '')}
"""
                
                env_content = f"""# Meta Long-Lived Tokens - Created on {time.strftime('%Y-%m-%d')}
META_ACCESS_TOKEN={access_token}
# Optional: META_ACCESS_TOKEN_EXPIRES={expires_at}

# Meta App Credentials (BACKUP)
# META_APP_ID=1289705299666205
# META_APP_SECRET=c39f0a5c6cae9fb6983454954756c77f

# Existing Platform Credentials
FACEBOOK_PAGE_ID=963943753475520
INSTAGRAM_ACCOUNT_ID=17841480700754002

# Enhanced Links Configuration
WEBSITE_URL=https://amazing-cool-finds.com
"""
                
                # Write main env file
                with open('.env', 'w') as f:
                    f.write(env_content)
                
                # Keep backup
                with open('.env.backup', 'w') as f:
                    f.write(backup_env_content)
                
                print("✅ Tokens guardados en .env")
                print("📂 Backup guardado en .env.backup")
                print("🎯 META TOKENS LISTOS!")
                
                return test_token(access_token)
            else:
                print("❌ No access token en respuesta")
                return False
        else:
            print(f"❌ Error intercambiando código: {response.status_code}")
            print(f"Respuesta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_token(access_token):
    """Test if token is valid"""
    try:
        test_url = "https://graph.facebook.com/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ Token válido")
            print(f"👤 Usuario: {user_data.get('name', 'Unknown')}")
            print(f"📧 Permisos: {len(user_data.get('permissions', []))}")
            
            # Check if we have Instagram permissions
            permissions = user_data.get('permissions', [])
            instagram_perms = [p for p in permissions if 'instagram' in p.lower()]
            
            if len(instagram_perms) > 5:
                print(f"✅ Permisos Instagram: {len(instagram_perms)}")
                print("✅ LISTO PARA INSTAGRAM!")
                return 'instagram_ready'
            else:
                print("⚠️  Permisos Instagram insuficientes")
                return 'instagram_insufficient'
        else:
            print(f"❌ Token inválido: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing token: {e}")
        return False

def try_alternative():
    """Try alternative redirect methods"""
    print("🔄 Intentando con redirects alternativos...")
    
    redirect_uris = [
        "https://amazing-cool-finds.com/auth/callback",
        "https://localhost:8081",
        "https://127.0.0.1:8081"
    ]
    
    for redirect_uri in redirect_uris:
        print(f"🌐 Intentando con: {redirect_uri}")
        
        auth_params = {
            'client_id': "1289705299666205",
            'client_secret': "c39f0a5c6cae9fb6983454954756c77f",
            'redirect_uri': redirect_uri,
            'scope': 'pages_show_list pages_read_engagement pages_read_engagement pages_manage_posts pages_manage_engagement instagram_basic instagram_content_publish instagram_manage_insights instagram_shopping_tag_product_catalog_management pages_read_user_content pages_read_user_posts pages_show_lists business_management instagram_manage_comments',
            'response_type': 'code',
            'access_type': 'offline'
        }
        
        auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(auth_params)}"
        
        try:
            webbrowser.open(auth_url)
            print(f"✅ Abierto navegador para: {redirect_uri}")
            
            print("📋 Esperando código de autorización...")
            import sys
            
        try:
            auth_code = None
            
            print("🔍 Esperando código de autorización...")
            print("📋 Pasos:")
            print("1. El navegador ya debe estar abierto con la URL")
            print("2. Completa la autorización en Facebook")
            print("3. Copia el código de la URL de redirect")
            print("4. Presiona Enter cuando estés listo")
            print("5. Luego presiona Ctrl+D para continuar")
            
            # Read until Enter or Ctrl+D
            while not auth_code:
                if sys.stdin in select([sys.stdin], [], [], 0.1)[0]:
                    auth_code = sys.stdin.readline().strip()
                    if auth_code and len(auth_code) > 5:
                        break
                    elif auth_code.lower() == 'exit':
                        print("🚪 Cancelado por el usuario")
                        return False
                elif auth_code.lower() in ['quit', 'salir', 'cancel']:
                    print("🚪 Cancelado por el usuario")
                    return False
                
                print(f"🔄 Esperando... (intentos: {30-i})")
                time.sleep(0.1)
            
        except KeyboardInterrupt:
            print("\n🚪 Cancelado por el usuario")
            return False
                    if auth_code and len(auth_code) > 10:
                        break
                time.sleep(0.1)
            
            if auth_code:
                print(f"🔄 Procesando código...")
                
                token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
                token_data = {
                    'client_id': "1289705299666205",
                    'client_secret': "c39f0a5c6cae9fb6983454954756c77f",
                    'redirect_uri': redirect_uri,
                    'code': auth_code,
                }
                
                response = requests.post(token_url, data=token_data, timeout=30)
                
                if response.status_code == 200:
                    token_info = response.json()
                    access_token = token_info.get('access_token')
                    
                    if access_token:
                        print(f"✅ ÉXITO con: {redirect_uri}")
                        print(f"🕐 Access Token: {access_token[:20]}...")
                        return test_token(access_token)
                
                else:
                    print(f"❌ Error: {response.status_code}")
            
        except Exception as e:
            print(f"❌ Error con {redirect_uri}: {e}")
    
    print("❌ Todos los métodos fallaron")
    return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Corrected Meta Token Generator")
    parser.add_argument("--create", action="store_true", help="Generate new long-lived tokens")
    parser.add_argument("--test", action="store_true", help="Test current tokens")
    parser.add_argument("--alt", action="store_true", help="Try alternative redirect methods")
    
    args = parser.parse_args()
    
    if args.alternative or args.alt:
        try_alternative()
    elif args.create:
        generate_meta_tokens()
    elif args.test:
        access_token = os.getenv("META_ACCESS_TOKEN")
        if access_token:
            test_token(access_token)
        else:
            print("❌ No hay tokens para probar")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()