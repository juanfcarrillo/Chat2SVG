"""
RunPod Serverless Handler for Chat2SVG Stage 1 - Template Generation
This handler provides a serverless API endpoint for generating SVG templates.
"""

import runpod
import os
import sys
import tempfile
import shutil
import base64
from pathlib import Path
import yaml

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils.gpt as gpt
from utils.util import save, save_svg, extract_svg
import torch
import clip
import ImageReward as RM
import glob
from PIL import Image


class SVGGenerator:
    """Handler class for SVG generation"""
    
    def __init__(self):
        """Initialize models and session"""
        self.session = None
        self.reward_model = None
        self.reward_model_name = None
        
    def initialize_session(self, model: str, prompts_file: str = "prompts"):
        """Initialize GPT session"""
        if self.session is None or self.session.model != model:
            self.session = gpt.Session(model=model, prompts_file=prompts_file)
    
    def initialize_reward_model(self, model_name: str = "ImageReward"):
        """Initialize reward model for ranking"""
        if self.reward_model is None or self.reward_model_name != model_name:
            if model_name == "ImageReward":
                self.reward_model = RM.load("ImageReward-v1.0")
            else:  # CLIP
                device = "cuda" if torch.cuda.is_available() else "cpu"
                self.reward_model, self.preprocess = clip.load("ViT-B/32", device=device)
            self.reward_model_name = model_name
    
    def select_best_svg(self, svg_dir: str, png_dir: str, prompt: str, target: str, model_name: str = "ImageReward"):
        """Select the best SVG based on reward model"""
        self.initialize_reward_model(model_name)
        
        png_files = sorted(glob.glob(f"{png_dir}/*.png"))
        
        if not png_files:
            raise ValueError("No PNG files found for ranking")
        
        # Get ranking based on selected model
        with torch.no_grad():
            if model_name == "ImageReward":
                ranking, _ = self.reward_model.inference_rank(prompt, png_files)
                best_index = ranking[0] - 1
            else:  # CLIP
                device = next(self.reward_model.parameters()).device
                
                images = torch.cat([
                    self.preprocess(Image.open(png_file)).unsqueeze(0)
                    for png_file in png_files
                ]).to(device)
                text = clip.tokenize([prompt]).to(device)
                
                image_features = self.reward_model.encode_image(images)
                text_features = self.reward_model.encode_text(text)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
                similarity = (100.0 * image_features @ text_features.T).squeeze()
                best_index = similarity.argmax().item()
        
        best_svg_path = f"{svg_dir}/{target}_{best_index}.svg"
        return best_svg_path, best_index
    
    def generate_svg(
        self,
        prompt: str,
        target: str = "generated",
        viewbox: int = 512,
        refine_iter: int = 2,
        model: str = "claude-3-5-sonnet-20240620",
        reward_model: str = "ImageReward",
        prompts_file: str = "prompts"
    ):
        """
        Generate SVG template from text prompt
        
        Args:
            prompt: Text description of the SVG to generate
            target: Name identifier for the output
            viewbox: SVG viewbox size (default: 512)
            refine_iter: Number of refinement iterations (default: 2)
            model: LLM model to use (default: claude-3-5-sonnet-20240620)
            reward_model: Reward model for selection (ImageReward or CLIP)
            prompts_file: Prompts file to use (default: prompts)
            
        Returns:
            dict with SVG content and metadata
        """
        
        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up directories
            svg_dir = os.path.join(temp_dir, "svg_logs")
            png_dir = os.path.join(temp_dir, "png_logs")
            msg_dir = os.path.join(temp_dir, "raw_logs")
            
            for dir_p in [svg_dir, png_dir, msg_dir]:
                os.makedirs(dir_p, exist_ok=True)
            
            # Create config object
            class Config:
                def __init__(self):
                    self.prompt = prompt
                    self.target = target
                    self.viewbox = viewbox
                    self.refine_iter = refine_iter
                    self.model = model
                    self.reward_model = reward_model
                    self.svg_dir = svg_dir
                    self.png_dir = png_dir
                    self.msg_dir = msg_dir
            
            cfg = Config()
            
            # Initialize session
            self.initialize_session(model, prompts_file)
            
            msg_path = lambda i: f"{msg_dir}/{target}_raw{i}"
            
            # Task 1: Expand the text prompt
            print(f"Expanding prompt: {prompt}")
            expanded_text_prompt = self.session.send(
                "expand_text_prompt",
                {"text_prompt": prompt},
                file_path=f"{msg_dir}/{target}_prompt",
            )
            save(f"{msg_dir}/{target}_prompt", expanded_text_prompt)
            
            # Task 2: Generate initial SVG code
            print("Generating initial SVG...")
            svg_code = self.session.send("write_svg_code", file_path=msg_path(0))
            save(msg_path(0), svg_code)
            save_svg(cfg, svg_code, f"{target}_0")
            png_path = f"{png_dir}/{target}_0.png"
            
            # Task 3: Iterate improvements
            for i in range(1, refine_iter + 1):
                print(f"Refining SVG iteration {i}/{refine_iter}...")
                svg_code = self.session.send("svg_refine", images=[png_path], file_path=msg_path(i))
                save(msg_path(i), svg_code)
                save_svg(cfg, svg_code, f"{target}_{i}")
                png_path = f"{png_dir}/{target}_{i}.png"
            
            # Select best SVG
            print(f"Selecting best SVG using {reward_model}...")
            best_svg_path, best_index = self.select_best_svg(
                svg_dir, png_dir, prompt, target, reward_model
            )
            
            # Read the best SVG
            with open(best_svg_path, 'r') as f:
                best_svg_content = f.read()
            
            # Read the best PNG and encode to base64
            best_png_path = f"{png_dir}/{target}_{best_index}.png"
            with open(best_png_path, 'rb') as f:
                best_png_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Collect all SVG iterations
            all_svgs = []
            for i in range(refine_iter + 1):
                svg_path = f"{svg_dir}/{target}_{i}.svg"
                if os.path.exists(svg_path):
                    with open(svg_path, 'r') as f:
                        all_svgs.append({
                            "iteration": i,
                            "svg_content": f.read()
                        })
            
            return {
                "success": True,
                "best_svg": best_svg_content,
                "best_index": best_index,
                "best_png_base64": best_png_base64,
                "all_iterations": all_svgs,
                "metadata": {
                    "prompt": prompt,
                    "expanded_prompt": expanded_text_prompt,
                    "target": target,
                    "model": model,
                    "reward_model": reward_model,
                    "refine_iterations": refine_iter,
                    "total_generated": len(all_svgs)
                }
            }


