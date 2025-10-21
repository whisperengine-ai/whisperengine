"""
Helper utility functions for the Discord bot.
Contains common functionality used across multiple modules.
"""

import logging
import os
from datetime import UTC, datetime
from typing import List

logger = logging.getLogger(__name__)

# Admin user IDs - this should be configurable
admin_user_ids = set()
if os.getenv("ADMIN_USER_IDS"):
    try:
        admin_user_ids = set(map(int, os.getenv("ADMIN_USER_IDS", "").split(",")))
        logger.info(f"Loaded {len(admin_user_ids)} admin user IDs")
    except ValueError:
        logger.warning("Invalid ADMIN_USER_IDS format, no admin users configured")


def is_admin(ctx) -> bool:
    """Check if the user has admin permissions (guild admin or in admin list)"""
    user_id = ctx.author.id

    # Check if user is in admin list
    if user_id in admin_user_ids:
        return True

    # Check guild permissions (only if in a guild)
    if ctx.guild and hasattr(ctx.author, "guild_permissions"):
        return ctx.author.guild_permissions.administrator

    return False


def get_current_time_context() -> str:
    """Generate current date/time context for the bot"""
    now = datetime.now(UTC)
    local_time = now.astimezone()

    # Format for different time zones - you can customize this based on your needs
    utc_str = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    local_str = local_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    day_of_week = now.strftime("%A")

    return f"Current time: {local_str} ({utc_str}) - {day_of_week}"


def add_debug_info_to_response(
    response: str,
    user_id: str,
    memory_manager,
    message_id: str | None = None,
    debug_mode: bool = False,
) -> str:
    """SECURITY FIX: Secure debug logging that prevents sensitive information disclosure"""
    try:
        # Import secure debug module
        from src.security.debug_mode_security import secure_add_debug_info_to_response

        # Use secure debug logging instead of exposing sensitive information
        return secure_add_debug_info_to_response(
            response, user_id, memory_manager, message_id, debug_mode
        )
    except ImportError:
        # Fallback if security module not available
        if debug_mode:
            return f"{response}\n\n[Debug: Message ID: {message_id}]"
        return response


def store_discord_user_info(user, memory_manager, debug_mode: bool = False):
    """Store Discord user information (disabled - global facts are admin-only now)"""
    # Global fact storage has been disabled for automatic collection
    # Only admins can manually add global facts using !add_global_fact
    # SECURITY FIX: Use secure logging to prevent information disclosure
    try:
        from src.security.debug_mode_security import secure_log_user_info

        secure_log_user_info(user, memory_manager, debug_mode)
    except ImportError:
        # Fallback if security module not available
        if debug_mode:
            logger.debug(f"User info: {user.display_name} ({user.id})")


def store_discord_server_info(guild, memory_manager, debug_mode: bool = False):
    """Store Discord server information (disabled - global facts are admin-only now)"""
    # Global fact storage has been disabled for automatic collection
    # Only admins can manually add global facts using !add_global_fact
    # SECURITY FIX: Use secure logging to prevent information disclosure
    try:
        from src.security.debug_mode_security import secure_log_server_info

        secure_log_server_info(guild, memory_manager, debug_mode)
    except ImportError:
        # Fallback if security module not available
        if debug_mode:
            logger.debug(f"Guild info: {guild.name} ({guild.id})")


