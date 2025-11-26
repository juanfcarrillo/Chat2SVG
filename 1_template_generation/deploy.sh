#!/bin/bash

# Script para construir y desplegar la imagen Docker de Chat2SVG Stage 1 en RunPod

set -e  # Exit on error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
IMAGE_NAME="${IMAGE_NAME:-chat2svg-stage1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DOCKER_USERNAME="${DOCKER_USERNAME:-}"

# Función para imprimir mensajes con color
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

# Verificar que estamos en el directorio correcto
if [ ! -f "1_template_generation/Dockerfile" ]; then
    print_message "$RED" "❌ Error: Debe ejecutar este script desde la raíz del proyecto Chat2SVG"
    exit 1
fi

print_header "🚀 Chat2SVG Stage 1 - Build & Deploy Script"

# Menú de opciones
echo ""
echo "Seleccione una opción:"
echo "1) Build imagen Docker localmente"
echo "2) Build y push a Docker Hub"
echo "3) Build y test localmente"
echo "4) Solo test (sin build)"
echo "5) Limpiar imágenes antiguas"
echo "0) Salir"
echo ""
read -p "Opción: " option

case $option in
    1)
        print_header "🔨 Building Docker Image"
        
        docker build \
            -t ${IMAGE_NAME}:${IMAGE_TAG} \
            -f 1_template_generation/Dockerfile \
            .
        
        print_message "$GREEN" "✅ Imagen construida: ${IMAGE_NAME}:${IMAGE_TAG}"
        print_message "$YELLOW" "💡 Para probar: docker run --env-file .env ${IMAGE_NAME}:${IMAGE_TAG}"
        ;;
    
    2)
        print_header "🔨 Building and Pushing to Docker Hub"
        
        # Verificar username
        if [ -z "$DOCKER_USERNAME" ]; then
            read -p "Docker Hub username: " DOCKER_USERNAME
        fi
        
        FULL_IMAGE_NAME="${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
        
        # Build
        print_message "$BLUE" "📦 Building image..."
        docker build \
            -t ${IMAGE_NAME}:${IMAGE_TAG} \
            -t ${FULL_IMAGE_NAME} \
            -f 1_template_generation/Dockerfile \
            .
        
        # Login to Docker Hub
        print_message "$BLUE" "🔐 Logging into Docker Hub..."
        docker login
        
        # Push
        print_message "$BLUE" "☁️  Pushing to Docker Hub..."
        docker push ${FULL_IMAGE_NAME}
        
        print_message "$GREEN" "✅ Imagen publicada: ${FULL_IMAGE_NAME}"
        print_message "$YELLOW" "💡 Usa esta imagen en RunPod: ${FULL_IMAGE_NAME}"
        ;;
    
    3)
        print_header "🔨 Build and Test Locally"
        
        # Build
        print_message "$BLUE" "📦 Building image..."
        docker build \
            -t ${IMAGE_NAME}:${IMAGE_TAG} \
            -f 1_template_generation/Dockerfile \
            .
        
        # Check if .env exists
        if [ ! -f ".env" ]; then
            print_message "$RED" "❌ Error: Archivo .env no encontrado"
            print_message "$YELLOW" "💡 Crea un archivo .env con:"
            echo "BACKEND=Claude"
            echo "ANTHROPIC_API_KEY=tu_clave"
            exit 1
        fi
        
        # Run test
        print_message "$BLUE" "🧪 Running test..."
        docker run \
            --rm \
            --env-file .env \
            -v $(pwd)/1_template_generation/test_output:/app/1_template_generation/test_output \
            ${IMAGE_NAME}:${IMAGE_TAG} \
            python test_handler.py
        
        print_message "$GREEN" "✅ Test completado!"
        print_message "$YELLOW" "💡 Revisa los resultados en: 1_template_generation/test_output/"
        ;;
    
    4)
        print_header "🧪 Testing Locally (without Docker)"
        
        # Check if .env exists
        if [ ! -f ".env" ]; then
            print_message "$RED" "❌ Error: Archivo .env no encontrado"
            exit 1
        fi
        
        # Load .env
        export $(cat .env | grep -v '^#' | xargs)
        
        # Run test
        cd 1_template_generation
        python test_handler.py
        cd ..
        
        print_message "$GREEN" "✅ Test completado!"
        ;;
    
    5)
        print_header "🧹 Cleaning Old Images"
        
        print_message "$BLUE" "🗑️  Removiendo imágenes antiguas de ${IMAGE_NAME}..."
        docker images | grep ${IMAGE_NAME} | awk '{print $3}' | xargs -r docker rmi -f || true
        
        print_message "$BLUE" "🗑️  Removiendo imágenes dangling..."
        docker image prune -f
        
        print_message "$GREEN" "✅ Limpieza completada!"
        ;;
    
    0)
        print_message "$YELLOW" "👋 Saliendo..."
        exit 0
        ;;
    
    *)
        print_message "$RED" "❌ Opción inválida"
        exit 1
        ;;
esac

echo ""
print_message "$GREEN" "🎉 Proceso completado!"

# Mostrar siguientes pasos si se hizo push
if [ "$option" = "2" ]; then
    echo ""
    print_header "📋 Siguientes Pasos para Deploy en RunPod"
    echo ""
    echo "1. Ve a https://www.runpod.io/console/serverless"
    echo "2. Crea un nuevo Endpoint"
    echo "3. Configura:"
    echo "   - Docker Image: ${FULL_IMAGE_NAME}"
    echo "   - Container Disk: 10 GB mínimo"
    echo "   - GPU: A4000 o superior (o CPU)"
    echo "   - Environment Variables:"
    echo "     * BACKEND=Claude"
    echo "     * ANTHROPIC_API_KEY=tu_clave"
    echo "4. Deploy!"
    echo ""
    print_message "$YELLOW" "📖 Para más detalles, lee: 1_template_generation/README_RUNPOD.md"
fi