# Initialize generator
generator = SVGGenerator()


def handler(event):
    """
    RunPod handler function
    
    Expected input format:
    {
        "input": {
            "prompt": "A cat sitting",  # Required
            "target": "cat",  # Optional, default: "generated"
            "viewbox": 512,  # Optional, default: 512
            "refine_iter": 2,  # Optional, default: 2
            "model": "claude-3-5-sonnet-20240620",  # Optional
            "reward_model": "ImageReward",  # Optional: "ImageReward" or "CLIP"
            "prompts_file": "prompts"  # Optional, default: "prompts"
        }
    }
    
    Returns:
    {
        "success": True,
        "best_svg": "<svg>...</svg>",
        "best_index": 0,
        "best_png_base64": "base64_encoded_image",
        "all_iterations": [...],
        "metadata": {...}
    }
    """
    try:
        # Extract input parameters
        job_input = event.get("input", {})
        
        # Validate required parameters
        if "prompt" not in job_input:
            return {
                "error": "Missing required parameter: prompt",
                "success": False
            }
        
        prompt = job_input["prompt"]
        target = job_input.get("target", "generated")
        viewbox = job_input.get("viewbox", 512)
        refine_iter = job_input.get("refine_iter", 2)
        model = job_input.get("model", "claude-3-5-sonnet-20240620")
        reward_model = job_input.get("reward_model", "ImageReward")
        prompts_file = job_input.get("prompts_file", "prompts")
        
        # Validate parameters
        if reward_model not in ["ImageReward", "CLIP"]:
            return {
                "error": f"Invalid reward_model: {reward_model}. Must be 'ImageReward' or 'CLIP'",
                "success": False
            }
        
        # Generate SVG
        result = generator.generate_svg(
            prompt=prompt,
            target=target,
            viewbox=viewbox,
            refine_iter=refine_iter,
            model=model,
            reward_model=reward_model,
            prompts_file=prompts_file
        )
        
        return result
        
    except Exception as e:
        import traceback
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "success": False
        }


if __name__ == "__main__":
    # Start the RunPod serverless worker
    print("Starting RunPod serverless worker for Chat2SVG Stage 1...")
    runpod.serverless.start({"handler": handler})