def _summarize_message_topics(messages: List[str]) -> List[str]:
    """Convert raw message content to meaningful topic summaries."""
    topics = []
    
    # Topic extraction patterns
    topic_keywords = {
        'Food preferences': ['pizza', 'burger', 'sandwich', 'taco', 'food', 'eat', 'meal', 'breakfast', 'dinner', 'lunch'],
        'Greetings and social': ['hi', 'hello', 'good morning', 'good afternoon', 'good evening', 'hey', 'how are you'],
        'Mood and emotions': ['good mood', 'secret', 'happy', 'excited', 'feeling', 'emotion'],
        'Activities': ['beach', 'swim', 'dive', 'travel', 'visit', 'went to', 'going to'],
        'Questions about preferences': ['what do', 'what foods', 'what\'s your', 'tell me about'],
        'Creative topics': ['dream', 'creative', 'art', 'music', 'design', 'imagine'],
        'Science topics': ['research', 'experiment', 'ocean', 'marine', 'study']
    }
    
    for message in messages:
        message_lower = message.lower()
        topic_found = False
        
        # Find matching topic categories
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                if topic not in topics:  # Avoid duplicates
                    topics.append(topic)
                topic_found = True
                break
        
        # If no specific topic found, create a generic one
        if not topic_found and len(message) > 20:
            # Extract meaningful words and create a topic
            words = message.split()[:4]  # First 4 words
            clean_words = [w for w in words if len(w) > 2 and w.lower() not in ['the', 'and', 'for', 'are', 'you', 'what', 'how']]
            if clean_words:
                generic_topic = f"Discussion about {' '.join(clean_words[:2]).lower()}"
                if generic_topic not in topics:
                    topics.append(generic_topic)
    
    # Limit to 3 most relevant topics
    return topics[:3] if topics else ["General conversation"]


def generate_conversation_summary(recent_messages, user_id: str, max_length: int = 400) -> str:
    """
    Generate an intelligent summary of recent conversation for system context.

    This provides structured conversation flow context that's easier to sanitize
    than raw message history, supporting the security improvements.

    Args:
        recent_messages: List of recent Discord messages or message dicts
        user_id: User ID for filtering user-specific messages
        max_length: Maximum length of summary

    Returns:
        Concise conversation summary string, or empty string if no meaningful content
    """
    # Check if memory summarization is enabled
    enable_summarization = os.getenv("ENABLE_MEMORY_SUMMARIZATION", "true").lower() in ("true", "1", "yes", "on")
    if not enable_summarization:
        return ""
    
    try:
        if not recent_messages or len(recent_messages) < 2:
            return ""

        # Filter and analyze recent messages (last 10 for summary)
        user_topics = []
        bot_responses = []

        for msg in recent_messages[-10:]:
            # Handle both Discord message objects and dict messages from Redis cache
            if isinstance(msg, dict):
                # Redis cache message format
                content = msg.get("content", "")
                author_id = str(msg.get("author_id", ""))
                is_bot = msg.get("bot", False)
            else:
                # Discord message object format
                content = msg.content
                author_id = str(msg.author.id)
                is_bot = hasattr(msg.author, "bot") and msg.author.bot

            # Skip commands and very short messages
            if content.startswith("!") or len(content.strip()) < 5:
                continue

            if author_id == user_id:
                user_topics.append(content.strip())
            elif is_bot:
                bot_responses.append(
                    content.strip()[:300]
                )  # Increased from 100 to 300 characters for bot responses

        if not user_topics:
            return ""

        # Generate structured summary
        summary_parts = []

        # Recent user interests/topics (last 3 most meaningful) - IMPROVED: Summarize instead of raw content
        meaningful_topics = [topic for topic in user_topics[-3:] if len(topic) > 10]
        if meaningful_topics:
            # Convert raw message content to topic summaries
            summarized_topics = _summarize_message_topics(meaningful_topics)
            topics_summary = "; ".join(summarized_topics)
            summary_parts.append(f"Recent topics: {topics_summary}")

        # Conversation flow indicator
        if len(user_topics) >= 1:  # Changed from > 1 to >= 1 to handle single messages
            if len(bot_responses) > 0:
                summary_parts.append(
                    f"Active conversation with {len(user_topics)} user messages and {len(bot_responses)} responses"
                )
            elif len(user_topics) > 1:
                summary_parts.append(
                    f"User initiated conversation with {len(user_topics)} messages"
                )
            # For single message, we rely on the topics summary only

        # Combine summary
        full_summary = ". ".join(summary_parts)

        # Truncate if too long and sanitize
        if len(full_summary) > max_length:
            full_summary = full_summary[: max_length - 3] + "..."

        # Basic sanitization to prevent system prompt injection
        full_summary = (
            full_summary.replace("system:", "").replace("assistant:", "").replace("user:", "")
        )

        return full_summary

    except Exception as e:
        logger.warning(f"Error generating conversation summary: {e}")
        return ""


