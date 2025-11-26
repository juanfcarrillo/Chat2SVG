# Chat2SVG Stage 1 - Template Generation API

> 🚀 **API Serverless para generar plantillas SVG desde texto usando RunPod**

## ⚠️ Alcance

Esta implementación incluye **SOLO Stage 1** del pipeline Chat2SVG:

✅ **Incluido:**
- Generación de plantillas SVG desde descripción de texto
- Refinamiento iterativo usando LLM (Claude/Wildcard)
- Selección automática del mejor SVG con IA (ImageReward/CLIP)
- API REST serverless compatible con RunPod

❌ **NO Incluido:**
- Stage 2: Detail Enhancement (mejora con Stable Diffusion)
- Stage 3: SVG Optimization (optimización de paths con VAE)

## 🚀 Quick Start

```bash
# Setup automático
bash setup.sh

# Test local
python test_handler.py

# Deploy a RunPod
bash deploy.sh
```

## 📚 Documentación

- **[README_RUNPOD.md](README_RUNPOD.md)** - Documentación completa y detallada
- **[QUICKREF.md](QUICKREF.md)** - Referencia rápida de comandos
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Checklist de producción

## 📦 Archivos Principales

```
1_template_generation/
├── handler.py                   # 🔥 Handler de RunPod
├── test_handler.py              # 🧪 Tests
├── Dockerfile                   # 🐳 Imagen Docker (SOLO Stage 1)
├── requirements_stage1.txt      # 📦 Dependencias mínimas
├── setup.sh                     # 🔧 Setup automático
├── deploy.sh                    # 🚀 Build & deploy
└── README_RUNPOD.md            # 📖 Docs completas
```

## 💻 Uso Básico

### Local

```python
from handler import handler

result = handler({
    "input": {
        "prompt": "A cute cat sitting",
        "refine_iter": 2
    }
})

print(result["best_svg"])
```

### RunPod API

```python
import requests

url = "https://api.runpod.ai/v2/{endpoint-id}/runsync"
response = requests.post(url, 
    headers={"Authorization": "Bearer {api-key}"},
    json={"input": {"prompt": "A spaceship"}})
```

## 🔧 Requisitos

- Python 3.10+
- Cairo (sistema)
- Variables de entorno:
  - `BACKEND=Claude` (o Wildcard)
  - `ANTHROPIC_API_KEY=...` (o OPENAI_API_KEY)

## 📊 Modelos

| Modelo | Tamaño | Descarga |
|--------|--------|----------|
| CLIP ViT-B/32 | ~338 MB | Automática |
| ImageReward | ~2.1 GB | Automática |

**Total:** ~2.5 GB

## ⚡ Performance

| Iteraciones | Tiempo | Costo/Request (GPU A4000) |
|-------------|--------|---------------------------|
| 1 | ~30s | $0.01-0.02 |
| 2 (default) | ~60s | $0.02-0.04 |
| 5 | ~150s | $0.05-0.10 |

## 🆘 Ayuda

1. **Instalación:** Lee [README_RUNPOD.md](README_RUNPOD.md#-instalación-local)
2. **Deploy:** Lee [README_RUNPOD.md](README_RUNPOD.md#-deploy-en-runpod)
3. **Problemas:** Lee [README_RUNPOD.md](README_RUNPOD.md#-troubleshooting)
4. **Comandos:** Lee [QUICKREF.md](QUICKREF.md)

## 📄 Licencia

Mismo que el proyecto Chat2SVG principal.

---

**¿Necesitas los otros stages?** Tendrás que implementar Stage 2 y 3 por separado. Esta API solo cubre la generación de plantillas (Stage 1).
