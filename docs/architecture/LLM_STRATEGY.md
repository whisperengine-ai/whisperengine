# WhisperEngine LLM Integration Strategy

## 🎯 **Overview**

This document outlines WhisperEngine's strategy for Local Large Language Model (LLM) integration across desktop and cloud deployment modes. The approach prioritizes user experience, resource efficiency, and maintainability.

## 📋 **Current Architecture Status**

### **HTTP API-Based Approach (Current)**
WhisperEngine currently uses an **HTTP API abstraction layer** for all LLM interactions:

```python
# src/llm/llm_client.py - Universal HTTP client
class LLMClient:
    """Generic client for connecting to various LLM services via HTTP API"""
    
    # Supported providers:
    # - LM Studio (local): http://localhost:1234/v1
    # - Ollama (local): http://localhost:11434/v1  
    # - OpenRouter (cloud): https://openrouter.ai/api/v1
    # - Any OpenAI-compatible API endpoint
```

### **Current Components:**
- ✅ **Main LLM**: HTTP API calls via `LLMClient`
- ✅ **Embeddings**: Direct Python loading via ChromaDB + SentenceTransformers
- ✅ **Emotion AI**: HTTP API calls (same infrastructure as main LLM)
- ✅ **Memory Systems**: Local ChromaDB + Redis caching

---

## 🎯 **Recommended Strategy: Enhanced HTTP API Approach**

### **Decision: Keep HTTP API as Primary Method**

**Rationale:**
1. **Proven Architecture** - Current system is functional and tested
2. **Resource Efficiency** - LLMs run in optimized separate processes
3. **User Flexibility** - Users can choose their preferred local LLM server
4. **Maintenance Simplicity** - No PyTorch/CUDA dependency management
5. **GPU Memory Management** - External servers handle GPU allocation efficiently

### **Enhancement Areas:**
1. **Auto-Detection & Setup Guidance**
2. **Intelligent Fallback Chains**
3. **Resource-Aware Recommendations**
4. **Seamless Desktop Experience**

---

## 🏗️ **Implementation Plan**

### **Phase 1: Enhanced HTTP API (Immediate - v1.0)**

#### **1.1 Auto-Detection System**
```python
# src/llm/local_server_detector.py (NEW)
class LocalLLMDetector:
    """Automatically detect and connect to local LLM servers"""
    
    def detect_available_servers(self) -> Dict[str, ServerInfo]:
        """Scan for LM Studio, Ollama, and other local servers"""
        servers = {}
        
        # Check LM Studio (port 1234)
        if self._test_connection("http://localhost:1234/v1"):
            servers['lm_studio'] = ServerInfo(
                name="LM Studio",
                url="http://localhost:1234/v1",
                status="available",
                models=self._get_available_models("http://localhost:1234/v1")
            )
        
        # Check Ollama (port 11434)
        if self._test_connection("http://localhost:11434/v1"):
            servers['ollama'] = ServerInfo(
                name="Ollama", 
                url="http://localhost:11434/v1",
                status="available",
                models=self._get_available_models("http://localhost:11434/v1")
            )
            
        return servers
    
    def get_recommended_setup(self, resources: ResourceInfo) -> SetupRecommendation:
        """Provide setup recommendations based on system resources"""
        if resources.memory_gb >= 16 and resources.gpu_available:
            return SetupRecommendation(
                preferred_server="LM Studio",
                recommended_models=["llama-3.1-8b", "mistral-7b"],
                setup_url="https://lmstudio.ai/",
                memory_note="Your system can handle larger models (7B-13B)"
            )
        elif resources.memory_gb >= 8:
            return SetupRecommendation(
                preferred_server="Ollama",
                recommended_models=["llama-3.2-3b", "phi-3-mini"],
                setup_url="https://ollama.ai/",
                memory_note="Recommend smaller models (3B-7B) for your system"
            )
        else:
            return SetupRecommendation(
                preferred_server="OpenRouter",
                recommended_models=["cloud-based"],
                setup_url="https://openrouter.ai/",
                memory_note="Cloud API recommended - no local requirements"
            )
```

#### **1.2 Enhanced Web-UI Application Integration**
```python
# universal_native_app.py - Enhanced startup
class WhisperEngineWebUIApp:
    def __init__(self):
        self.llm_detector = LocalLLMDetector()
        self.setup_assistant = LLMSetupAssistant()
        
    async def startup_sequence(self):
        """Enhanced startup with LLM detection and setup guidance"""
        
        # 1. Detect system resources
        resources = EnvironmentDetector.detect_resources()
        
        # 2. Scan for available LLM servers
        available_servers = self.llm_detector.detect_available_servers()
        
        # 3. Configure or guide setup
        if available_servers:
            # Use best available server
            best_server = self._select_best_server(available_servers, resources)
            self._configure_llm_client(best_server)
            self.logger.info(f"Connected to {best_server.name}")
        else:
            # Guide user through setup
            recommendation = self.llm_detector.get_recommended_setup(resources)
            self.setup_assistant.show_setup_guidance(recommendation)
            
        # 4. Start web UI with LLM status
        await self.start_web_ui()
```