async def process_message_with_images(
    message_content: str, attachments, conversation_context: list, llm_client, image_processor
) -> list:
    """
    Process a message that may contain image attachments and update conversation context

    Args:
        message_content: Text content of the message
        attachments: Discord message attachments
        conversation_context: Existing conversation context to modify
        llm_client: LLM client instance
        image_processor: Image processor instance

    Returns:
        Updated conversation context with image handling
    """
    # Check if there are any image attachments
    if not attachments:
        # No attachments, add text message normally
        conversation_context.append({"role": "user", "content": message_content})
        return conversation_context

    # Process image attachments
    processed_images = await image_processor.process_multiple_attachments(attachments)

    if not processed_images:
        # No valid images found, treat as text-only message
        conversation_context.append({"role": "user", "content": message_content})
        logger.debug("No valid images found in attachments")
        return conversation_context

    logger.info(f"Found {len(processed_images)} valid images in message")

    # Check if vision is supported directly; if not, attempt hybrid summarizer
    if not llm_client.has_vision_support():
        try:
            from src.vision.vision_summarizer import get_vision_summarizer
            summarizer = get_vision_summarizer()
        except Exception as e:
            summarizer = None
            logger.warning(f"Hybrid vision summarizer import failed: {e}")

        summary_text = None
        if summarizer and summarizer.is_available():
            try:
                summary_text = await summarizer.summarize_images(attachments, user_prompt=message_content[:200])
            except Exception as e:
                logger.error(f"Vision summarizer error: {e}")
                summary_text = None

        if summary_text:
            # Insert as system-level visual context to prevent model treating it as user intent to analyze
            visual_context_msg = (
                "Visual context (user shared images): " + summary_text.strip()
            )
            if message_content.strip():
                conversation_context.append({"role": "user", "content": message_content})
            conversation_context.append({"role": "system", "content": visual_context_msg})
            logger.info("Added hybrid vision summary via secondary model")
            return conversation_context
        else:
            # Fallback: simple description prompt (legacy behavior)
            image_description = image_processor.get_image_description_prompt(processed_images)
            combined_content = (
                f"{message_content}\n\n{image_description}"
                if message_content.strip()
                else image_description
            )
            conversation_context.append({"role": "user", "content": combined_content})
            logger.info("Added image descriptions to text message (vision not supported; summarizer unavailable)")
            return conversation_context

    # Vision is supported, create multimodal message
    encoded_images = [img["encoded_data"] for img in processed_images]

    # Create vision message
    vision_message = llm_client.create_vision_message(message_content, encoded_images)
    conversation_context.append(vision_message)

    logger.info(f"Created vision message with {len(encoded_images)} images")
    return conversation_context


def get_message_content(msg):
    """Get content from message, handling both dict and Discord message objects"""
    if isinstance(msg, dict):
        return msg.get("content", "")
    return getattr(msg, "content", "")


def get_message_author_id(msg):
    """Get author ID from message, handling both dict and Discord message objects"""
    if isinstance(msg, dict):
        return str(msg.get("author_id", ""))
    return str(getattr(msg.author, "id", ""))


def get_message_author_bot(msg):
    """Check if message author is a bot, handling both dict and Discord message objects"""
    if isinstance(msg, dict):
        return msg.get("bot", False)
    return getattr(msg.author, "bot", False)


