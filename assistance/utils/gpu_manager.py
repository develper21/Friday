"""
GPU Manager for Optimal Device Selection
Detects and optimizes GPU/CPU usage for ML operations
"""

import torch
import psutil
from typing import Optional


class GPUManager:
    """Manages GPU detection and optimization"""
    
    @staticmethod
    def get_optimal_device() -> str:
        """
        Detect and return optimal device for computation
        
        Returns:
            'cuda' if GPU available with sufficient memory, else 'cpu'
        """
        if torch.cuda.is_available():
            try:
                # Check GPU memory
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                free_memory = gpu_memory - torch.cuda.memory_allocated(0)
                
                # Require at least 2GB free memory
                if free_memory > 2 * 1024 * 1024 * 1024:
                    print(f"✓ GPU detected with {free_memory / (1024**3):.1f}GB free memory")
                    return "cuda"
                else:
                    print(f"⚠️ GPU available but insufficient memory ({free_memory / (1024**3):.1f}GB)")
            except Exception as e:
                print(f"⚠️ GPU detection error: {e}")
        
        print("Using CPU for computation")
        return "cpu"
    
    @staticmethod
    def get_memory_usage() -> dict:
        """
        Get current memory usage statistics
        
        Returns:
            Dictionary with CPU and GPU memory info
        """
        cpu_percent = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        
        result = {
            "cpu_percent": cpu_percent,
            "ram_used_gb": ram.used / (1024**3),
            "ram_total_gb": ram.total / (1024**3),
            "ram_percent": ram.percent
        }
        
        if torch.cuda.is_available():
            try:
                result["gpu_used_gb"] = torch.cuda.memory_allocated(0) / (1024**3)
                result["gpu_total_gb"] = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                result["gpu_percent"] = (result["gpu_used_gb"] / result["gpu_total_gb"]) * 100
            except Exception:
                pass
        
        return result
    
    @staticmethod
    def print_memory_stats():
        """Print current memory statistics"""
        stats = GPUManager.get_memory_usage()
        print("\n=== Memory Statistics ===")
        print(f"CPU Usage: {stats['cpu_percent']}%")
        print(f"RAM Usage: {stats['ram_used_gb']:.1f}GB / {stats['ram_total_gb']:.1f}GB ({stats['ram_percent']:.1f}%)")
        
        if "gpu_used_gb" in stats:
            print(f"GPU Usage: {stats['gpu_used_gb']:.1f}GB / {stats['gpu_total_gb']:.1f}GB ({stats['gpu_percent']:.1f}%)")
        print()
    
    @staticmethod
    def optimize_for_inference():
        """
        Optimize PyTorch settings for inference
        """
        if torch.cuda.is_available():
            # Enable cuDNN benchmarking for consistent input sizes
            torch.backends.cudnn.benchmark = True
            
            # Disable gradient calculation for inference
            torch.set_grad_enabled(False)
            
            print("✓ PyTorch optimized for GPU inference")
        else:
            print("Using CPU, PyTorch optimizations not applicable")