#### **1.3 Intelligent Fallback Chain**
```python
# src/llm/llm_client.py - Enhanced with fallbacks
class LLMClient:
    def __init__(self):
        self.fallback_chain = [
            "http://localhost:1234/v1",  # LM Studio
            "http://localhost:11434/v1", # Ollama
            "https://openrouter.ai/api/v1" # Cloud fallback
        ]
        
    async def chat_completion(self, messages, **kwargs):
        """Try servers in fallback order"""
        last_error = None
        
        for server_url in self.fallback_chain:
            try:
                if self._is_server_available(server_url):
                    response = await self._make_request(server_url, messages, **kwargs)
                    return response
            except Exception as e:
                last_error = e
                continue
                
        # All servers failed - provide helpful guidance
        raise LLMConnectionError(
            "No LLM servers available. Please set up LM Studio, Ollama, or OpenRouter API key.",
            setup_guidance=self._get_setup_guidance(),
            last_error=last_error
        )
```

#### **1.4 Setup Assistant Web UI**
```python
# src/ui/setup_assistant.py (NEW)
class LLMSetupAssistant:
    """Interactive setup guidance for LLM backends"""
    
    def show_setup_guidance(self, recommendation: SetupRecommendation):
        """Display setup instructions in web UI"""
        guidance = {
            "status": "setup_required",
            "recommendation": recommendation,
            "steps": self._generate_setup_steps(recommendation),
            "download_links": self._get_download_links(recommendation),
            "test_connection": "/api/test-llm-connection"
        }
        
        # Store guidance for web UI to display
        self._store_setup_state(guidance)
        
    def _generate_setup_steps(self, recommendation: SetupRecommendation) -> List[str]:
        """Generate step-by-step setup instructions"""
        if recommendation.preferred_server == "LM Studio":
            return [
                "1. Download LM Studio from https://lmstudio.ai/",
                "2. Install and launch LM Studio",
                "3. Download a recommended model (e.g., Llama 3.1 8B)",
                "4. Start the local server (default port 1234)",
                "5. Return to WhisperEngine - it will auto-detect the server"
            ]
        # Similar for Ollama, OpenRouter...
```

### **Phase 2: Advanced Features (Future - v1.1+)**

#### **2.1 Optional Direct Python Loading**
```python
# src/llm/direct_llm_loader.py (FUTURE)
class DirectLLMLoader:
    """Optional direct model loading for advanced users"""
    
    def __init__(self):
        self.enabled = os.getenv("WHISPER_ENABLE_DIRECT_LLM", "false").lower() == "true"
        self.model_cache_dir = Path.home() / ".whisperengine" / "models"
        
    def load_model_directly(self, model_name: str):
        """Load model directly with transformers (optional feature)"""
        if not self.enabled:
            raise FeatureNotEnabledError("Direct LLM loading disabled")
            
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            import torch
            
            # Load model and tokenizer
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                cache_dir=self.model_cache_dir,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
            )
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            
            return DirectLLMWrapper(model, tokenizer)
            
        except ImportError:
            raise DependencyError("transformers and torch required for direct loading")
```

#### **2.2 Hybrid Mode**
```python
# src/llm/hybrid_llm_manager.py (FUTURE)
class HybridLLMManager:
    """Manages both HTTP API and direct loading modes"""
    
    def __init__(self):
        self.http_client = LLMClient()
        self.direct_loader = DirectLLMLoader() if DirectLLMLoader.is_available() else None
        self.mode = self._determine_best_mode()
        
    def _determine_best_mode(self) -> str:
        """Choose best LLM mode based on available resources and user preference"""
        user_preference = os.getenv("WHISPER_LLM_MODE", "auto")
        
        if user_preference == "direct" and self.direct_loader:
            return "direct"
        elif user_preference == "http":
            return "http"
        else:  # auto
            # Prefer HTTP if servers available, fallback to direct
            if self.http_client.has_available_servers():
                return "http"
            elif self.direct_loader and self.direct_loader.enabled:
                return "direct"
            else:
                return "http"  # Will guide user to setup
```

---

## 🔧 **Configuration Strategy**