def message_equals_bot_user(msg, bot_user):
    """Check if message author equals bot user"""
    if isinstance(msg, dict):
        return str(msg.get("author_id", "")) == str(bot_user.id)
    return msg.author == bot_user


def get_message_id(msg):
    """Get message ID, handling both dict and Discord message objects"""
    if isinstance(msg, dict):
        return str(msg.get("id", ""))
    return str(getattr(msg, "id", ""))


def prepare_message_for_storage(message_content: str, attachments) -> str:
    """
    Prepare message content for memory storage by adding attachment descriptions.

    Args:
        message_content: Original message text content
        attachments: Discord message attachments

    Returns:
        Text content suitable for memory storage (no binary data)
    """
    # Start with the original text content
    storage_content = message_content

    # Process attachments if present
    if attachments:
        # Categorize attachments by MIME type
        attachment_categories = {
            "images": [],
            "text_files": [],
            "documents": [],
            "media": [],
            "archives": [],
            "code": [],
            "other": [],
        }

        # MIME type mappings for better categorization
        mime_categories = {
            # Images
            "image/": "images",
            # Text files
            "text/plain": "text_files",
            "text/markdown": "text_files",
            "text/csv": "text_files",
            "text/html": "text_files",
            "text/css": "text_files",
            "text/javascript": "code",
            "text/xml": "text_files",
            # Documents
            "application/pdf": "documents",
            "application/msword": "documents",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "documents",
            "application/vnd.ms-excel": "documents",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "documents",
            "application/vnd.ms-powerpoint": "documents",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "documents",
            "application/rtf": "documents",
            "application/vnd.oasis.opendocument.text": "documents",
            "application/vnd.oasis.opendocument.spreadsheet": "documents",
            "application/vnd.oasis.opendocument.presentation": "documents",
            # Code files
            "application/json": "code",
            "application/xml": "code",
            "application/javascript": "code",
            "application/x-python-code": "code",
            "application/x-sh": "code",
            # Media
            "audio/": "media",
            "video/": "media",
            # Archives
            "application/zip": "archives",
            "application/x-rar-compressed": "archives",
            "application/x-7z-compressed": "archives",
            "application/gzip": "archives",
            "application/x-tar": "archives",
        }

        # Extension fallbacks for when MIME type isn't available or reliable
        extension_categories = {
            # Text files
            ".txt": "text_files",
            ".md": "text_files",
            ".csv": "text_files",
            ".html": "text_files",
            ".htm": "text_files",
            ".xml": "text_files",
            ".css": "text_files",
            ".yaml": "text_files",
            ".yml": "text_files",
            ".ini": "text_files",
            ".cfg": "text_files",
            ".conf": "text_files",
            ".log": "text_files",
            ".sql": "text_files",
            # Code files
            ".py": "code",
            ".js": "code",
            ".ts": "code",
            ".jsx": "code",
            ".tsx": "code",
            ".java": "code",
            ".cpp": "code",
            ".c": "code",
            ".h": "code",
            ".hpp": "code",
            ".cs": "code",
            ".php": "code",
            ".rb": "code",
            ".go": "code",
            ".rs": "code",
            ".swift": "code",
            ".kt": "code",
            ".scala": "code",
            ".r": "code",
            ".json": "code",
            ".xml": "code",
            ".sh": "code",
            ".bat": "code",
            ".ps1": "code",
            # Documents
            ".pdf": "documents",
            ".doc": "documents",
            ".docx": "documents",
            ".xls": "documents",
            ".xlsx": "documents",
            ".ppt": "documents",
            ".pptx": "documents",
            ".rtf": "documents",
            ".odt": "documents",
            ".ods": "documents",
            ".odp": "documents",
            # Images
            ".jpg": "images",
            ".jpeg": "images",
            ".png": "images",
            ".gif": "images",
            ".bmp": "images",
            ".svg": "images",
            ".webp": "images",
            ".ico": "images",
            ".tiff": "images",
            ".tif": "images",
            # Media
            ".mp3": "media",
            ".wav": "media",
            ".flac": "media",
            ".aac": "media",
            ".mp4": "media",
            ".avi": "media",
            ".mov": "media",
            ".wmv": "media",
            ".mkv": "media",
            ".webm": "media",
            ".m4v": "media",
            # Archives
            ".zip": "archives",
            ".rar": "archives",
            ".7z": "archives",
            ".tar": "archives",
            ".gz": "archives",
            ".bz2": "archives",
            ".xz": "archives",
        }

        # Categorize each attachment
        for att in attachments:
            category = "other"  # default

            # First try MIME type detection (if available)
            if hasattr(att, "content_type") and att.content_type:
                mime_type = att.content_type.lower()

                # Check exact MIME type matches
                if mime_type in mime_categories:
                    category = mime_categories[mime_type]
                else:
                    # Check prefix matches (e.g., 'image/' matches 'image/png')
                    for mime_prefix, cat in mime_categories.items():
                        if mime_prefix.endswith("/") and mime_type.startswith(mime_prefix):
                            category = cat
                            break

            # Fallback to extension-based detection
            if category == "other":
                extension = os.path.splitext(att.filename.lower())[1]
                category = extension_categories.get(extension, "other")

            attachment_categories[category].append(att)

        # Generate descriptions for each category
        descriptions = []

        # Handle images (preserve existing image processing logic)
        if attachment_categories["images"]:
            if len(attachment_categories["images"]) == 1:
                img = attachment_categories["images"][0]
                descriptions.append(f"[Image: {img.filename}]")
            else:
                filenames = [img.filename for img in attachment_categories["images"]]
                descriptions.append(f"[Images: {', '.join(filenames)}]")

        # Handle text files
        if attachment_categories["text_files"]:
            if len(attachment_categories["text_files"]) == 1:
                txt_file = attachment_categories["text_files"][0]
                descriptions.append(f"[Text file: {txt_file.filename}]")
            else:
                filenames = [txt.filename for txt in attachment_categories["text_files"]]
                descriptions.append(f"[Text files: {', '.join(filenames)}]")

        # Handle code files
        if attachment_categories["code"]:
            if len(attachment_categories["code"]) == 1:
                code_file = attachment_categories["code"][0]
                descriptions.append(f"[Code file: {code_file.filename}]")
            else:
                filenames = [code.filename for code in attachment_categories["code"]]
                descriptions.append(f"[Code files: {', '.join(filenames)}]")

        # Handle documents
        if attachment_categories["documents"]:
            if len(attachment_categories["documents"]) == 1:
                doc_file = attachment_categories["documents"][0]
                descriptions.append(f"[Document: {doc_file.filename}]")
            else:
                filenames = [doc.filename for doc in attachment_categories["documents"]]
                descriptions.append(f"[Documents: {', '.join(filenames)}]")

        # Handle media files
        if attachment_categories["media"]:
            if len(attachment_categories["media"]) == 1:
                media_file = attachment_categories["media"][0]
                descriptions.append(f"[Media file: {media_file.filename}]")
            else:
                filenames = [media.filename for media in attachment_categories["media"]]
                descriptions.append(f"[Media files: {', '.join(filenames)}]")

        # Handle archives
        if attachment_categories["archives"]:
            if len(attachment_categories["archives"]) == 1:
                archive_file = attachment_categories["archives"][0]
                descriptions.append(f"[Archive: {archive_file.filename}]")
            else:
                filenames = [arch.filename for arch in attachment_categories["archives"]]
                descriptions.append(f"[Archives: {', '.join(filenames)}]")

        # Handle other/unknown files
        if attachment_categories["other"]:
            if len(attachment_categories["other"]) == 1:
                other_file = attachment_categories["other"][0]
                descriptions.append(f"[File: {other_file.filename}]")
            else:
                filenames = [other.filename for other in attachment_categories["other"]]
                descriptions.append(f"[Files: {', '.join(filenames)}]")

        # Add all descriptions to storage content
        if descriptions:
            storage_content += f"\n{' '.join(descriptions)}"

    # SECURITY FIX: Ensure we don't return empty content
    # If the message content was empty but had attachments, create a meaningful description
    if not storage_content.strip():
        if attachments:
            attachment_count = len(attachments)
            if attachment_count == 1:
                storage_content = f"[Shared 1 file: {attachments[0].filename}]"
            else:
                storage_content = f"[Shared {attachment_count} files]"
        else:
            storage_content = "[Empty message]"

    return storage_content


