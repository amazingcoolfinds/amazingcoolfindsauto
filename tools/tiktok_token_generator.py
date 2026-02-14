#!/usr/bin/env python3
"""
TikTok Token Generator - Create tokens for TikTok API
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
log = logging.getLogger("TikTokTokenGen")

def create_tiktok_tokens():
    """Create TikTok tokens using OAuth flow"""
    
    # Get app credentials
    client_key = os.getenv('TIKTOK_CLIENT_KEY')
    client_secret = os.getenv('TIKTOK_CLIENT_SECRET')
    
    if not client_key or not client_secret:
        print("❌ TIKTOK_CLIENT_KEY y TIKTOK_CLIENT_SECRET requeridos en .env")
        return False
    
    # Define scopes for TikTok
    scopes = [
        'user.info.basic',
        'video.list',
        'video.upload'
    ]
    
    # Create OAuth URL
    auth_url = (
        f"https://www.tiktok.com/v2/auth/authorize?"
        f"client_key={client_key}"
        f"&scope={','.join(scopes)}"
        f"&response_type=code"
        f"&redirect_uri=https://amazing-cool-finds.com/auth/tiktok"
        f"&state=tiktok_auth_{int(time.time())}"
    )
    
    print(f"🌐 Abriendo navegador para autenticación TikTok...")
    print(f"📋 URL: {auth_url}")
    print(f"🔑 Permisos solicitados: {len(scopes)}")
    print(f"📅 Redirect URI: https://amazing-cool-finds.com/auth/tiktok")
    print()
    
    try:
        # Open browser for manual authentication
        webbrowser.open(auth_url)
        print("⏳ Esperando tu autorización en TikTok...")
        
        # For testing, you would manually get the code from the callback
        print("\n📄 MANUAL INSTRUCTIONS (para testing):")
        print("1. Copia el 'code' de la URL de redirect")
        print("2. Pega el código aquí y presiona Enter")
        print("3. O simplemente presiona Enter para usar el código de ejemplo")
        
        # Read authorization code from user input
        try:
            auth_code = input("🔑 Pega el código de autorización TikTok: ").strip()
        except EOFError:
            print("📋 Usando código de ejemplo para testing...")
            auth_code = "example_tiktok_code_12345"
        
        # If no code provided, use example for testing
        if not auth_code:
            print("📋 Usando código de ejemplo para testing...")
            auth_code = "example_tiktok_code_12345"
        
        # Exchange code for tokens
        print("🔄 Intercambiando código por tokens TikTok...")
        
        token_url = "https://open.tiktokapis.com/v2/oauth/token/"
        
        token_data = {
            'client_key': client_key,
            'client_secret': client_secret,
            'code': auth_code,
            'grant_type': 'authorization_code',
            'redirect_uri': 'https://amazing-cool-finds.com/auth/tiktok'
        }
        
        response = requests.post(token_url, data=token_data, timeout=30)
        
        if response.status_code == 200:
            token_info = response.json()
            
            access_token = token_info.get('access_token')
            refresh_token = token_info.get('refresh_token')
            
            if access_token:
                # Save tokens to .env
                env_updates = f"""
# TikTok Tokens - Created on {time.strftime('%Y-%m-%d')}
TIKTOK_ACCESS_TOKEN={access_token}
TIKTOK_REFRESH_TOKEN={refresh_token}
TIKTOK_TOKEN_EXPIRES={token_info.get('expires_in', 'N/A')}
"""
                
                # Update .env file
                env_file = '.env'
                if os.path.exists(env_file):
                    with open(env_file, 'r') as f:
                        content = f.read()
                    
                    # Remove existing TIKTOK tokens if present
                    lines = content.split('\n')
                    new_lines = []
                    for line in lines:
                        if not line.startswith('TIKTOK_'):
                            new_lines.append(line)
                    
                    # Add new tokens
                    new_lines.append(env_updates.strip())
                    content = '\n'.join(new_lines)
                    
                    with open(env_file, 'w') as f:
                        f.write(content)
                
                print("✅ Tokens TikTok guardados en .env")
                print(f"🕐 Expires: {token_info.get('expires_in', 'N/A')}")
                print("📋 Access Token: OK")
                print("📋 Refresh Token: OK")
                
                # Display all tokens
                print("\n📋 TOKENS TIKTOK GUARDADOS:")
                print(f"   ✅ Access Token: {access_token[:20]}...")
                print(f"   ✅ Refresh Token: {refresh_token[:20]}...")
                print(f"   🕐 Expiración: {token_info.get('expires_in', 'N/A')}")
                
                return True
                
            else:
                print("❌ No access token received")
                return False
        else:
            print(f"❌ Error exchanging code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_current_tokens():
    """Test current TikTok tokens"""
    print("🔍 TESTING CURRENT TIKTOK TOKENS")
    print("=" * 50)
    
    access_token = os.getenv("TIKTOK_ACCESS_TOKEN")
    refresh_token = os.getenv("TIKTOK_REFRESH_TOKEN")
    
    print(f"📋 Access Token: {'✅ PRESENTE' if access_token else '❌ FALTANTE'}")
    print(f"📋 Refresh Token: {'✅ PRESENTE' if refresh_token else '❌ FALTANTE'}")
    
    if access_token:
        # Test token validity
        test_url = "https://open.tiktokapis.com/v2/user/info/"
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"✅ Token válido - User: {user_info.get('data', {}).get('user', {}).get('display_name', 'N/A')}")
        else:
            print(f"❌ Token inválido - Status: {response.status_code}")
    
    print()

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--create":
            print("🎯 TIKTOK TOKENS")
            print("=" * 60)
            success = create_tiktok_tokens()
            if success:
                print("\n✅ TOKENS TIKTOK CREADOS EXITOSAMENTE")
                print("📋 Listos para usar en el pipeline")
            else:
                print("\n❌ FALLÓ LA CREACIÓN DE TOKENS")
                
        elif command == "--test":
            test_current_tokens()
            
        elif command == "--help":
            print("🎯 TIKTOK TOKEN GENERATOR")
            print("=" * 30)
            print("Commands:")
            print("  --create   Create TikTok tokens")
            print("  --test     Test current tokens")
            print("  --help     Show this help")
    else:
        print("🎯 TIKTOK TOKEN GENERATOR")
        print("=" * 30)
        print("Use --create to generate tokens")
        print("Use --test to test current tokens")
        print("Use --help for help")

if __name__ == "__main__":
    main()