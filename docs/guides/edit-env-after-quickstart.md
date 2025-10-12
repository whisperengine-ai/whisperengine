## Editing your .env after Quickstart

This guide shows how to edit your `.env` file after running the quickstart script. The quickstart script creates a `.env` file with default settings that you can customize for your LLM provider and Discord integration.

---

## LLM Configuration (Required)

Open the `.env` file in your text editor. You'll see several LLM provider options. Choose ONE by uncommenting the lines (remove the `#`) for your preferred provider.

**💡 Note about API keys**: Local options (LM Studio, Ollama) don't need API keys because they run on your computer. Cloud options (OpenRouter, OpenAI) require API keys because they use external services.

### Option 1: LM Studio (Default - Free, Local, No API Key)
The default setting uses LM Studio running locally. **No API key needed** because it runs on your computer:

```env
LLM_CLIENT_TYPE=lmstudio
LLM_CHAT_API_URL=http://host.docker.internal:1234/v1
LLM_CHAT_MODEL=local-model
LLM_CHAT_API_KEY=
```

**Why the API key is empty**: LM Studio runs locally on your machine, so no external service or payment is needed.

### Option 2: Ollama (Free, Local, No API Key)
For Ollama running locally. **No API key needed** because it runs on your computer:

```env
LLM_CLIENT_TYPE=ollama
LLM_CHAT_API_URL=http://host.docker.internal:11434/v1
LLM_CHAT_MODEL=llama3.1:8b
LLM_CHAT_API_KEY=
```

**Why the API key is empty**: Ollama runs locally on your machine, so no external service or payment is needed.

### Option 3: OpenRouter (Paid, Cloud, API Key Required)
For OpenRouter, uncomment these lines and add your API key:

```env
LLM_CLIENT_TYPE=openrouter
LLM_CHAT_API_URL=https://openrouter.ai/api/v1
LLM_CHAT_MODEL=mistralai/mistral-medium-3.1
LLM_CHAT_API_KEY=your_api_key_here
```

**Why an API key is needed**: OpenRouter is a cloud service that costs money per message.

### Option 4: OpenAI (Paid, Cloud, API Key Required)
For OpenAI, uncomment these lines and add your API key:

```env
LLM_CLIENT_TYPE=openai
LLM_CHAT_API_URL=https://api.openai.com/v1
LLM_CHAT_MODEL=gpt-4o-mini
LLM_CHAT_API_KEY=sk-your_openai_key
```

**Why an API key is needed**: OpenAI is a cloud service that costs money per message.

---

## Discord Integration (Optional)

**Do you need Discord?** Only if you want to chat with your AI assistant through Discord. If you just want to use the web interface, you can skip this section.

To enable Discord, you need a Discord bot token from Discord Developer Portal:

1. Go to https://discord.com/developers/applications
2. Create a new application
3. Go to "Bot" section and create a bot
4. Copy the bot token

Then edit these lines in your `.env` file:

```env
DISCORD_BOT_TOKEN=your_discord_bot_token_here
ENABLE_DISCORD=true
```

**Why both settings are needed**: 
- `DISCORD_BOT_TOKEN` is your bot's identity on Discord
- `ENABLE_DISCORD=true` tells WhisperEngine to actually connect to Discord

If you don't want Discord, leave it as:

```env
DISCORD_BOT_TOKEN=
ENABLE_DISCORD=false
```

---

## Apply Changes

After editing your `.env` file, stop and start the assistant to reload the environment variables:

```bash
docker stop whisperengine-assistant
docker start whisperengine-assistant
```

Check if it's working:

```bash
docker logs whisperengine-assistant --tail 50
```