#!/bin/bash

# Script de instalación y setup para Chat2SVG Stage 1
# Este script facilita la configuración inicial del proyecto

set -e  # Exit on error

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo ""
    print_message "$BLUE" "================================"
    print_message "$BLUE" "$1"
    print_message "$BLUE" "================================"
}

# Banner
clear
print_header "🎨 Chat2SVG Stage 1 - Setup Script"
echo ""
print_message "$GREEN" "Este script configurará tu entorno para usar Chat2SVG Stage 1"
echo ""

# Check Python version
print_header "🐍 Verificando Python"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_message "$GREEN" "✅ Python encontrado: $PYTHON_VERSION"
    
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 10 ]); then
        print_message "$RED" "❌ Se requiere Python 3.10 o superior"
        exit 1
    fi
else
    print_message "$RED" "❌ Python3 no encontrado. Por favor instala Python 3.10+"
    exit 1
fi

# Check if running from correct directory
if [ ! -f "../requirements.txt" ]; then
    print_message "$RED" "❌ Error: Ejecuta este script desde el directorio 1_template_generation/"
    exit 1
fi

# Check for .env file
print_header "🔐 Verificando Variables de Entorno"
if [ -f "../.env" ]; then
    print_message "$GREEN" "✅ Archivo .env encontrado"
    
    # Check if required variables are set
    if grep -q "BACKEND" ../.env && grep -q "API_KEY" ../.env; then
        print_message "$GREEN" "✅ Variables de entorno configuradas"
    else
        print_message "$YELLOW" "⚠️  Variables de entorno incompletas"
    fi
else
    print_message "$YELLOW" "⚠️  Archivo .env no encontrado"
    read -p "¿Deseas crear uno ahora? (s/n): " create_env
    
    if [ "$create_env" = "s" ] || [ "$create_env" = "S" ]; then
        echo ""
        print_message "$BLUE" "Selecciona tu backend:"
        echo "1) Claude (Anthropic)"
        echo "2) Wildcard (OpenAI compatible)"
        read -p "Opción (1/2): " backend_option
        
        if [ "$backend_option" = "1" ]; then
            BACKEND="Claude"
            read -p "Ingresa tu ANTHROPIC_API_KEY: " API_KEY
            cat > ../.env << EOF
# Chat2SVG Configuration
BACKEND=Claude
ANTHROPIC_API_KEY=$API_KEY
EOF
        else
            BACKEND="Wildcard"
            read -p "Ingresa tu OPENAI_API_KEY: " API_KEY
            cat > ../.env << EOF
# Chat2SVG Configuration
BACKEND=Wildcard
OPENAI_API_KEY=$API_KEY
EOF
        fi
        
        print_message "$GREEN" "✅ Archivo .env creado"
    else
        print_message "$YELLOW" "⚠️  Recuerda crear el archivo .env manualmente"
    fi
fi

# Check for virtual environment
print_header "📦 Verificando Entorno Virtual"
if [ -d "../venv" ] || [ -d "venv" ]; then
    print_message "$GREEN" "✅ Entorno virtual encontrado"
else
    print_message "$YELLOW" "⚠️  No se encontró entorno virtual"
    read -p "¿Deseas crear uno ahora? (s/n): " create_venv
    
    if [ "$create_venv" = "s" ] || [ "$create_venv" = "S" ]; then
        print_message "$BLUE" "Creando entorno virtual..."
        cd ..
        python3 -m venv venv
        cd 1_template_generation
        print_message "$GREEN" "✅ Entorno virtual creado"
        print_message "$YELLOW" "💡 Actívalo con: source ../venv/bin/activate"
    fi
fi

# Check system dependencies
print_header "🔧 Verificando Dependencias del Sistema"

# Check for Cairo
if pkg-config --exists cairo; then
    print_message "$GREEN" "✅ Cairo encontrado"
else
    print_message "$YELLOW" "⚠️  Cairo no encontrado"
    print_message "$BLUE" "Instalación recomendada:"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install cairo pkg-config"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  sudo apt-get install libcairo2-dev pkg-config python3-dev"
    fi
fi

