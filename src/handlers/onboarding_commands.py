#!/usr/bin/env python3
"""
Enhanced Help and Onboarding Commands
Provides context-aware help and guided onboarding for WhisperEngine users
"""

import logging
import os
from datetime import datetime
import discord
from discord.ext import commands
from src.utils.onboarding_manager import FirstRunDetector

logger = logging.getLogger(__name__)


class OnboardingCommands:
    """Command handlers for user onboarding and guided help"""
    
    def __init__(self, bot, **dependencies):
        self.bot = bot
        
        # Store dependencies passed from DiscordBotCore
        self.memory_manager = dependencies.get('memory_manager')
        self.llm_client = dependencies.get('llm_client')
        
        # Initialize onboarding detector
        self.detector = FirstRunDetector()
        
        # Onboarding command handlers initialized quietly
    
    def register_commands(self, bot_name_filter, is_admin):
        """Register onboarding and help commands"""
        
        @self.bot.command(name='getting-started', aliases=['start', 'begin', 'onboard'])
        async def getting_started(ctx):
            """Interactive getting started guide for new users"""
            try:
                embed = discord.Embed(
                    title="🎭 Getting Started with WhisperEngine",
                    description="Welcome! Let me help you get familiar with WhisperEngine's features.",
                    color=0x0099ff,
                    timestamp=datetime.now()
                )
                
                # Basic commands
                embed.add_field(
                    name="💬 Basic Chat",
                    value="Just talk to me naturally! I'll remember our conversations and respond with personality.",
                    inline=False
                )
                
                # Memory features
                if self.memory_manager:
                    embed.add_field(
                        name="🧠 Memory Features",
                        value="`!memory-search <query>` - Search past conversations\n"
                              "`!memory-stats` - See your memory statistics\n"
                              "`!memories` - View recent memories",
                        inline=False
                    )
                
                # Personality and emotions
                embed.add_field(
                    name="🎭 Personality & Emotions",
                    value="`!personality` - See my current personality traits\n"
                          "`!mood` - Check emotional context\n"
                          "`!analyze-image` - Analyze images with emotional intelligence",
                    inline=False
                )
                
                # Performance and admin
                embed.add_field(
                    name="📊 System & Admin",
                    value="`!perf` - System performance dashboard\n"
                          "`!status` - Bot health and configuration\n"
                          "`!help` - Complete command list",
                    inline=False
                )
                
                # Quick tips
                embed.add_field(
                    name="💡 Quick Tips",
                    value="• I learn from our conversations and remember context\n"
                          "• Upload images for visual analysis and description\n"
                          "• Use `!setup` if you need to reconfigure anything\n"
                          "• Check `!status` if something seems wrong",
                    inline=False
                )
                
                embed.set_footer(text="Try talking to me naturally - I'm here to help! 🤖")
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in getting started command: {e}")
                await ctx.send("❌ Error showing getting started guide. Check logs for details.")
        
        @self.bot.command(name='setup', aliases=['configure', 'config-help'])
        async def setup_help(ctx):
            """Show setup and configuration help"""
            try:
                embed = discord.Embed(
                    title="⚙️ WhisperEngine Setup & Configuration",
                    description="Configuration help and troubleshooting guide",
                    color=0xff6600,
                    timestamp=datetime.now()
                )
                
                # Check current configuration status
                env_mode = os.getenv('ENV_MODE', 'development')
                llm_url = os.getenv('LLM_CHAT_API_URL', 'Not configured')
                
                embed.add_field(
                    name="📋 Current Configuration",
                    value=f"**Environment**: {env_mode}\n"
                          f"**LLM Service**: {llm_url}\n"
                          f"**Bot Name**: {os.getenv('DISCORD_BOT_NAME', 'WhisperEngine')}",
                    inline=False
                )
                
                # Setup options
                embed.add_field(
                    name="🔧 Setup Options",
                    value="**Interactive Wizard**: `python setup_wizard.py`\n"
                          "**Validate Config**: `python env_manager.py --validate`\n"
                          "**Quick Setup**: `python env_manager.py --setup`\n"
                          "**Manual Config**: Edit your `.env` file",
                    inline=False
                )
                
                # Configuration files
                embed.add_field(
                    name="📁 Configuration Files",
                    value="• `.env.discord` - Discord bot mode\n"
                          "• `.env.development` - Development mode\n"
                          "• `.env` - Default configuration",
                    inline=False
                )
                
                # LLM setup
                embed.add_field(
                    name="🤖 LLM Setup",
                    value="**Local (Free)**:\n"
                          "• LM Studio: Download from lmstudio.ai\n"
                          "• Ollama: Install from ollama.ai\n\n"
                          "**Cloud (Paid)**:\n"
                          "• OpenAI: Get key from platform.openai.com\n"
                          "• OpenRouter: Get key from openrouter.ai",
                    inline=False
                )
                
                # Troubleshooting
                embed.add_field(
                    name="🔍 Troubleshooting",
                    value="• **Bot not responding**: Check `!status` for issues\n"
                          "• **Memory issues**: Check vector store connection\n"
                          "• **Performance slow**: Use `!perf` to diagnose\n"
                          "• **Setup errors**: Run validation with `--validate`",
                    inline=False
                )
                
                embed.set_footer(text="Need more help? Check the documentation or run the setup wizard!")
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in setup help command: {e}")
                await ctx.send("❌ Error showing setup help. Check logs for details.")
        
        @self.bot.command(name='features', aliases=['what-can-you-do', 'capabilities'])
        async def show_features(ctx):
            """Show WhisperEngine's main features and capabilities"""
            try:
                embed = discord.Embed(
                    title="🌟 WhisperEngine Features & Capabilities",
                    description="Discover what makes WhisperEngine special!",
                    color=0x00ff00,
                    timestamp=datetime.now()
                )
                
                # Core AI features
                embed.add_field(
                    name="🧠 Advanced AI Memory",
                    value="• Remembers conversations across sessions\n"
                          "• Contextual memory retrieval\n"
                          "• Semantic search through chat history\n"
                          "• Multi-dimensional memory networks",
                    inline=True
                )
                
                # Emotional intelligence
                embed.add_field(
                    name="🎭 Emotional Intelligence",
                    value="• Emotion detection and response\n"
                          "• Personality adaptation\n"
                          "• Mood-aware conversations\n"
                          "• Emotional context preservation",
                    inline=True
                )
                
                # Visual features
                embed.add_field(
                    name="🖼️ Visual Analysis",
                    value="• Image description and analysis\n"
                          "• Visual emotion detection\n"
                          "• Scene understanding\n"
                          "• Multi-modal conversations",
                    inline=True
                )
                
                # Performance features
                embed.add_field(
                    name="📊 Performance Monitoring",
                    value="• Real-time system health\n"
                          "• Performance optimization\n"
                          "• Bottleneck detection\n"
                          "• Automatic error recovery",
                    inline=True
                )
                
                # Privacy features
                embed.add_field(
                    name="🔒 Privacy & Security",
                    value="• Local deployment options\n"
                          "• Context-aware memory isolation\n"
                          "• Secure API key management\n"
                          "• Privacy-first design",
                    inline=True
                )
                
                # Platform features
                embed.add_field(
                    name="✨ Deployment Options",
                    value="• Discord bot mode\n"
                          "• Docker containers\n"
                          "• Multi-bot support\n"
                          "• Cross-platform support",
                    inline=True
                )
                
                # LLM compatibility
                embed.add_field(
                    name="🤖 LLM Compatibility",
                    value="**Local**: LM Studio, Ollama, llama.cpp\n"
                          "**Cloud**: OpenAI, OpenRouter, Custom APIs\n"
                          "**Models**: GPT-4, Claude, Llama, Mistral",
                    inline=False
                )
                
                embed.set_footer(text="Try these features yourself - start chatting naturally!")
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in features command: {e}")
                await ctx.send("❌ Error showing features. Check logs for details.")
        
        @self.bot.command(name='welcome', aliases=['intro', 'about'])
        async def welcome_message(ctx):
            """Show a friendly welcome message with personality"""
            try:
                user_name = ctx.author.display_name
                
                embed = discord.Embed(
                    title=f"🎭 Hello {user_name}! Welcome to WhisperEngine!",
                    description="I'm an AI with memory, emotions, and personality. Let's have an amazing conversation!",
                    color=0xff69b4,
                    timestamp=datetime.now()
                )
                
                # Personal greeting
                embed.add_field(
                    name="👋 Nice to meet you!",
                    value=f"Hi {user_name}! I'm WhisperEngine, your AI conversation partner. "
                          "I'm not just another chatbot - I have memory, emotions, and a unique personality "
                          "that adapts to our conversations.",
                    inline=False
                )
                
                # What makes me special
                embed.add_field(
                    name="✨ What makes me different?",
                    value="• **I remember** our conversations and learn from them\n"
                          "• **I understand emotions** and respond with empathy\n"
                          "• **I have personality** that evolves through our chats\n"
                          "• **I'm privacy-focused** and can run locally\n"
                          "• **I analyze images** and understand visual content",
                    inline=False
                )
                
                # How to interact
                embed.add_field(
                    name="💬 How to chat with me",
                    value="Just talk naturally! Ask me questions, share thoughts, upload images, "
                          "or tell me about your day. I'll remember what we discuss and build "
                          "on our conversations over time.",
                    inline=False
                )
                
                # Quick start
                embed.add_field(
                    name="✨ Quick Start",
                    value="Try saying: *\"Tell me about yourself\"* or *\"What can you remember about our past conversations?\"*\n"
                          "Use `!getting-started` for a complete guide.",
                    inline=False
                )
                
                embed.set_footer(text="I'm excited to get to know you! What would you like to talk about? 🤖💙")
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in welcome command: {e}")
                await ctx.send("❌ Error showing welcome message. Check logs for details.")
        
        @self.bot.command(name='first-time', aliases=['new-user', 'newbie'])
        async def first_time_help(ctx):
            """Special help for first-time users"""
            try:
                embed = discord.Embed(
                    title="🌱 First Time Using WhisperEngine? You're in the right place!",
                    description="Let me give you a gentle introduction to get you started.",
                    color=0x90EE90,
                    timestamp=datetime.now()
                )
                
                # Step by step guide
                embed.add_field(
                    name="📖 Step 1: Understand what I am",
                    value="I'm an AI assistant with advanced memory and emotional intelligence. "
                          "Unlike basic chatbots, I remember our conversations and develop a relationship with you over time.",
                    inline=False
                )
                
                embed.add_field(
                    name="💬 Step 2: Start chatting",
                    value="Just talk to me naturally! You can:\n"
                          "• Ask questions about anything\n"
                          "• Share your thoughts or experiences\n"
                          "• Upload images for me to analyze\n"
                          "• Request help with tasks",
                    inline=False
                )
                
                embed.add_field(
                    name="🧠 Step 3: Watch me learn",
                    value="As we chat, I'll remember:\n"
                          "• Your preferences and interests\n"
                          "• Context from our conversations\n"
                          "• Your communication style\n"
                          "• Topics that matter to you",
                    inline=False
                )
                
                embed.add_field(
                    name="🔧 Step 4: Explore commands",
                    value="When you're ready, try:\n"
                          "`!memory-search <topic>` - Find past conversations\n"
                          "`!personality` - See how I perceive myself\n"
                          "`!help` - Full command list",
                    inline=False
                )
                
                embed.add_field(
                    name="💡 Pro Tips for New Users",
                    value="• Don't worry about 'perfect' questions - I understand context\n"
                          "• Feel free to correct me if I misunderstand something\n"
                          "• I work better with longer conversations than quick exchanges\n"
                          "• Upload images to unlock my visual analysis features",
                    inline=False
                )
                
                embed.set_footer(text="Ready to start? Just say hello! I'm here to chat and help. 😊")
                await ctx.send(embed=embed)
                
            except Exception as e:
                logger.error(f"Error in first time help command: {e}")
                await ctx.send("❌ Error showing first-time help. Check logs for details.")


def create_onboarding_commands(bot, **dependencies):
    """Factory function to create onboarding commands"""
    return OnboardingCommands(bot, **dependencies)