def fix_message_alternation(messages: list) -> list:
    """
    Ensure proper user/assistant alternation by filtering, not merging.
    This prevents content concatenation bugs while satisfying API requirements.

    SECURITY ENHANCEMENT: Completely eliminates content merging to prevent conversation history leakage.

    Args:
        messages: List of message dictionaries with 'role' and 'content'

    Returns:
        Filtered list with proper role alternation (NO CONTENT MERGING)
    """
    if not messages:
        return messages

    result = []
    system_messages = []

    # Extract system messages first
    for msg in messages:
        if msg.get("role") == "system":
            system_messages.append(msg)
        else:
            result.append(msg)

    # Combine system messages (this is safe as they're context, not conversation)
    if system_messages:
        combined_system = {
            "role": "system",
            "content": "\n\n".join(
                msg.get("content", "") for msg in system_messages if msg.get("content")
            ),
        }
        final_result = [combined_system]
    else:
        final_result = []

    # SECURITY FIX: Filter for proper alternation by SELECTION, not merging
    if not result:
        return final_result

    filtered_messages = []
    expected_role = "user"

    for msg in result:
        role = msg.get("role")
        content = msg.get("content", "")

        # Skip empty messages
        if not content or not content.strip():
            logger.debug(f"Skipping empty message with role {role}")
            continue

        if role == expected_role:
            # Expected role - add message and flip expectation
            filtered_messages.append(msg)
            expected_role = "assistant" if role == "user" else "user"
            logger.debug(f"Added {role} message, expecting {expected_role} next")
        else:
            # Role doesn't match expectation - check for consecutive same-role messages first
            if filtered_messages and filtered_messages[-1]["role"] == role:
                # Consecutive same-role messages - replace with most recent
                logger.debug(f"Replacing previous {role} message with more recent one")
                filtered_messages[-1] = msg  # Replace with newer message
                # Keep same expected_role since we just replaced, don't flip
            elif role == "assistant" and expected_role == "user":
                # Assistant message when expecting user - add minimal placeholder
                placeholder = {"role": "user", "content": "[Continuing conversation]"}
                filtered_messages.append(placeholder)
                filtered_messages.append(msg)
                expected_role = "user"
                logger.debug("Added placeholder user message before assistant message")
            else:
                # Other cases - just add the message
                filtered_messages.append(msg)
                expected_role = "assistant" if role == "user" else "user"

    final_result.extend(filtered_messages)

    # Log the filtering for debugging
    logger.debug(
        f"Message alternation filter: {len(messages)} -> {len(final_result)} messages (NO MERGING)"
    )

    return final_result


