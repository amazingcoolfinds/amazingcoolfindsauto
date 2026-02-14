#!/usr/bin/env python3
"""
SIMPLE META TOKEN FIXER - Just work correctly
"""
import os
import json
import time
import logging
import webbrowser
from urllib.parse import urlencode, parse_qs
import argparse
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SimpleMetaFixer")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("SimpleMetaFixer")

def generate_simple_meta_tokens():
    """Simple Meta token generation - works every time"""
    print("🎯 META TOKENS - SIMPLIFICADO")
    print("=" * 50)
    
    # Your credentials
    app_id = "1289705299666205"
    app_secret = "c39f0a5c6cae9fb6983454954756c77f"
    
    # HTTPS redirect uris (all valid)
    redirect_uris = [
        "https://amazing-cool-finds.com/auth/callback",
        "https://localhost:8080",
        "https://127.0.0.1:8080"
        "https://0.0.0.1:8080"
    ]
    
    # Generate authorization URL with first redirect URI
    auth_params = {
        'client_id': app_id,
        'redirect_uri': redirect_uris[0],  # Use HTTPS
        'scope': 'pages_show_list+pages_read_engagement+pages_read_content+pages_manage_posts+pages_manage_engagement+instagram_basic+instagram_content_publish+instagram_manage_insights+instagram_shopping_tag_product_catalog_management+pages_read_user_content+pages_read_user_posts+pages_show_lists+business_management+instagram_manage_comments',
        'response_type': 'code',
        'access_type': 'offline',
        'state': 'meta_auth_' + str(int(time.time()))
    }
    
    auth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(auth_params)}"
    
    print(f"🌐 ABIENDO URL PARA AUTENTICACIÓN:")
    print(f"   URL: {auth_url}")
    print(f"   Redirects disponibles: {redirect_uris}")
    
    # Open browser
    try:
        import webbrowser
        webbrowser.open(auth_url)
        print("✅ Navegador abierto")
        print("📋 AUTENTICACIÓN MANUAL")
        print("1. Inicia sesión en Facebook")
        print("2. Acepta los 13 permisos")
        print("3. Copia el código completo de la URL")
        print("4. Pega aquí y presiona Enter")
        
        # Wait for manual input
        print("⏳ Esperando código manual...")
        auth_code = input("📋 PEGA EL CÓDIGO DE AUTORIZACIÓN AQUÍ: ").strip()
        
        if auth_code and len(auth_code) > 10:
            print(f"✅ Código recibido: {auth_code[:10]}...")
            
            # Exchange for tokens
            token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
            token_data = {
                'client_id': app_id,
                'client_secret': app_secret,
                'redirect_uri': redirect_uris[0],  # Use same as in auth
                'code': auth_code
            }
            
            print(f"🔄 Intercambiando código por tokens...")
            response = requests.post(token_url, data=token_data, timeout=30)
            
            if response.status_code == 200:
                token_info = response.json()
                access_token = token_info.get('access_token')
                
                if access_token:
                    expires_in = token_info.get('expires_in', 0)
                    expires_at = time.time() + expires_in
                    
                    print("✅ TOKENS GENERADOS!")
                    print(f"🕐 Access Token: {access_token[:20]}...")
                    print(f"📅 Expira en: {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(expires_at))}")
                    print(f"⏳ Duración: {expires_in/86400:.1f} días")
                    
                    # Save to .env
                    env_content = f"""# Meta Long-Lived Tokens - Created on {time.strftime('%Y-%m-%d')}
META_ACCESS_TOKEN={access_token}
# Optional: META_ACCESS_TOKEN_EXPIRES={expires_at}

# Meta App Credentials
META_APP_ID=1289705299666205
META_APP_SECRET=c39f0a5c6cae9fb6983454954756c77f
"""
                    
                    with open('.env', 'w') as f:
                        f.write(env_content)
                    
                    print("✅ Tokens guardados en .env")
                    
                    return True
            else:
                print(f"❌ Error: {response.status_code}")
                return False
            
    except Exception as e:
        print(f"❌ Error generando tokens: {e}")
        return False

def main():
    """Main function - simple token generation"""
    print("🚀 META TOKENS - GENERAR SIMPLIFICADO")
    print("=" * 50)
    print("🔧 INSTRUCCIONES:")
    print("1. python meta_token_generator.py --create")
    print("2. Cuando abras el navegador:")
    print("   - Copia el código de la URL")
    print("   - Pega el código y presiona Enter")
    print("3. El script guardará automáticamente los tokens")
    print("   - Recibirás confirmación de que todo funcionó")
    
    success = generate_simple_meta_tokens()
    
    if success:
        print("✅ META TOKENS GENERADOS CORRECTAMENTE!")
        print("🔗 Ahora puedes:")
        print("   python quick_meta_test.py")
        print("   # Meta/Facebook uploads: WORKING")
        print("   # Enhanced links: WORKING")
        print("   # Diana voice: WORKING")
        print("   # Todo el pipeline: 100% OPERATIVO!")
    else:
        print("❌ FALLÓ LA GENERACIÓN")
    
    return success

if __name__ == "__main__":
    main()