### **Environment Variables**
```bash
# Primary LLM configuration (current)
LLM_CHAT_API_URL=http://localhost:1234/v1
LLM_CHAT_API_KEY=your_openrouter_key_here
LLM_MODEL_NAME=llama-3.1-8b-instruct

# Enhanced configuration (new)
WHISPER_LLM_AUTO_DETECT=true
WHISPER_LLM_FALLBACK_CHAIN=lm_studio,ollama,openrouter
WHISPER_SHOW_SETUP_GUIDANCE=true

# Future: Direct loading mode (optional)
WHISPER_ENABLE_DIRECT_LLM=false
WHISPER_LLM_MODE=auto  # auto, http, direct
WHISPER_MODEL_CACHE_DIR=~/.whisperengine/models
```

### **Adaptive Configuration**
```python
# src/config/adaptive_config.py - Enhanced LLM config
class AdaptiveConfigManager:
    def get_llm_configuration(self) -> LLMConfiguration:
        """Get optimized LLM configuration based on resources and environment"""
        resources = self.detect_resources()
        
        return LLMConfiguration(
            preferred_mode="http",  # Always prefer HTTP API
            auto_detect_servers=True,
            fallback_chain=self._build_fallback_chain(resources),
            setup_guidance_enabled=True,
            resource_recommendations=self._get_resource_recommendations(resources)
        )
    
    def _build_fallback_chain(self, resources: ResourceInfo) -> List[str]:
        """Build intelligent fallback chain based on system capabilities"""
        chain = []
        
        # Always try local servers first
        chain.extend(["lm_studio", "ollama"])
        
        # Add cloud fallback if API key available
        if os.getenv("LLM_CHAT_API_KEY"):
            chain.append("openrouter")
            
        return chain
```

---

## 📊 **Performance Considerations**

### **Memory Usage Patterns**
```
Web-UI Application Modes:
├── HTTP API Mode (Recommended)
│   ├── WhisperEngine App: ~200-500MB
│   ├── LM Studio/Ollama: ~4-16GB (depending on model)
│   └── Total: ~4.2-16.5GB
└── Direct Loading Mode (Future)
    ├── WhisperEngine + Model: ~4-16GB
    └── Total: ~4-16GB (but less efficient)
```

### **Startup Time Analysis**
```
HTTP API Mode:
├── App Startup: ~2-5 seconds
├── Server Detection: ~1-2 seconds  
├── First Request: ~1-3 seconds (model already loaded)
└── Total Ready Time: ~4-10 seconds

Direct Loading Mode (Future):
├── App Startup: ~2-5 seconds
├── Model Loading: ~30-120 seconds (first time)
├── First Request: ~1-2 seconds
└── Total Ready Time: ~33-127 seconds
```

---

## 🛠️ **Implementation Timeline**

### **Phase 1: Enhanced HTTP API (Target: 2-3 weeks)**
- [ ] **Week 1**: Auto-detection system and setup assistant
- [ ] **Week 2**: Enhanced web-UI application integration and fallback chains
- [ ] **Week 3**: Web UI setup guidance and testing

### **Phase 2: Advanced Features (Target: Future releases)**
- [ ] **Optional Direct Loading**: For advanced users who want single-process mode
- [ ] **Hybrid Mode**: Intelligent switching between HTTP and direct
- [ ] **Model Marketplace**: Easy model download and management

---

## 🧪 **Testing Strategy**

### **Test Scenarios**
1. **Fresh Install**: No LLM servers installed
2. **LM Studio Available**: LM Studio running with models
3. **Ollama Available**: Ollama running with models  
4. **Multiple Servers**: Both LM Studio and Ollama available
5. **Cloud Only**: No local servers, OpenRouter API key
6. **No Configuration**: No servers or API keys

### **Validation Checklist**
- [ ] Auto-detection finds available servers
- [ ] Setup guidance appears when needed
- [ ] Fallback chain works correctly
- [ ] Performance is acceptable
- [ ] Error messages are helpful
- [ ] Resource recommendations are accurate

---

## 📚 **References & Resources**

### **Local LLM Servers**
- **LM Studio**: https://lmstudio.ai/ - User-friendly GUI for local models
- **Ollama**: https://ollama.ai/ - Command-line local model runner
- **text-generation-webui**: https://github.com/oobabooga/text-generation-webui

### **Cloud APIs**
- **OpenRouter**: https://openrouter.ai/ - Access to multiple model providers
- **OpenAI**: https://openai.com/api/ - GPT models
- **Anthropic**: https://anthropic.com/ - Claude models

### **Model Recommendations by System Specs**
```
16GB+ RAM + GPU:
├── Llama 3.1 8B Instruct
├── Mistral 7B Instruct  
└── CodeLlama 7B

8-16GB RAM:
├── Llama 3.2 3B Instruct
├── Phi-3 Mini
└── Gemma 2B

<8GB RAM:
├── OpenRouter API (recommended)
├── Tiny Llama 1.1B (basic functionality)
└── OpenAI API
```

---

*This strategy prioritizes user experience, maintainability, and resource efficiency while keeping the door open for future enhancements based on user feedback and ecosystem evolution.*