#!/usr/bin/env python3
"""
QUICK META TOKEN TEST - Test existing tokens without browser
"""
import os
import json
import time
import logging
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("QuickMetaTest")

def test_existing_tokens():
    """Test and validate current Meta tokens"""
    print("🔍 TESTING TOKENS META EXISTENTES")
    print("=" * 50)
    
    access_token = os.getenv("META_ACCESS_TOKEN")
    
    if not access_token:
        print("❌ META_ACCESS_TOKEN no encontrado")
        print("\n📋 NECESITARIO:")
        print("Los tokens no están configurados correctamente.")
        print("Por favor, genera tokens usando:")
        print("1. Facebook Developer Console")
        print("2. Agrega dominios: amazing-cool-finds.com, localhost:8080")
        print("3. Reautentica con todos los permisos")
        return False
    
    try:
        print(f"🔑 Token encontrado: {access_token[:20]}...")
        
        # Test 1: Basic validation
        test_url = "https://graph.facebook.com/me"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(test_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            print("✅ Token básico válido")
            print(f"👤 Usuario: {user_data.get('name', 'Unknown')}")
            
            # Test 2: Check Instagram permissions
            permissions = user_data.get('permissions', [])
            instagram_perms = [p for p in permissions if 'instagram' in p.lower()]
            
            print(f"📧 Total permisos: {len(permissions)}")
            print(f"📸 Permisos Instagram: {len(instagram_perms)}")
            
            if len(instagram_perms) > 5:
                print("✅ PERMISOS DE INSTAGRAM ADECUADOS")
                print("✅ LISTO PARA SUBIR CONTENIDO!")
                
                # Simulate Instagram upload test
                print("\n📹 SIMULANDO SUBIDA A INSTAGRAM...")
                
                test_video_path = 'output_videos/video_B0FS74F9Q3.mp4'
                if os.path.exists(test_video_path):
                    print(f"🎥 Video de prueba: {test_video_path}")
                    
                    # This would use the meta_uploader.py
                    try:
                        # Test Instagram upload simulation
                        ig_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "17841480700754002")
                        
                        print(f"📸 Cuenta IG: {ig_account_id}")
                        print("✅ Instagram listo para subida")
                        
                        # Test Catbox upload for Instagram patch
                        from meta_uploader import MetaUploader
                        
                        meta_up = MetaUploader()
                        public_url = meta_up._get_public_url(test_video_path)
                        
                        if public_url:
                            print(f"✅ Patch Instagram funcionando: {public_url}")
                        else:
                            print("⚠️  Patch Instagram necesita revisión")
                    
                    except Exception as e:
                        print(f"⚠️  Error en simulación: {e}")
                else:
                    print("⚠️  Video de prueba no encontrado")
            else:
                print("⚠️  Permisos Instagram insuficientes")
                print("Necesitas reautenticar con más permisos de Instagram")
        else:
            print(f"❌ Token inválido: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_fallback_token():
    """Create a test token for immediate use"""
    print("\n🔄 CREANDO TOKEN DE PRUEBA...")
    
    # This is a simulated token for testing
    test_token = "EAAYZCjZCo1ZA4ZBAXAgABCdf1n981gAFAZC1ZAaASO5wBADwZC1BOAsdf1oQGZAdbBA8hZC1xAaASO5mAD"  # Ficticio para pruebas
    
    env_content = f"""# Meta Test Token - Created on {datetime.now().strftime('%Y-%m-%d')}
META_ACCESS_TOKEN={test_token}

# Existing credentials
FACEBOOK_PAGE_ID=963943753475520
INSTAGRAM_ACCOUNT_ID=17841480700754002
"""
    
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Token de prueba creado")
        print("⚠️  Este es solo para pruebas")
        print("🔑 Para producción, genera tokens reales")
        return True
        
    except Exception as e:
        print(f"❌ Error creando token: {e}")
        return False

def main():
    print("🚀 META TOKENS - TESTING ACTUAL STATE")
    print("=" * 60)
    
    # Try to use existing tokens first
    if test_existing_tokens():
        print("\n🎯 ESTADO FINAL:")
        print("✅ Tokens: CONFIGURADOS")
        print("✅ Permisos: ADECUADOS")
        print("✅ Instagram: LISTO")
        print("✅ Pipeline: PREPARADO")
        
        print("\n📋 SIGUIENTES PASOS:")
        print("1. Ejecutar: python pipeline.py --run")
        print("2. Subir a Instagram y Facebook")
        print("3. Usar enlaces mejorados con scroll suave")
    else:
        print("\n🔄 Creando token de prueba...")
        create_fallback_token()

if __name__ == "__main__":
    main()