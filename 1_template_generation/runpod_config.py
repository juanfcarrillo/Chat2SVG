"""
RunPod Configuration and Setup
Contains configuration helpers and utilities for RunPod deployment
"""

import os
from typing import Dict, Any


class RunPodConfig:
    """Configuration class for RunPod serverless deployment"""
    
    # Default model configurations
    DEFAULT_MODEL = "claude-3-5-sonnet-20240620"
    DEFAULT_REWARD_MODEL = "ImageReward"
    DEFAULT_VIEWBOX = 512
    DEFAULT_REFINE_ITER = 2
    DEFAULT_PROMPTS_FILE = "prompts"
    
    # RunPod specific settings
    TIMEOUT_SECONDS = 600  # 10 minutes timeout for generation
    MAX_CONCURRENT_REQUESTS = 1  # Process one request at a time
    
    # Model preloading configuration
    PRELOAD_REWARD_MODEL = True  # Preload reward model on startup
    PRELOAD_CLIP_MODEL = False  # Set to True if using CLIP primarily
    
    @staticmethod
    def validate_input(job_input: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate input parameters
        
        Args:
            job_input: Input dictionary from RunPod
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check required parameters
        if "prompt" not in job_input:
            return False, "Missing required parameter: prompt"
        
        # Validate prompt is not empty
        if not job_input["prompt"].strip():
            return False, "Parameter 'prompt' cannot be empty"
        
        # Validate reward model if provided
        reward_model = job_input.get("reward_model", RunPodConfig.DEFAULT_REWARD_MODEL)
        if reward_model not in ["ImageReward", "CLIP"]:
            return False, f"Invalid reward_model: {reward_model}. Must be 'ImageReward' or 'CLIP'"
        
        # Validate numeric parameters
        viewbox = job_input.get("viewbox", RunPodConfig.DEFAULT_VIEWBOX)
        if not isinstance(viewbox, int) or viewbox <= 0:
            return False, f"Invalid viewbox: {viewbox}. Must be a positive integer"
        
        refine_iter = job_input.get("refine_iter", RunPodConfig.DEFAULT_REFINE_ITER)
        if not isinstance(refine_iter, int) or refine_iter < 0:
            return False, f"Invalid refine_iter: {refine_iter}. Must be a non-negative integer"
        
        if refine_iter > 10:
            return False, f"refine_iter too high: {refine_iter}. Maximum is 10 to prevent timeouts"
        
        return True, ""
    
    @staticmethod
    def get_default_params() -> Dict[str, Any]:
        """
        Get default parameters for SVG generation
        
        Returns:
            Dictionary with default parameters
        """
        return {
            "model": RunPodConfig.DEFAULT_MODEL,
            "reward_model": RunPodConfig.DEFAULT_REWARD_MODEL,
            "viewbox": RunPodConfig.DEFAULT_VIEWBOX,
            "refine_iter": RunPodConfig.DEFAULT_REFINE_ITER,
            "prompts_file": RunPodConfig.DEFAULT_PROMPTS_FILE,
            "target": "generated"
        }
    
    @staticmethod
    def merge_with_defaults(job_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user input with default parameters
        
        Args:
            job_input: User provided parameters
            
        Returns:
            Complete parameter dictionary
        """
        defaults = RunPodConfig.get_default_params()
        defaults.update(job_input)
        return defaults


def check_environment() -> Dict[str, Any]:
    """
    Check if required environment variables are set
    
    Returns:
        Dictionary with environment status
    """
    required_vars = ["ANTHROPIC_API_KEY", "BACKEND"]
    optional_vars = ["OPENAI_API_KEY"]
    
    status = {
        "all_required_set": True,
        "missing_required": [],
        "optional_set": {},
        "backend": None
    }
    
    # Check required variables
    for var in required_vars:
        if not os.getenv(var):
            status["all_required_set"] = False
            status["missing_required"].append(var)
    
    # Check optional variables
    for var in optional_vars:
        status["optional_set"][var] = os.getenv(var) is not None
    
    # Get backend
    status["backend"] = os.getenv("BACKEND")
    
    return status


def format_error_response(error: Exception, context: str = "") -> Dict[str, Any]:
    """
    Format error response for RunPod
    
    Args:
        error: Exception that occurred
        context: Additional context about the error
        
    Returns:
        Formatted error dictionary
    """
    import traceback
    
    return {
        "success": False,
        "error": str(error),
        "error_type": type(error).__name__,
        "context": context,
        "traceback": traceback.format_exc()
    }


def get_system_info() -> Dict[str, Any]:
    """
    Get system information for debugging
    
    Returns:
        Dictionary with system info
    """
    import torch
    import sys
    
    info = {
        "python_version": sys.version,
        "cuda_available": torch.cuda.is_available(),
        "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    }
    
    if torch.cuda.is_available():
        info["device_name"] = torch.cuda.get_device_name(0)
        info["device_capability"] = torch.cuda.get_device_capability(0)
    
    return info


if __name__ == "__main__":
    # Test configuration
    print("RunPod Configuration Test")
    print("=" * 50)
    
    print("\nDefault Parameters:")
    defaults = RunPodConfig.get_default_params()
    for key, value in defaults.items():
        print(f"  {key}: {value}")
    
    print("\nEnvironment Check:")
    env_status = check_environment()
    print(f"  All required variables set: {env_status['all_required_set']}")
    if env_status['missing_required']:
        print(f"  Missing: {', '.join(env_status['missing_required'])}")
    print(f"  Backend: {env_status['backend']}")
    
    print("\nSystem Info:")
    sys_info = get_system_info()
    for key, value in sys_info.items():
        print(f"  {key}: {value}")
    
    print("\nValidation Tests:")
    test_cases = [
        {"prompt": "A cat"},  # Valid
        {},  # Missing prompt
        {"prompt": "", "refine_iter": 2},  # Empty prompt
        {"prompt": "A dog", "reward_model": "Invalid"},  # Invalid reward model
        {"prompt": "A bird", "refine_iter": -1},  # Invalid refine_iter
    ]
    
    for i, test_input in enumerate(test_cases, 1):
        is_valid, error = RunPodConfig.validate_input(test_input)
        status = "✓ VALID" if is_valid else f"✗ INVALID: {error}"
        print(f"  Test {i}: {status}")