# Install Python dependencies
print_header "📚 Instalando Dependencias de Python"
echo "Elige qué instalar:"
echo "1) Solo Stage 1 (recomendado - ~3 GB)"
echo "2) Proyecto completo (todos los stages - ~12 GB)"
echo "3) Saltar instalación"
read -p "Opción (1/2/3): " install_option

if [ "$install_option" = "1" ]; then
    print_message "$BLUE" "Instalando dependencias de Stage 1..."
    pip install --upgrade pip
    pip install -r requirements_stage1.txt
    print_message "$GREEN" "✅ Dependencias de Stage 1 instaladas"
elif [ "$install_option" = "2" ]; then
    print_message "$BLUE" "Instalando dependencias completas..."
    pip install --upgrade pip
    pip install -r ../requirements.txt
    print_message "$GREEN" "✅ Dependencias completas instaladas"
else
    print_message "$YELLOW" "⚠️  Instalación saltada"
fi

# Download models
print_header "🤖 Descargando Modelos"
read -p "¿Descargar modelos pre-entrenados ahora? (s/n): " download_models

if [ "$download_models" = "s" ] || [ "$download_models" = "S" ]; then
    print_message "$BLUE" "Descargando CLIP e ImageReward..."
    python3 << 'EOF'
import clip
import torch
import ImageReward as RM

try:
    print("Descargando CLIP...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, preprocess = clip.load("ViT-B/32", device=device)
    print("✅ CLIP descargado")
    
    print("Descargando ImageReward...")
    reward_model = RM.load("ImageReward-v1.0")
    print("✅ ImageReward descargado")
    
    print("\n🎉 Todos los modelos descargados correctamente!")
except Exception as e:
    print(f"❌ Error al descargar modelos: {e}")
    print("Los modelos se descargarán automáticamente en el primer uso")
EOF
else
    print_message "$YELLOW" "⚠️  Los modelos se descargarán en el primer uso"
fi

# Create output directories
print_header "📁 Creando Directorios"
mkdir -p test_output
mkdir -p ../output
print_message "$GREEN" "✅ Directorios creados"

# Verification
print_header "✅ Verificación Final"
python3 << 'EOF'
import sys

print("Verificando instalación...")
errors = []

try:
    import torch
    print(f"✅ PyTorch {torch.__version__}")
    if torch.cuda.is_available():
        print(f"   🎮 CUDA disponible: {torch.cuda.get_device_name(0)}")
except ImportError:
    errors.append("❌ PyTorch no instalado")

try:
    import clip
    print("✅ CLIP")
except ImportError:
    errors.append("❌ CLIP no instalado")

try:
    import ImageReward
    print("✅ ImageReward")
except ImportError:
    errors.append("❌ ImageReward no instalado")

try:
    import cairosvg
    print("✅ CairoSVG")
except ImportError:
    errors.append("❌ CairoSVG no instalado")

try:
    import runpod
    print("✅ RunPod SDK")
except ImportError:
    errors.append("❌ RunPod SDK no instalado")

try:
    import yaml
    print("✅ PyYAML")
except ImportError:
    errors.append("❌ PyYAML no instalado")

if errors:
    print("\nErrores encontrados:")
    for error in errors:
        print(error)
    sys.exit(1)
else:
    print("\n🎉 Todas las dependencias verificadas correctamente!")
EOF

if [ $? -eq 0 ]; then
    print_header "🎉 ¡Setup Completado!"
    echo ""
    print_message "$GREEN" "Todo está listo para usar Chat2SVG Stage 1"
    echo ""
    print_message "$BLUE" "Próximos pasos:"
    echo "  1. Activa el entorno virtual (si usas uno):"
    echo "     source ../venv/bin/activate"
    echo ""
    echo "  2. Prueba el sistema:"
    echo "     python test_handler.py"
    echo ""
    echo "  3. O ejecuta el CLI original:"
    echo "     python main.py --target test --output_path ../output --output_folder test"
    echo ""
    print_message "$YELLOW" "📖 Lee README_RUNPOD.md para más información"
else
    print_message "$RED" "❌ Hubo algunos errores en la instalación"
    print_message "$YELLOW" "Revisa los mensajes arriba para más detalles"
fi
