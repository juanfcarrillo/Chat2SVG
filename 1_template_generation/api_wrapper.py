"""
API wrapper for the main.py functionality
Allows calling the stage 1 generation as a function instead of CLI
"""

import sys
import os
import yaml
import shutil
from typing import Dict, Optional

sys.path.append("../")

import utils.gpt as gpt
from utils.util import save, save_svg
import torch
import clip
import ImageReward as RM
import glob
from PIL import Image


class TemplateGenerator:
    """
    Class to handle SVG template generation with a functional API
    """
    
    def __init__(self, output_base_path: str = "../output"):
        """
        Initialize the template generator
        
        Args:
            output_base_path: Base path for output files
        """
        self.output_base_path = output_base_path
        
    def generate(
        self,
        target: str,
        prompt: str,
        output_folder: str = None,
        viewbox: int = 512,
        refine_iter: int = 2,
        model: str = "claude-3-5-sonnet-20240620",
        reward_model: str = "ImageReward",
        prompts_file: str = "prompts"
    ) -> Dict:
        """
        Generate SVG template from text prompt
        
        Args:
            target: Concept identifier (used for naming)
            prompt: Text description to generate SVG from
            output_folder: Optional custom output folder name
            viewbox: SVG viewbox size
            refine_iter: Number of refinement iterations
            model: LLM model to use
            reward_model: Model for ranking ("ImageReward" or "CLIP")
            prompts_file: Prompts configuration file
            
        Returns:
            Dictionary with generation results including paths and metadata
        """
        
        # Create config object similar to argparse args
        class Config:
            pass
        
        cfg = Config()
        cfg.target = target
        cfg.prompt = prompt
        cfg.viewbox = viewbox
        cfg.refine_iter = refine_iter
        cfg.model = model
        cfg.reward_model = reward_model
        cfg.prompts_file = prompts_file
        
        # Set up output directories
        if output_folder is None:
            output_folder = target
        
        cfg.root_dir = f"{self.output_base_path}/{output_folder}"
        cfg.output_folder = f"{cfg.root_dir}/stage_1"
        cfg.svg_dir = f"{cfg.output_folder}/svg_logs"
        cfg.png_dir = f"{cfg.output_folder}/png_logs"
        cfg.msg_dir = f"{cfg.output_folder}/raw_logs"
        
        for dir_p in [cfg.output_folder, cfg.svg_dir, cfg.png_dir, cfg.msg_dir]:
            os.makedirs(dir_p, exist_ok=True)
        
        # Save config
        with open(f"{cfg.output_folder}/config.yaml", "w", encoding="utf-8") as f:
            yaml.dump(cfg.__dict__, f)
        
        # Save prompts file
        prompts_source = f"../{prompts_file}.yaml"
        if os.path.exists(prompts_source):
            shutil.copyfile(prompts_source, f"{cfg.output_folder}/prompts.yaml")
        
        # Execute generation
        result = self._execute_generation(cfg)
        
        return result
    
    def _execute_generation(self, cfg) -> Dict:
        """
        Execute the actual SVG generation process
        
        Args:
            cfg: Configuration object
            
        Returns:
            Dictionary with results
        """
        session = gpt.Session(model=cfg.model, prompts_file=cfg.prompts_file)
        msg_path = lambda i: f"{cfg.msg_dir}/{cfg.target}_raw{i}"
        
        # Task 1: Expand the Text Prompt
        expanded_text_prompt = session.send(
            "expand_text_prompt",
            {"text_prompt": cfg.prompt},
            file_path=f"{cfg.msg_dir}/{cfg.target}_prompt",
        )
        save(f"{cfg.msg_dir}/{cfg.target}_prompt", expanded_text_prompt)
        
        # Task 2: Generate SVG Code
        svg_code = session.send("write_svg_code", file_path=msg_path(0))
        save(msg_path(0), svg_code)
        save_svg(cfg, svg_code, f"{cfg.target}_0")
        svg_path = f"{cfg.svg_dir}/{cfg.target}_0.svg"
        png_path = f"{cfg.png_dir}/{cfg.target}_0.png"
        
        # Task 3: Iterate Improvement
        for i in range(1, cfg.refine_iter + 1):
            svg_code = session.send("svg_refine", images=[png_path], file_path=msg_path(i))
            save(msg_path(i), svg_code)
            save_svg(cfg, svg_code, f"{cfg.target}_{i}")
            svg_path = f"{cfg.svg_dir}/{cfg.target}_{i}.svg"
            png_path = f"{cfg.png_dir}/{cfg.target}_{i}.png"
        
        # Automatically select the best SVG
        best_index = self._select_best_svg(cfg)
        
        result = {
            "success": True,
            "target": cfg.target,
            "best_index": best_index,
            "best_svg_path": f"{cfg.root_dir}/{cfg.target}_template.svg",
            "output_folder": cfg.output_folder,
            "svg_dir": cfg.svg_dir,
            "png_dir": cfg.png_dir,
            "expanded_prompt": expanded_text_prompt,
            "total_iterations": cfg.refine_iter + 1
        }
        
        return result
    
    def _select_best_svg(self, cfg) -> int:
        """
        Select the best SVG using reward model
        
        Args:
            cfg: Configuration object
            
        Returns:
            Index of the best SVG
        """
        model_name = cfg.reward_model
        assert model_name in [
            "ImageReward",
            "CLIP",
        ], "Only `ImageReward` and `CLIP` are supported"
        
        # Load appropriate model
        if model_name == "ImageReward":
            model = RM.load("ImageReward-v1.0")
        else:  # CLIP
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model, preprocess = clip.load("ViT-B/32", device=device)
        
        png_files = sorted(glob.glob(f"{cfg.png_dir}/*.png"))
        prompt = cfg.prompt
        
        # Get ranking based on selected model
        with torch.no_grad():
            if model_name == "ImageReward":
                ranking, _ = model.inference_rank(prompt, png_files)
                best_index = ranking[0] - 1  # ImageReward uses 1-based indexing
            else:  # CLIP
                device = next(model.parameters()).device
                
                images = torch.cat([
                    preprocess(Image.open(png_file)).unsqueeze(0)
                    for png_file in png_files
                ]).to(device)
                text = clip.tokenize([prompt]).to(device)
                
                image_features = model.encode_image(images)
                text_features = model.encode_text(text)
                image_features /= image_features.norm(dim=-1, keepdim=True)
                text_features /= text_features.norm(dim=-1, keepdim=True)
                
                similarity = (100.0 * image_features @ text_features.T).squeeze()
                best_index = similarity.argmax().item()
        
        # Copy the best SVG to the root directory
        best_svg = f"{cfg.target}_{best_index}.svg"
        print(f"The best SVG is: {best_svg}")
        shutil.copy(
            f"{cfg.svg_dir}/{best_svg}",
            f"{cfg.root_dir}/{cfg.target}_template.svg"
        )
        
        return best_index


