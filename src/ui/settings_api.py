"""
Desktop App Settings API Routes
FastAPI routes for managing desktop app settings.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src.config.desktop_settings import DesktopSettingsManager

logger = logging.getLogger(__name__)


# Pydantic models for API requests
class SystemPromptRequest(BaseModel):
    name: str
    content: str
    set_active: bool = False


class LLMConfigRequest(BaseModel):
    api_url: str
    api_key: str
    model_name: str = ""


class DiscordConfigRequest(BaseModel):
    bot_token: str


class UIPreferenceRequest(BaseModel):
    key: str
    value: Any


class SettingsAPIManager:
    """Manages settings API endpoints"""
    
    def __init__(self, settings_manager: DesktopSettingsManager, templates: Jinja2Templates):
        self.settings_manager = settings_manager
        self.templates = templates
        
    def add_routes(self, app: FastAPI):
        """Add settings routes to FastAPI app"""
        
        # Settings page
        @app.get("/settings", response_class=HTMLResponse)
        async def settings_page(request: Request):
            """Serve the settings page"""
            try:
                # Get all current settings
                system_prompt_config = self.settings_manager.get_system_prompt_config()
                llm_config = self.settings_manager.get_llm_config()
                discord_config = self.settings_manager.get_discord_config()
                ui_preferences = self.settings_manager.get_ui_preferences()
                
                # Get additional data
                uploaded_prompts = self.settings_manager.get_uploaded_prompts()
                active_prompt_content = self.settings_manager.get_active_system_prompt()
                
                context = {
                    "request": request,
                    "system_prompt_config": system_prompt_config,
                    "llm_config": llm_config,
                    "discord_config": discord_config,
                    "ui_preferences": ui_preferences,
                    "uploaded_prompts": uploaded_prompts,
                    "active_prompt_content": active_prompt_content[:500] + "..." if len(active_prompt_content) > 500 else active_prompt_content
                }
                
                return self.templates.TemplateResponse("settings.html", context)
                
            except Exception as e:
                logger.error(f"Settings page error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # System prompt APIs
        @app.get("/api/settings/system-prompt")
        async def get_system_prompt_config():
            """Get system prompt configuration"""
            try:
                config = self.settings_manager.get_system_prompt_config()
                config["active_content"] = self.settings_manager.get_active_system_prompt()
                config["uploaded_prompts"] = self.settings_manager.get_uploaded_prompts()
                return config
            except Exception as e:
                logger.error(f"Get system prompt config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/system-prompt/custom")
        async def save_custom_prompt(request: SystemPromptRequest):
            """Save a custom system prompt"""
            try:
                success = self.settings_manager.save_custom_prompt(request.name, request.content)
                
                if request.set_active and success:
                    self.settings_manager.set_active_prompt("custom", request.name)
                
                if success:
                    return {"status": "success", "message": "Custom prompt saved"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to save prompt")
                    
            except Exception as e:
                logger.error(f"Save custom prompt error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/system-prompt/upload")
        async def upload_prompt_file(file: UploadFile = File(...), set_active: bool = Form(False)):
            """Upload a system prompt file"""
            try:
                if not file.filename or not file.filename.endswith('.txt'):
                    raise HTTPException(status_code=400, detail="Only .txt files are allowed")
                
                content = await file.read()
                content_str = content.decode('utf-8')
                
                success = self.settings_manager.upload_prompt_file(file.filename, content_str)
                
                if set_active and success:
                    self.settings_manager.set_active_prompt("uploaded", file.filename)
                
                if success:
                    return {"status": "success", "message": f"Prompt file {file.filename} uploaded"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to upload prompt file")
                    
            except Exception as e:
                logger.error(f"Upload prompt file error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/system-prompt/set-active")
        async def set_active_prompt(request: Request):
            """Set the active system prompt"""
            try:
                data = await request.json()
                source = data.get("source")
                prompt_name = data.get("prompt_name")
                
                if not source or not prompt_name:
                    raise HTTPException(status_code=400, detail="Source and prompt_name are required")
                
                success = self.settings_manager.set_active_prompt(source, prompt_name)
                
                if success:
                    return {"status": "success", "message": "Active prompt updated"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to set active prompt")
                    
            except Exception as e:
                logger.error(f"Set active prompt error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.delete("/api/settings/system-prompt/custom/{prompt_name}")
        async def delete_custom_prompt(prompt_name: str):
            """Delete a custom prompt"""
            try:
                success = self.settings_manager.delete_custom_prompt(prompt_name)
                
                if success:
                    return {"status": "success", "message": f"Prompt '{prompt_name}' deleted"}
                else:
                    raise HTTPException(status_code=404, detail="Prompt not found")
                    
            except Exception as e:
                logger.error(f"Delete custom prompt error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # LLM configuration APIs
        @app.get("/api/settings/llm-config")
        async def get_llm_config():
            """Get LLM configuration"""
            try:
                config = self.settings_manager.get_llm_config()
                # Don't return the API key in full for security
                if config["api_key"]:
                    config["api_key_masked"] = "*" * (len(config["api_key"]) - 4) + config["api_key"][-4:]
                else:
                    config["api_key_masked"] = ""
                return config
            except Exception as e:
                logger.error(f"Get LLM config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/llm-config")
        async def set_llm_config(request: LLMConfigRequest):
            """Set LLM configuration"""
            try:
                success = self.settings_manager.set_llm_config(
                    request.api_url, 
                    request.api_key, 
                    request.model_name
                )
                
                if success:
                    return {"status": "success", "message": "LLM configuration updated"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to update LLM configuration")
                    
            except Exception as e:
                logger.error(f"Set LLM config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/llm-config/validate")
        async def validate_llm_config():
            """Validate LLM configuration and fetch models"""
            try:
                result = await self.settings_manager.validate_llm_config()
                return result
            except Exception as e:
                logger.error(f"Validate LLM config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Discord configuration APIs
        @app.get("/api/settings/discord-config")
        async def get_discord_config():
            """Get Discord configuration"""
            try:
                config = self.settings_manager.get_discord_config()
                # Don't return the token in full for security
                if config["bot_token"]:
                    config["bot_token_masked"] = "*" * (len(config["bot_token"]) - 8) + config["bot_token"][-8:]
                else:
                    config["bot_token_masked"] = ""
                return config
            except Exception as e:
                logger.error(f"Get Discord config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/discord-config")
        async def set_discord_config(request: DiscordConfigRequest):
            """Set Discord configuration"""
            try:
                success = self.settings_manager.set_discord_token(request.bot_token)
                
                if success:
                    return {"status": "success", "message": "Discord configuration updated"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to update Discord configuration")
                    
            except Exception as e:
                logger.error(f"Set Discord config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/discord-config/validate")
        async def validate_discord_config():
            """Validate Discord configuration"""
            try:
                result = await self.settings_manager.validate_discord_token()
                return result
            except Exception as e:
                logger.error(f"Validate Discord config error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # UI preferences APIs
        @app.get("/api/settings/ui-preferences")
        async def get_ui_preferences():
            """Get UI preferences"""
            try:
                return self.settings_manager.get_ui_preferences()
            except Exception as e:
                logger.error(f"Get UI preferences error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/ui-preferences")
        async def set_ui_preference(request: UIPreferenceRequest):
            """Set a UI preference"""
            try:
                success = self.settings_manager.set_ui_preference(request.key, request.value)
                
                if success:
                    return {"status": "success", "message": "UI preference updated"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to update UI preference")
                    
            except Exception as e:
                logger.error(f"Set UI preference error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        # Export/Import APIs
        @app.get("/api/settings/export")
        async def export_settings():
            """Export all settings"""
            try:
                settings_data = self.settings_manager.export_settings()
                return {"status": "success", "data": settings_data}
            except Exception as e:
                logger.error(f"Export settings error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @app.post("/api/settings/import")
        async def import_settings(request: Request):
            """Import settings"""
            try:
                data = await request.json()
                settings_data = data.get("data")
                
                if not settings_data:
                    raise HTTPException(status_code=400, detail="Settings data is required")
                
                success = self.settings_manager.import_settings(settings_data)
                
                if success:
                    return {"status": "success", "message": "Settings imported successfully"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to import settings")
                    
            except Exception as e:
                logger.error(f"Import settings error: {e}")
                raise HTTPException(status_code=500, detail=str(e))


def add_settings_routes(app: FastAPI, templates: Jinja2Templates) -> DesktopSettingsManager:
    """Add settings routes to FastAPI app and return settings manager"""
    settings_manager = DesktopSettingsManager()
    api_manager = SettingsAPIManager(settings_manager, templates)
    api_manager.add_routes(app)
    
    return settings_manager