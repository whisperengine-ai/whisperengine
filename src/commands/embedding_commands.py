"""
Embedding Test Commands for Discord Bot
Commands to test and manage the external embedding system.
"""

import os

from src.utils.embedding_manager import embedding_manager, get_embedding_config


async def handle_embedding_test_command(message) -> str:
    """
    Handle !embedding_test command - test the embedding system

    Usage: !embedding_test
    Returns: Embedding system status and test results
    """
    try:
        # Get configuration
        config = get_embedding_config()

        # Test connection
        connection_test = await embedding_manager.test_connection()

        # Test embedding generation
        test_texts = ["Hello world", "This is a test"]
        embeddings = await embedding_manager.get_embeddings(test_texts)

        # Format response
        response = "🔧 **Embedding System Status**\n\n"
        response += "**Configuration:**\n"
        response += (
            f"• External Embeddings: {'✅ Enabled' if config['use_external'] else '❌ Disabled'}\n"
        )
        response += f"• API URL: `{config['embedding_api_url']}`\n"
        response += f"• Model: `{config['embedding_model']}`\n"
        response += f"• Has API Key: {'✅ Yes' if config['has_api_key'] else '❌ No'}\n"
        response += f"• Batch Size: {config['max_batch_size']}\n\n"

        response += "**Connection Test:**\n"
        if connection_test["success"]:
            response += "✅ **Connected Successfully**\n"
            response += f"• Service: {connection_test.get('service', 'unknown')}\n"
            response += f"• Model: {connection_test.get('model', 'unknown')}\n"
            response += f"• Dimension: {connection_test.get('dimension', 'unknown')}\n"
            response += f"• Response Time: {connection_test.get('response_time', 0):.3f}s\n"
        else:
            response += "❌ **Connection Failed**\n"
            response += f"• Error: {connection_test.get('error', 'Unknown error')}\n"

        response += "\n**Embedding Test:**\n"
        if embeddings and len(embeddings) > 0:
            response += f"✅ **Generated {len(embeddings)} embeddings**\n"
            response += f"• Dimension: {len(embeddings[0])}\n"
            response += f"• Sample values: {[f'{x:.4f}' for x in embeddings[0][:5]]}\n"
        else:
            response += "❌ **Failed to generate embeddings**\n"

        return response

    except Exception as e:
        return f"❌ **Embedding test failed:** {str(e)}"


async def handle_embedding_config_command(message) -> str:
    """
    Handle !embedding_config command - show configuration

    Usage: !embedding_config
    Returns: Current embedding configuration
    """
    try:
        config = get_embedding_config()

        response = "⚙️ **Embedding Configuration**\n\n"

        for key, value in config.items():
            if key == "has_api_key":
                display_value = "✅ Set" if value else "❌ Not set"
            elif key == "has_local_function":
                display_value = "✅ Available" if value else "❌ Not available"
            elif isinstance(value, bool):
                display_value = "✅ Enabled" if value else "❌ Disabled"
            else:
                display_value = str(value)

            # Format key name
            display_key = key.replace("_", " ").title()
            response += f"• **{display_key}:** `{display_value}`\n"

        response += "\n**To change configuration:**\n"
        response += "1. Update your `.env` file\n"
        response += "2. Set `USE_EXTERNAL_EMBEDDINGS=true/false`\n"
        response += "3. Restart the bot\n"

        return response

    except Exception as e:
        return f"❌ **Failed to get configuration:** {str(e)}"


async def handle_embedding_performance_command(message) -> str:
    """
    Handle !embedding_performance command - analyze embedding performance

    Usage: !embedding_performance
    Returns: Performance analysis and recommendations
    """
    try:
        from src.utils.chromadb_performance_monitor import check_chromadb_performance

        perf_info = await check_chromadb_performance()

        response = "🔍 **ChromaDB Embedding Performance Analysis**\n\n"

        # System information
        system_info = perf_info.get("system_info", {})
        response += "**System Information:**\n"
        response += f"• Platform: {system_info.get('platform', 'unknown')}\n"
        response += f"• Architecture: {system_info.get('machine', 'unknown')}\n"

        # GPU information
        gpu_info = perf_info.get("gpu_info", {})
        response += f"• GPU Available: {'✅ Yes' if gpu_info.get('available') else '❌ No'}\n"
        if not gpu_info.get("available"):
            response += f"• Reason: {gpu_info.get('reason', 'unknown')}\n"

        # Performance estimate
        perf_est = perf_info.get("performance_estimate", {})
        tokens_per_sec = perf_est.get("tokens_per_second", 0)
        if tokens_per_sec > 0:
            response += f"• Estimated Speed: ~{tokens_per_sec:,.0f} tokens/sec\n"

        response += "\n"

        # Warnings
        warnings = perf_info.get("warnings", [])
        if warnings:
            response += "**⚠️ Performance Warnings:**\n"
            for warning in warnings:
                response += f"• {warning}\n"
            response += "\n"

        # Recommendations
        recommendations = perf_info.get("recommendations", [])
        if recommendations:
            response += "**💡 Recommendations:**\n"
            for rec in recommendations:
                response += f"• {rec}\n"
            response += "\n"

        # Current configuration
        from src.utils.embedding_manager import is_external_embedding_configured

        external_configured = is_external_embedding_configured()
        response += "**Current Configuration:**\n"
        response += f"• External Embeddings: {'✅ Configured' if external_configured else '❌ Not configured'}\n"

        if external_configured:
            # Show the actual API URL being used (including fallback)
            embedding_url = (
                os.getenv("LLM_EMBEDDING_API_URL")
                or os.getenv("LLM_CHAT_API_URL")  # Fallback to main LLM API URL
                or "Not set"
            )
            response += f"• API URL: `{embedding_url}`\n"
            if (
                os.getenv("LLM_EMBEDDING_API_URL") is None
                and os.getenv("LLM_CHAT_API_URL") is not None
            ):
                response += "  (using LLM_CHAT_API_URL as fallback)\n"
            response += f"• Model: `{os.getenv('LLM_EMBEDDING_MODEL', 'not set')}`\n"
        else:
            response += "• Using: ChromaDB default embeddings (CPU-based)\n"

        # Configuration suggestions
        external_recommended = perf_info.get("external_embedding_recommended", False)
        if external_recommended and not external_configured:
            response += "\n**🚀 Recommended Configuration:**\n"
            response += "Add to your `.env` file:\n"
            response += "```\n"
            response += "LLM_EMBEDDING_API_URL=http://localhost:1234/v1\n"
            response += "LLM_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5\n"
            response += "```\n"
            response += "Then restart the bot for better performance.\n"

        return response

    except Exception as e:
        return f"❌ **Performance analysis failed:** {str(e)}"