def extract_text_for_memory_storage(message_content: str, attachments) -> str:
    """
    Extract text content suitable for memory storage, replacing binary data with descriptions

    Args:
        message_content: Original message text content
        attachments: Discord message attachments

    Returns:
        Text content suitable for memory storage (no binary data)
    """
    # Start with the original text content
    storage_content = message_content

    # Process attachments if present
    if attachments:
        # Categorize attachments by MIME type
        attachment_categories = {
            "images": [],
            "text_files": [],
            "documents": [],
            "media": [],
            "archives": [],
            "code": [],
            "other": [],
        }

        # MIME type mappings for better categorization
        mime_categories = {
            # Images
            "image/": "images",
            # Text files
            "text/plain": "text_files",
            "text/markdown": "text_files",
            "text/csv": "text_files",
            "text/html": "text_files",
            "text/css": "text_files",
            "text/javascript": "code",
            "text/xml": "text_files",
            # Documents
            "application/pdf": "documents",
            "application/msword": "documents",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "documents",
            "application/vnd.ms-excel": "documents",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "documents",
            "application/vnd.ms-powerpoint": "documents",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "documents",
            "application/rtf": "documents",
            "application/vnd.oasis.opendocument.text": "documents",
            "application/vnd.oasis.opendocument.spreadsheet": "documents",
            "application/vnd.oasis.opendocument.presentation": "documents",
            # Code files
            "application/json": "code",
            "application/xml": "code",
            "application/javascript": "code",
            "application/x-python-code": "code",
            "application/x-sh": "code",
            # Media
            "audio/": "media",
            "video/": "media",
            # Archives
            "application/zip": "archives",
            "application/x-rar-compressed": "archives",
            "application/x-7z-compressed": "archives",
            "application/gzip": "archives",
            "application/x-tar": "archives",
        }

        # Extension fallbacks for when MIME type isn't available or reliable
        extension_categories = {
            # Text files
            ".txt": "text_files",
            ".md": "text_files",
            ".csv": "text_files",
            ".html": "text_files",
            ".htm": "text_files",
            ".xml": "text_files",
            ".css": "text_files",
            ".yaml": "text_files",
            ".yml": "text_files",
            ".ini": "text_files",
            ".cfg": "text_files",
            ".conf": "text_files",
            ".log": "text_files",
            ".sql": "text_files",
            # Code files
            ".py": "code",
            ".js": "code",
            ".ts": "code",
            ".jsx": "code",
            ".tsx": "code",
            ".java": "code",
            ".cpp": "code",
            ".c": "code",
            ".h": "code",
            ".hpp": "code",
            ".cs": "code",
            ".php": "code",
            ".rb": "code",
            ".go": "code",
            ".rs": "code",
            ".swift": "code",
            ".kt": "code",
            ".scala": "code",
            ".r": "code",
            ".json": "code",
            ".xml": "code",
            ".sh": "code",
            ".bat": "code",
            ".ps1": "code",
            # Documents
            ".pdf": "documents",
            ".doc": "documents",
            ".docx": "documents",
            ".xls": "documents",
            ".xlsx": "documents",
            ".ppt": "documents",
            ".pptx": "documents",
            ".rtf": "documents",
            ".odt": "documents",
            ".ods": "documents",
            ".odp": "documents",
            # Images
            ".jpg": "images",
            ".jpeg": "images",
            ".png": "images",
            ".gif": "images",
            ".bmp": "images",
            ".svg": "images",
            ".webp": "images",
            ".ico": "images",
            ".tiff": "images",
            ".tif": "images",
            # Media
            ".mp3": "media",
            ".wav": "media",
            ".flac": "media",
            ".aac": "media",
            ".mp4": "media",
            ".avi": "media",
            ".mov": "media",
            ".wmv": "media",
            ".mkv": "media",
            ".webm": "media",
            ".m4v": "media",
            # Archives
            ".zip": "archives",
            ".rar": "archives",
            ".7z": "archives",
            ".tar": "archives",
            ".gz": "archives",
            ".bz2": "archives",
            ".xz": "archives",
        }

        # Categorize each attachment
        for att in attachments:
            category = "other"  # default

            # First try MIME type detection (if available)
            if hasattr(att, "content_type") and att.content_type:
                mime_type = att.content_type.lower()

                # Check exact MIME type matches
                if mime_type in mime_categories:
                    category = mime_categories[mime_type]
                else:
                    # Check prefix matches (e.g., 'image/' matches 'image/png')
                    for mime_prefix, cat in mime_categories.items():
                        if mime_prefix.endswith("/") and mime_type.startswith(mime_prefix):
                            category = cat
                            break

            # Fallback to extension-based detection
            if category == "other":
                extension = os.path.splitext(att.filename.lower())[1]
                category = extension_categories.get(extension, "other")

            attachment_categories[category].append(att)

        # Generate descriptions for each category
        descriptions = []

        # Handle images (preserve existing image processing logic)
        if attachment_categories["images"]:
            if len(attachment_categories["images"]) == 1:
                img = attachment_categories["images"][0]
                descriptions.append(f"[Image: {img.filename}]")
            else:
                filenames = [img.filename for img in attachment_categories["images"]]
                descriptions.append(f"[Images: {', '.join(filenames)}]")

        # Handle text files
        if attachment_categories["text_files"]:
            if len(attachment_categories["text_files"]) == 1:
                txt_file = attachment_categories["text_files"][0]
                descriptions.append(f"[Text file: {txt_file.filename}]")
            else:
                filenames = [txt.filename for txt in attachment_categories["text_files"]]
                descriptions.append(f"[Text files: {', '.join(filenames)}]")

        # Handle code files
        if attachment_categories["code"]:
            if len(attachment_categories["code"]) == 1:
                code_file = attachment_categories["code"][0]
                descriptions.append(f"[Code file: {code_file.filename}]")
            else:
                filenames = [code.filename for code in attachment_categories["code"]]
                descriptions.append(f"[Code files: {', '.join(filenames)}]")

        # Handle documents
        if attachment_categories["documents"]:
            if len(attachment_categories["documents"]) == 1:
                doc_file = attachment_categories["documents"][0]
                descriptions.append(f"[Document: {doc_file.filename}]")
            else:
                filenames = [doc.filename for doc in attachment_categories["documents"]]
                descriptions.append(f"[Documents: {', '.join(filenames)}]")

        # Handle media files
        if attachment_categories["media"]:
            if len(attachment_categories["media"]) == 1:
                media_file = attachment_categories["media"][0]
                descriptions.append(f"[Media file: {media_file.filename}]")
            else:
                filenames = [media.filename for media in attachment_categories["media"]]
                descriptions.append(f"[Media files: {', '.join(filenames)}]")

        # Handle archives
        if attachment_categories["archives"]:
            if len(attachment_categories["archives"]) == 1:
                archive_file = attachment_categories["archives"][0]
                descriptions.append(f"[Archive: {archive_file.filename}]")
            else:
                filenames = [arch.filename for arch in attachment_categories["archives"]]
                descriptions.append(f"[Archives: {', '.join(filenames)}]")

        # Handle other/unknown files
        if attachment_categories["other"]:
            if len(attachment_categories["other"]) == 1:
                other_file = attachment_categories["other"][0]
                descriptions.append(f"[File: {other_file.filename}]")
            else:
                filenames = [other.filename for other in attachment_categories["other"]]
                descriptions.append(f"[Files: {', '.join(filenames)}]")

        # Add all descriptions to storage content
        if descriptions:
            storage_content += f"\n{' '.join(descriptions)}"

    # SECURITY FIX: Ensure we don't return empty content
    # If the message content was empty but had attachments, create a meaningful description
    if not storage_content.strip():
        if attachments:
            attachment_count = len(attachments)
            if attachment_count == 1:
                storage_content = f"[Shared file: {attachments[0].filename}]"
            else:
                filenames = [att.filename for att in attachments[:3]]  # Show up to 3 filenames
                if attachment_count > 3:
                    filenames.append(f"and {attachment_count - 3} more")
                storage_content = f"[Shared files: {', '.join(filenames)}]"
        else:
            # Truly empty message - this should be rare
            storage_content = "[Empty message]"

    return storage_content




# REMOVED: get_contextualized_system_prompt function
# This was part of the old adaptive prompt engineering system that has been
# superseded by the CDL character system and vector-native multimodal approach.