def generate_template(
    target: str,
    prompt: str,
    output_folder: str = None,
    viewbox: int = 512,
    refine_iter: int = 2,
    model: str = "claude-3-5-sonnet-20240620",
    reward_model: str = "ImageReward",
    output_base_path: str = "../output",
    prompts_file: str = "prompts"
) -> Dict:
    """
    Convenience function to generate SVG template
    
    Args:
        target: Concept identifier
        prompt: Text description
        output_folder: Custom output folder name (optional)
        viewbox: SVG viewbox size
        refine_iter: Number of refinement iterations
        model: LLM model to use
        reward_model: Ranking model ("ImageReward" or "CLIP")
        output_base_path: Base path for outputs
        prompts_file: Prompts configuration file
        
    Returns:
        Dictionary with generation results
    """
    generator = TemplateGenerator(output_base_path=output_base_path)
    return generator.generate(
        target=target,
        prompt=prompt,
        output_folder=output_folder,
        viewbox=viewbox,
        refine_iter=refine_iter,
        model=model,
        reward_model=reward_model,
        prompts_file=prompts_file
    )


if __name__ == "__main__":
    # Example usage
    result = generate_template(
        target="test_cat",
        prompt="A cat sitting",
        refine_iter=2
    )
    print("Generation complete!")
    print(f"Best SVG: {result['best_svg_path']}")
