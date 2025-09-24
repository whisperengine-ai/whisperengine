/**
 * Web Voice Chat Component
 * 
 * Provides voice chat functionality for the WhisperEngine web interface:
 * - Record audio from microphone
 * - Send audio for speech-to-text conversion
 * - Send text messages to bots
 * - Receive bot responses as audio (text-to-speech)
 * - Play audio responses in browser
 */

class VoiceChat {
    constructor(apiBaseUrl = '/api/voice') {
        this.apiBaseUrl = apiBaseUrl;
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioContext = null;
        this.currentAudio = null;
        
        // Voice settings
        this.voiceSettings = {
            voice_id: null,
            stability: 0.5,
            similarity_boost: 0.8,
            style: 0.0,
            use_speaker_boost: true
        };
        
        // Initialize audio context
        this.initializeAudio();
        
        // Load available voices
        this.loadAvailableVoices();
    }

    /**
     * Initialize Web Audio API
     */
    async initializeAudio() {
        try {
            this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Audio context initialized');
        } catch (error) {
            console.error('Failed to initialize audio context:', error);
        }
    }

    /**
     * Load available voices from API
     */
    async loadAvailableVoices() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/voices`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const voices = await response.json();
            console.log('Available voices:', voices);
            
            // Use first voice as default if none set
            if (voices.length > 0 && !this.voiceSettings.voice_id) {
                this.voiceSettings.voice_id = voices[0].voice_id;
            }
            
            return voices;
        } catch (error) {
            console.error('Failed to load voices:', error);
            return [];
        }
    }

    /**
     * Start recording audio from microphone
     */
    async startRecording() {
        try {
            // Request microphone access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            // Create media recorder
            this.mediaRecorder = new MediaRecorder(stream, {
                mimeType: 'audio/webm;codecs=opus'
            });
            
            this.audioChunks = [];
            
            // Handle audio data
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };
            
            // Handle recording stop
            this.mediaRecorder.onstop = () => {
                this.processRecording();
            };
            
            // Start recording
            this.mediaRecorder.start();
            this.isRecording = true;
            
            console.log('Recording started');
            this.onRecordingStart();
            
        } catch (error) {
            console.error('Failed to start recording:', error);
            this.onRecordingError(error);
        }
    }

    /**
     * Stop recording audio
     */
    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            
            // Stop media stream
            const stream = this.mediaRecorder.stream;
            stream.getTracks().forEach(track => track.stop());
            
            console.log('Recording stopped');
            this.onRecordingStop();
        }
    }

    /**
     * Process recorded audio
     */
    async processRecording() {
        try {
            // Create audio blob
            const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            console.log('Audio blob created:', audioBlob.size, 'bytes');
            
            // Convert to text using speech-to-text API
            const transcription = await this.speechToText(audioBlob);
            console.log('Transcription:', transcription);
            
            // Trigger callback with transcribed text
            this.onTranscription(transcription);
            
        } catch (error) {
            console.error('Failed to process recording:', error);
            this.onTranscriptionError(error);
        }
    }

    /**
     * Convert speech to text using API
     */
    async speechToText(audioBlob) {
        const formData = new FormData();
        formData.append('audio_file', audioBlob, 'recording.webm');
        
        const response = await fetch(`${this.apiBaseUrl}/stt`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Speech-to-text failed');
        }
        
        const result = await response.json();
        return result.text;
    }

    /**
     * Convert text to speech using API
     */
    async textToSpeech(text, voiceId = null) {
        try {
            const payload = {
                text: text,
                voice_id: voiceId || this.voiceSettings.voice_id
            };
            
            const response = await fetch(`${this.apiBaseUrl}/tts`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Text-to-speech failed');
            }
            
            const result = await response.json();
            console.log('TTS result:', result.voice_id, result.duration_estimate);
            
            // Decode base64 audio data
            const audioData = atob(result.audio_data);
            const audioBuffer = new ArrayBuffer(audioData.length);
            const audioView = new Uint8Array(audioBuffer);
            
            for (let i = 0; i < audioData.length; i++) {
                audioView[i] = audioData.charCodeAt(i);
            }
            
            // Create audio blob and play
            const audioBlob = new Blob([audioBuffer], { type: 'audio/mpeg' });
            await this.playAudio(audioBlob);
            
            return result;
            
        } catch (error) {
            console.error('Text-to-speech error:', error);
            this.onTTSError(error);
            throw error;
        }
    }

    /**
     * Play audio blob in browser
     */
    async playAudio(audioBlob) {
        try {
            // Stop any currently playing audio
            if (this.currentAudio) {
                this.currentAudio.pause();
                this.currentAudio = null;
            }
            
            // Create audio URL and play
            const audioUrl = URL.createObjectURL(audioBlob);
            this.currentAudio = new Audio(audioUrl);
            
            // Handle audio events
            this.currentAudio.onplay = () => {
                console.log('Audio playback started');
                this.onAudioStart();
            };
            
            this.currentAudio.onended = () => {
                console.log('Audio playback ended');
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                this.onAudioEnd();
            };
            
            this.currentAudio.onerror = (error) => {
                console.error('Audio playback error:', error);
                URL.revokeObjectURL(audioUrl);
                this.currentAudio = null;
                this.onAudioError(error);
            };
            
            // Start playback
            await this.currentAudio.play();
            
        } catch (error) {
            console.error('Failed to play audio:', error);
            this.onAudioError(error);
        }
    }

    /**
     * Update voice settings
     */
    async updateVoiceSettings(settings) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/settings`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to update settings');
            }
            
            const updatedSettings = await response.json();
            this.voiceSettings = updatedSettings;
            console.log('Voice settings updated:', updatedSettings);
            
            return updatedSettings;
            
        } catch (error) {
            console.error('Failed to update voice settings:', error);
            throw error;
        }
    }

    /**
     * Get current voice settings
     */
    async getVoiceSettings() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/settings`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const settings = await response.json();
            this.voiceSettings = settings;
            return settings;
            
        } catch (error) {
            console.error('Failed to get voice settings:', error);
            return this.voiceSettings;
        }
    }

    /**
     * Check voice service health
     */
    async checkHealth() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const health = await response.json();
            console.log('Voice service health:', health);
            return health;
        } catch (error) {
            console.error('Health check failed:', error);
            return { status: 'error', error: error.message };
        }
    }

    // Event callbacks (override these in your implementation)
    onRecordingStart() {
        console.log('Recording started callback');
    }

    onRecordingStop() {
        console.log('Recording stopped callback');
    }

    onRecordingError(error) {
        console.error('Recording error callback:', error);
    }

    onTranscription(text) {
        console.log('Transcription callback:', text);
    }

    onTranscriptionError(error) {
        console.error('Transcription error callback:', error);
    }

    onTTSError(error) {
        console.error('TTS error callback:', error);
    }

    onAudioStart() {
        console.log('Audio start callback');
    }

    onAudioEnd() {
        console.log('Audio end callback');
    }

    onAudioError(error) {
        console.error('Audio error callback:', error);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VoiceChat;
} else if (typeof window !== 'undefined') {
    window.VoiceChat = VoiceChat;
}