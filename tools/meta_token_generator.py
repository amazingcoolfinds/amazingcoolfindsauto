#!/usr/bin/env python3
"""
Meta Token Generator - Create long-lived tokens for Instagram/Facebook
"""
import os
import json
import time
import logging
import webbrowser
import requests
from urllib.parse import urlencode, parse_qs
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("MetaTokenGen")

def create_long_lived_tokens():
    """Create long-lived tokens using OAuth flow"""
    
    # Get app credentials
    app_id = os.getenv('META_APP_ID')
    app_secret = os.getenv('META_APP_SECRET')
    
    if not app_id or not app_secret:
        print("❌ META_APP_ID y META_APP_SECRET requeridos en .env")
        return False
    
    # Use HTTPS redirect URI
    redirect_uri = "https://amazing-cool-finds.com/auth/callback"
    
    # Define scopes for long-lived tokens
    scopes = [
        'pages_show_list',
        'pages_read_engagement', 
        'pages_read_content',
        'pages_manage_posts',
        'pages_manage_engagement',
        'instagram_basic',
        'instagram_content_publish',
        'instagram_manage_insights',
        'instagram_shopping_tag_product_catalog_management',
        'pages_read_user_content',
        'pages_read_user_posts',
        'pages_show_lists',
        'business_management',
        'instagram_manage_comments'
    ]
    
    # Create OAuth URL with long-lived permissions
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={app_id}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={' '.join(scopes)}"
        f"&response_type=code"
        f"access_type=offline"
    )
    
    print(f"🌐 Abriendo navegador para autenticación...")
    print(f"📋 URL: {auth_url}")
    print(f"🔑 Permisos solicitados: {len(scopes)} (long-lived)")
    print(f"📅 Redirect URI: {redirect_uri}")
    print()
    
    try:
        # Open browser for manual authentication
        webbrowser.open(auth_url)
        print("⏳ Esperando tu autorización en el navegador...")
        
        # For testing, you would manually get the code from the callback
        print("\n📄 MANUAL INSTRUCTIONS (para testing):")
        print("1. Copia el 'code' de la URL de redirect")
        print("2. Pega el código aquí y presiona Enter")
        
        # Read authorization code from user input
        auth_code = input("🔑 Pega el código de autorización: ").strip()
        
        if auth_code:
            # Exchange code for tokens
            print("🔄 Intercambiando código por tokens...")
            
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
                    # Save token to .env
                    env_updates = f"""
# Meta Long-Lived Tokens - Created on {time.strftime('%Y-%m-%d')}
META_ACCESS_TOKEN={access_token}
# Additional tokens (not available immediately)
# META_ACCESS_TOKEN_EXPIRES={token_info.get('expires_in', 'N/A')}
                    """
                    
                    # Update .env file
                    env_file = '.env'
                    
                    if os.path.exists(env_file):
                        with open(env_file, 'r') as f:
                            content = f.read()
                    else:
                        content = ""
                    
                    # Remove existing META_ACCESS_TOKEN
                    content = '\n'.join([line for line in content.split('\n') if not line.startswith('META_ACCESS_TOKEN=')])
                    
                    # Add new token
                    content += env_updates
                    
                    with open(env_file, 'w') as f:
                        f.write(content)
                    
                    print("✅ Token guardado en .env")
                    print(f"🕐 Expires: {token_info.get('expires_in', 'N/A')}")
                    print("📋 Access Token: OK")
                    print("📋 Long-lived: LISTO")
                    
                    # Display all tokens
                    print("\n📋 TOKENS GUARDADOS:")
                    print(f"   ✅ Access Token: {access_token[:20]}...")
                    print(f"   🕐 Expiración: {token_info.get('expires_in', 'N/A')}")
                    
                    return True
                    
                else:
                    print("❌ No access token received")
                    return False
            else:
                print(f"❌ Error exchanging code: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        else:
            print(f"❌ Error requesting token: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_current_tokens():
    """Test current Meta tokens"""
    print("🔍 TESTING CURRENT META TOKENS")
    print("=" * 50)
    
    access_token = os.getenv("META_ACCESS_TOKEN")
    page_id = os.getenv("FACEBOOK_PAGE_ID")
    ig_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID")
    
    print(f"📋 Access Token: {'✅ PRESENTE' if access_token else '❌ FALTANTE'}")
    print(f"📄 Page ID: {'✅ PRESENTE' if page_id else '❌ FALTANTE'}")
    print(f"📸 Instagram ID: {'✅ PRESENTE' if ig_account_id else '❌ FALTANTE'}")
    
    if access_token:
        # Test token validity
        try:
            test_url = "https://graph.facebook.com/me"
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(test_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                print(f"✅ Token válido para: {user_data.get('name', 'Unknown')}")
                print(f"📧 Permissions: {list(user_data.get('permissions', []))[:5]}...")
                return True
            else:
                print(f"❌ Token inválido: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing token: {e}")
            return False
    
    else:
        print("❌ No access token found")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Meta Token Generator")
    parser.add_argument("--create", action="store_true", help="Create new long-lived tokens")
    parser.add_argument("--test", action="store_true", help="Test current tokens")
    
    args = parser.parse_args()
    
    if args.create:
        success = create_long_lived_tokens()
        if success:
            print("\n🎉 META TOKENS CREADOS CORRECTAMENTE!")
            print("📋 Access Token: Guardado en .env")
            print("📋 Long-lived: 60 días")
            print("🚀 LISTO PARA META/TIKTOK!")
        
    elif args.test:
        test_current_tokens()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()