"""
Desktop App Setup Guidance Components
Provides UI components and endpoints for displaying LLM setup guidance.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)


class SetupGuidanceManager:
    """Manages setup guidance display in the web UI"""
    
    def __init__(self, templates: Jinja2Templates):
        self.templates = templates
        self.current_guidance: Optional[Dict[str, Any]] = None
        
    def set_setup_guidance(self, guidance_data: Dict[str, Any]):
        """Store setup guidance data for display"""
        self.current_guidance = guidance_data
        logger.info(f"Setup guidance set for {guidance_data.get('preferred_server', 'LLM')}")
        
    def get_setup_guidance(self) -> Optional[Dict[str, Any]]:
        """Get current setup guidance"""
        return self.current_guidance
        
    def clear_setup_guidance(self):
        """Clear setup guidance (when LLM is configured)"""
        self.current_guidance = None
        logger.info("Setup guidance cleared")
        
    def format_for_ui(self, guidance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format guidance data for UI display"""
        
        if not guidance_data:
            return {}
            
        # Extract key information
        preferred_server = guidance_data.get('preferred_server', 'LLM')
        system_specs = guidance_data.get('system_analysis', {})
        
        # Format for UI
        formatted = {
            'show_guidance': True,
            'title': f'Set up {preferred_server} for Local AI',
            'subtitle': 'Recommended based on your system specifications',
            'server_name': preferred_server,
            'benefits': [
                '🔒 Complete privacy - no data sent to cloud',
                '⚡ Fast responses - no internet required', 
                '💰 No API costs - run unlimited conversations',
                '🎛️ Full control - choose your preferred models'
            ],
            'system_info': {
                'ram': f"{system_specs.get('total_ram_gb', 'Unknown')}GB RAM",
                'cores': f"{system_specs.get('cpu_cores', 'Unknown')} CPU cores",
                'gpu': 'GPU Available' if system_specs.get('gpu_available') else 'No GPU detected'
            },
            'setup_steps': [],
            'download_url': '',
            'model_recommendations': []
        }
        
        # Add server-specific setup information
        if preferred_server.lower() == 'lm studio':
            formatted.update(self._get_lm_studio_setup(system_specs))
        elif preferred_server.lower() == 'ollama':
            formatted.update(self._get_ollama_setup(system_specs))
        else:
            formatted.update(self._get_generic_setup(preferred_server, system_specs))
            
        return formatted
        
    def _get_lm_studio_setup(self, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Get LM Studio specific setup guidance"""
        ram_gb = system_specs.get('total_ram_gb', 8)
        
        # Model recommendations based on RAM
        if ram_gb >= 32:
            models = ['Llama 3.1 8B Instruct', 'Llama 3.2 7B Instruct', 'Mistral 7B Instruct']
        elif ram_gb >= 16:
            models = ['Llama 3.2 3B Instruct', 'Phi 3 Mini', 'SmolLM2 1.7B']
        else:
            models = ['SmolLM2 1.7B', 'Phi 3 Mini', 'TinyLlama 1.1B']
            
        return {
            'download_url': 'https://lmstudio.ai/',
            'setup_steps': [
                'Download LM Studio from https://lmstudio.ai/',
                'Install and launch LM Studio',
                f'Browse models and download {models[0]} (recommended for your system)',
                'Load the model in the Chat tab',
                'Start the local server in the Developer tab',
                'Return to WhisperEngine - it will auto-detect the server!'
            ],
            'model_recommendations': [
                {
                    'name': models[0],
                    'description': 'Best balance of quality and performance for your system',
                    'size': '3-8GB',
                    'recommended': True
                },
                {
                    'name': models[1], 
                    'description': 'Faster alternative with good quality',
                    'size': '1-4GB',
                    'recommended': False
                }
            ]
        }
        
    def _get_ollama_setup(self, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Get Ollama specific setup guidance"""
        ram_gb = system_specs.get('total_ram_gb', 8)
        
        # Model recommendations based on RAM
        if ram_gb >= 32:
            main_model = 'llama3.1:8b'
        elif ram_gb >= 16:
            main_model = 'llama3.2:3b'
        else:
            main_model = 'smollm2:1.7b'
            
        return {
            'download_url': 'https://ollama.ai/',
            'setup_steps': [
                'Download Ollama from https://ollama.ai/',
                'Install Ollama',
                f'Open terminal and run: ollama pull {main_model}',
                'The model will download automatically',
                'Ollama starts serving automatically on localhost:11434',
                'Return to WhisperEngine - it will auto-detect Ollama!'
            ],
            'model_recommendations': [
                {
                    'name': main_model,
                    'description': 'Optimized for your system specifications',
                    'size': f'~{3 if "3b" in main_model else 1.7 if "1.7b" in main_model else 8}GB',
                    'recommended': True
                }
            ]
        }
        
    def _get_generic_setup(self, server_name: str, system_specs: Dict[str, Any]) -> Dict[str, Any]:
        """Get generic setup guidance"""
        return {
            'download_url': '',
            'setup_steps': [
                f'Download and install {server_name}',
                'Configure the server to run locally',
                'Start the server',
                'Return to WhisperEngine for auto-detection'
            ],
            'model_recommendations': []
        }


def add_setup_guidance_routes(app: FastAPI, templates: Jinja2Templates) -> SetupGuidanceManager:
    """Add setup guidance routes to FastAPI app"""
    
    guidance_manager = SetupGuidanceManager(templates)
    
    @app.get("/api/setup-guidance")
    async def get_setup_guidance():
        """Get current setup guidance data"""
        guidance = guidance_manager.get_setup_guidance()
        if guidance:
            return guidance_manager.format_for_ui(guidance)
        else:
            return {"show_guidance": False}
            
    @app.post("/api/setup-guidance/dismiss")
    async def dismiss_setup_guidance():
        """Dismiss setup guidance"""
        guidance_manager.clear_setup_guidance()
        return {"status": "dismissed"}
        
    @app.get("/setup")
    async def setup_page(request: Request):
        """Dedicated setup page"""
        guidance = guidance_manager.get_setup_guidance()
        formatted_guidance = guidance_manager.format_for_ui(guidance) if guidance else {}
        
        return templates.TemplateResponse("setup.html", {
            "request": request,
            "guidance": formatted_guidance
        })
    
    return guidance_manager