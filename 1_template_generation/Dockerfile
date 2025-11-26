# ==============================================================================
# RunPod Dockerfile for Chat2SVG Stage 1 - Template Generation
# ==============================================================================
# 
# Este Dockerfile crea una imagen optimizada para RunPod Serverless que:
# - Incluye PyTorch con CUDA 11.8 pre-instalado
# - Instala Cairo para conversión SVG->PNG
# - Descarga modelos en primer uso (CLIP e ImageReward)
# - Configura el handler de RunPod
#
# Build: docker build -t chat2svg-stage1 -f Dockerfile ..
# Test:  docker run --rm --env-file .env chat2svg-stage1 python test_handler.py
# ==============================================================================

# Imagen base con PyTorch 2.1.0, Python 3.10, CUDA 11.8
# Esta imagen incluye ~5GB de dependencias pre-instaladas
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Metadata
LABEL maintainer="Chat2SVG"
LABEL description="SVG Template Generation API for RunPod Serverless"
LABEL version="1.0"

# Set working directory
WORKDIR /app

# ==============================================================================
# Instalar dependencias del sistema
# ==============================================================================

# Cairo es necesario para cairosvg (conversión SVG a PNG)
# pkg-config ayuda a encontrar las librerías instaladas
# python3-dev necesario para compilar algunas extensiones
RUN apt-get update && apt-get install -y \
    libcairo2-dev \
    pkg-config \
    python3-dev \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# ==============================================================================
# Instalar dependencias de Python
# ==============================================================================

# Copiar requirements específicos del Stage 1 (solo las dependencias necesarias)
COPY 1_template_generation/requirements_stage1.txt /app/requirements_stage1.txt

# Instalar con pip
# --no-cache-dir reduce el tamaño de la imagen
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements_stage1.txt

# Instalar RunPod SDK
RUN pip install --no-cache-dir runpod>=1.6.0

# ==============================================================================
# Copiar código del proyecto (SOLO Stage 1)
# ==============================================================================

# Crear estructura de directorios
RUN mkdir -p /app/1_template_generation /app/utils /app/output

# Copiar archivos de configuración necesarios (prompts)
COPY prompts.yaml /app/prompts.yaml
COPY prompts_edit.yaml /app/prompts_edit.yaml
# NOTA: .env NO se copia - las variables se pasan via RunPod environment

# Copiar utilidades necesarias (solo las que usa Stage 1)
COPY utils/gpt.py /app/utils/gpt.py
COPY utils/util.py /app/utils/util.py
COPY utils/__init__.py /app/utils/__init__.py

# Copiar archivos del Stage 1
COPY 1_template_generation/handler.py /app/1_template_generation/handler.py
COPY 1_template_generation/api_wrapper.py /app/1_template_generation/api_wrapper.py
COPY 1_template_generation/runpod_config.py /app/1_template_generation/runpod_config.py
COPY 1_template_generation/test_handler.py /app/1_template_generation/test_handler.py
COPY 1_template_generation/main.py /app/1_template_generation/main.py

# ==============================================================================
# Configuración del entorno
# ==============================================================================

# PYTHONUNBUFFERED=1 - Output inmediato en logs (importante para debugging)
# PYTHONPATH=/app - Python puede importar módulos desde la raíz
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Crear directorio para outputs (opcional, se usan temp dirs en handler)
RUN mkdir -p /app/output

# ==============================================================================
# Preparar modelos (opcional - descomenta para pre-download)
# ==============================================================================

# Los modelos se descargan automáticamente en primer uso (~2.5 GB)
# Para pre-descargar y acelerar primera request, descomenta:
#
# RUN python3 -c "
# import clip
# import torch
# import ImageReward as RM
# device = 'cuda' if torch.cuda.is_available() else 'cpu'
# clip.load('ViT-B/32', device=device)
# RM.load('ImageReward-v1.0')
# "

# ==============================================================================
# Configuración final
# ==============================================================================

# Cambiar al directorio del stage 1
WORKDIR /app/1_template_generation

# Health check (opcional)
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#   CMD python -c "import torch; import clip; import ImageReward" || exit 1

# Puerto (no necesario para RunPod serverless, pero útil para testing)
EXPOSE 8000

# Comando por defecto: iniciar el handler de RunPod
# RunPod ejecutará este comando y llamará a la función handler()
CMD ["python", "-u", "handler.py"]

# ==============================================================================
# Información adicional
# ==============================================================================
#
# Variables de entorno requeridas en RunPod:
# - BACKEND=Claude (o Wildcard)
# - ANTHROPIC_API_KEY=sk-ant-... (o OPENAI_API_KEY)
#
# Tamaño de imagen: ~6-8 GB (solo Stage 1, sin Stage 2 y 3)
# Memoria recomendada: 8-16 GB
# GPU recomendada: A4000 o superior (o CPU funciona pero más lento)
# Container disk: Mínimo 8 GB
#
# IMPORTANTE: Esta imagen SOLO incluye Stage 1 (Template Generation)
# No incluye Stage 2 (Detail Enhancement) ni Stage 3 (SVG Optimization)
#
# ==============================================================================
