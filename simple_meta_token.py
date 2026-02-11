#!/usr/bin/env python3
"""
SIMPLE META TOKEN GENERATOR - Using your actual credentials
"""
import os
import sys
import json
import time
import logging
import requests
import webbrowser
from urllib.parse import urlencode, parse_qs
import argparse

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SimpleMetaTokenGen")

def generate_meta_tokens():
    """Generate Meta long-lived tokens using your credentials"""
    print("🎯 META TOKENS DE LARGA DURACIÓN")
    print("=" * 60)
    
    # Your actual credentials
    app_id = "1289705299666205"
    app_secret = "c39f0a5c6cae9fb6983454954756c77f"
    redirect_uri = "https://localhost:8080"
    
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
    
    # Generate authorization URL
    auth_params = {
        'client_id': app_id,
        'redirect_uri': redirect_uri,
        'scope': ' '.join(scopes),
        'response_type': 'code',
        'access_type': 'offline'
    }
    
    auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(auth_params)}"
    
    print(f"🌐 ABIENDO NAVEGADOR PARA AUTENTICACIÓN...")
    print(f"📋 URL: {auth_url}")
    print(f"🔑 Permisos solicitados: {len(scopes)} (long-lived)")
    print(f"📅 Redirect: {redirect_uri}")
    print()
    
    # Open browser
    try:
        webbrowser.open(auth_url)
        print("✅ Navegador abierto automáticamente")
    except:
        print("⚠️  Por favor, abre manualmente la URL de arriba")
    
    print()
    print("🔑 INSTRUCCIONES:")
    print("1. Inicia sesión en Facebook")
    print("2. Acepta todos los permisos solicitados")
    print("3. Serás redirigido a localhost (puede mostrar error - es normal)")
    print("4. Copia el código completo de la URL")
    print()
    
    # Wait for manual code input
    auth_code = input("📋 PEGA EL CÓDIGO DE AUTORIZACIÓN AQUÍ: ").strip()
    
    if not auth_code:
        print("❌ No se proporcionó código de autorización")
        return False
    
    print(f"🔄 Intercambiando código por tokens...")
    
    try:
        # Exchange code for access token
        token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
        token_data = {
            'client_id': app_id,
            'client_secret': app_secret,
            'redirect_uri': redirect_uri,
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
                
                # Test token
                test_url = "https://graph.facebook.com/me"
                headers = {"Authorization": f"Bearer {access_token}"}
                test_response = requests.get(test_url, headers=headers, timeout=10)
                
                if test_response.status_code == 200:
                    user_data = test_response.json()
                    print(f"✅ Token válido para: {user_data.get('name', 'Unknown')}")
                    print(f"📧 Permisos: {len(user_data.get('permissions', []))}")
                    
                    # Save to .env
                    env_content = f"""# Meta Long-Lived Tokens - Created on {time.strftime('%Y-%m-%d')}
META_ACCESS_TOKEN={access_token}
# Optional: META_ACCESS_TOKEN_EXPIRES={expires_at}

# Existing credentials
FACEBOOK_PAGE_ID=963943753475520
INSTAGRAM_ACCOUNT_ID=17841480700754002
"""
                    
                    with open('.env', 'w') as f:
                        f.write(env_content)
                    
                    print("✅ Tokens guardados en .env")
                    print("🎯 META TOKENS LISTOS PARA PRODUCCIÓN!")
                    
                    return True
                else:
                    print("❌ Error validando token")
                    print(f"Status: {test_response.status_code}")
                    return False
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

def test_current_tokens():
    """Test existing Meta tokens"""
    print("🔍 TESTING TOKENS ACTUALES")
    print("=" * 50)
    
    access_token = os.getenv("META_ACCESS_TOKEN")
    
    if not access_token:
        print("❌ META_ACCESS_TOKEN no encontrado")
        return False
    
    try:
        # Test token validity
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
            
            if instagram_perms:
                print(f"📸 Instagram permissions: {len(instagram_perms)}")
                print("✅ LISTO PARA SUBIR A INSTAGRAM!")
            else:
                print("⚠️  No hay permisos de Instagram")
            
            return True
        else:
            print(f"❌ Token inválido: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    import sys
    
    parser = argparse.ArgumentParser(description="Simple Meta Token Generator")
    parser.add_argument("--create", action="store_true", help="Generate new long-lived tokens")
    parser.add_argument("--test", action="store_true", help="Test current tokens")
    
    args = parser.parse_args()
    
    if args.create:
        success = generate_meta_tokens()
        sys.exit(0 if success else 1)
    elif args.test:
        test_current_tokens()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()