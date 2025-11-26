#!/bin/bash

# Script optimizado para build de Stage 1 SOLAMENTE
# Este script construye una imagen Docker que incluye ÚNICAMENTE el Stage 1

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Chat2SVG Stage 1 - Build Optimizado${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Verificar que estamos en el lugar correcto
if [ ! -f "handler.py" ]; then
    echo -e "${YELLOW}⚠️  Ejecuta este script desde 1_template_generation/${NC}"
    exit 1
fi

cd ..

echo -e "${GREEN}✓ Construyendo imagen SOLO con Stage 1...${NC}"
echo ""
echo "Tamaño estimado final: ~6-8 GB"
echo "Incluye:"
echo "  ✓ Stage 1 (Template Generation)"
echo "  ✗ Stage 2 (NO incluido)"
echo "  ✗ Stage 3 (NO incluido)"
echo ""

# Build
docker build \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    -t chat2svg-stage1:latest \
    -f 1_template_generation/Dockerfile \
    .

echo ""
echo -e "${GREEN}✅ Build completado!${NC}"
echo ""
echo "Tamaño de la imagen:"
docker images chat2svg-stage1:latest

echo ""
echo -e "${BLUE}Próximos pasos:${NC}"
echo "1. Probar localmente:"
echo "   docker run --rm --env-file .env chat2svg-stage1 python test_handler.py"
echo ""
echo "2. Push a Docker Hub:"
echo "   docker tag chat2svg-stage1:latest usuario/chat2svg-stage1:latest"
echo "   docker push usuario/chat2svg-stage1:latest"