async def handle_embedding_switch_command(message, args) -> str:
    """
    Handle !embedding_switch command - switch embedding modes

    Usage: !embedding_switch <external|local>
    Returns: Switch status
    """
    if not args or args[0].lower() not in ["external", "local"]:
        return "Usage: `!embedding_switch <external|local>`"

    mode = args[0].lower()

    response = "⚠️ **Embedding Mode Switch Request**\n\n"
    response += f"You requested to switch to **{mode}** embeddings.\n\n"
    response += "**To switch modes:**\n"

    if mode == "external":
        response += "1. Add to your `.env` file:\n"
        response += "```\n"
        response += "LLM_EMBEDDING_API_URL=http://localhost:1234/v1\n"
        response += "LLM_EMBEDDING_MODEL=text-embedding-nomic-embed-text-v1.5\n"
        response += "# Optional: LLM_EMBEDDING_API_KEY=your_key\n"
        response += "```\n"
        response += "2. Restart the bot\n\n"
        response += "**Alternative APIs:**\n"
        response += "• OpenAI: `https://api.openai.com/v1` + `text-embedding-3-small`\n"
        response += "• Ollama: `http://localhost:11434/v1` + `nomic-embed-text`\n"
    else:
        response += "1. Remove or comment out these lines in `.env`:\n"
        response += "```\n"
        response += "# LLM_EMBEDDING_API_URL=...\n"
        response += "# LLM_EMBEDDING_MODEL=...\n"
        response += "```\n"
        response += "2. Restart the bot\n\n"
        response += "Local embeddings will use ChromaDB's built-in models.\n"
        response += "**Note:** May be slower, especially on macOS.\n"

    response += "\n⚡ **Note:** Configuration changes require a bot restart to take effect."

    return response


# Example integration with your Discord bot commands
def add_embedding_commands_to_bot(bot):
    """
    Add embedding test commands to your Discord bot

    Call this function in your bot setup to add the commands
    """

    @bot.command(name="embedding_test")
    async def embedding_test(ctx):
        """Test the embedding system"""
        try:
            # Check if this is a DM or if user has admin permissions
            if not ctx.guild or ctx.author.guild_permissions.administrator:
                response = await handle_embedding_test_command(ctx.message)
                await ctx.send(response)
            else:
                await ctx.send("❌ This command requires administrator permissions.")
        except Exception as e:
            await ctx.send(f"❌ Command failed: {str(e)}")

    @bot.command(name="embedding_config")
    async def embedding_config(ctx):
        """Show embedding configuration"""
        try:
            if not ctx.guild or ctx.author.guild_permissions.administrator:
                response = await handle_embedding_config_command(ctx.message)
                await ctx.send(response)
            else:
                await ctx.send("❌ This command requires administrator permissions.")
        except Exception as e:
            await ctx.send(f"❌ Command failed: {str(e)}")

    @bot.command(name="embedding_switch")
    async def embedding_switch(ctx, mode=None):
        """Switch embedding modes"""
        try:
            if not ctx.guild or ctx.author.guild_permissions.administrator:
                args = [mode] if mode else []
                response = await handle_embedding_switch_command(ctx.message, args)
                await ctx.send(response)
            else:
                await ctx.send("❌ This command requires administrator permissions.")
        except Exception as e:
            await ctx.send(f"❌ Command failed: {str(e)}")

    @bot.command(name="embedding_performance")
    async def embedding_performance(ctx):
        """Analyze embedding performance"""
        try:
            if not ctx.guild or ctx.author.guild_permissions.administrator:
                response = await handle_embedding_performance_command(ctx.message)
                await ctx.send(response)
            else:
                await ctx.send("❌ This command requires administrator permissions.")
        except Exception as e:
            await ctx.send(f"❌ Command failed: {str(e)}")


# Alternative: Manual command handling for existing bot structure
async def handle_embedding_commands(message, command, args):
    """
    Handle embedding-related commands manually

    Args:
        message: Discord message object
        command: Command name (without !)
        args: List of command arguments

    Returns:
        Response string to send back
    """
    if command == "embedding_test":
        return await handle_embedding_test_command(message)

    elif command == "embedding_config":
        return await handle_embedding_config_command(message)

    elif command == "embedding_switch":
        return await handle_embedding_switch_command(message, args)

    elif command == "embedding_performance":
        return await handle_embedding_performance_command(message)

    else:
        return None  # Command not handled


# Usage example for your existing bot
"""
In your main bot file, add something like:

from src.commands.embedding_commands import handle_embedding_commands

# In your message handler:
if content.startswith('!'):
    parts = content[1:].split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    # Handle embedding commands
    embedding_response = await handle_embedding_commands(message, command, args)
    if embedding_response:
        await message.channel.send(embedding_response)
        return

    # Handle other commands...
"""
