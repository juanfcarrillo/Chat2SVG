"""
Script de prueba local para el handler de RunPod
Simula una request de RunPod para testing local
"""

import sys
sys.path.append('..')

from handler import handler
import json
from pathlib import Path
import base64


def test_handler():
    """Prueba el handler con diferentes casos"""
    
    print("🧪 Testing RunPod Handler Locally\n")
    print("=" * 60)
    
    # Test 1: Request básica
    print("\n📝 Test 1: Request básica")
    print("-" * 60)
    
    test_event_1 = {
        "input": {
            "prompt": "A simple cat sitting",
            "target": "test_cat",
            "refine_iter": 1,  # Solo 1 iteración para test rápido
        }
    }
    
    print(f"Input: {json.dumps(test_event_1, indent=2)}")
    print("\n⏳ Procesando...")
    
    try:
        result = handler(test_event_1)
        
        if result.get("success"):
            print("✅ SUCCESS!")
            print(f"\n📊 Metadata:")
            for key, value in result["metadata"].items():
                print(f"  - {key}: {value}")
            
            # Guardar resultados
            output_dir = Path("test_output")
            output_dir.mkdir(exist_ok=True)
            
            # Guardar SVG
            svg_path = output_dir / "test_cat.svg"
            svg_path.write_text(result["best_svg"])
            print(f"\n💾 SVG guardado en: {svg_path}")
            
            # Guardar PNG
            png_path = output_dir / "test_cat.png"
            png_data = base64.b64decode(result["best_png_base64"])
            png_path.write_bytes(png_data)
            print(f"💾 PNG guardado en: {png_path}")
            
            print(f"\n📈 Iteraciones generadas: {len(result['all_iterations'])}")
            
        else:
            print(f"❌ ERROR: {result.get('error')}")
            if 'traceback' in result:
                print(f"\n🔍 Traceback:\n{result['traceback']}")
    
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Test 2: Request con parámetros avanzados
    print("\n\n📝 Test 2: Request con CLIP")
    print("-" * 60)
    
    test_event_2 = {
        "input": {
            "prompt": "A rocket ship flying to the moon",
            "target": "rocket",
            "refine_iter": 1,
            "reward_model": "CLIP",
        }
    }
    
    print(f"Input: {json.dumps(test_event_2, indent=2)}")
    print("\n⏳ Procesando...")
    
    try:
        result = handler(test_event_2)
        
        if result.get("success"):
            print("✅ SUCCESS!")
            print(f"Mejor iteración: {result['best_index']}")
            
            # Guardar
            output_dir = Path("test_output")
            svg_path = output_dir / "test_rocket.svg"
            svg_path.write_text(result["best_svg"])
            print(f"💾 SVG guardado en: {svg_path}")
        else:
            print(f"❌ ERROR: {result.get('error')}")
    
    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
    
    # Test 3: Request con error (falta prompt)
    print("\n\n📝 Test 3: Request inválida (sin prompt)")
    print("-" * 60)
    
    test_event_3 = {
        "input": {
            "target": "test_error"
        }
    }
    
    print(f"Input: {json.dumps(test_event_3, indent=2)}")
    
    try:
        result = handler(test_event_3)
        
        if result.get("success"):
            print("❌ Se esperaba un error pero fue exitoso!")
        else:
            print(f"✅ Error detectado correctamente: {result.get('error')}")
    
    except Exception as e:
        print(f"✅ Exception esperada: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Tests completados!")


if __name__ == "__main__":
    test_handler()
