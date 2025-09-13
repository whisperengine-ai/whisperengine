"""
Image processing module for Discord message attachments
"""
import os
import io
import base64
import aiohttp
import aiofiles
import logging
from typing import Optional, Dict, List, Any, Tuple
from PIL import Image
from src.utils.exceptions import ValidationError

class ImageProcessor:
    """Handles image processing for Discord attachments"""
    
    # Supported image formats
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    # Maximum image size in bytes (10MB)
    MAX_IMAGE_SIZE = 10 * 1024 * 1024
    
    # Maximum image dimensions for processing
    MAX_WIDTH = 2048
    MAX_HEIGHT = 2048
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the image processor
        
        Args:
            temp_dir: Directory to store temporary image files
        """
        if temp_dir is None:
            temp_dir = os.getenv('TEMP_IMAGES_DIR', 'temp_images')
        self.temp_dir = temp_dir
        self.logger = logging.getLogger(__name__)
        
        # Create temp directory if it doesn't exist
        os.makedirs(temp_dir, exist_ok=True)
        self.logger.debug(f"ImageProcessor initialized with temp_dir: {temp_dir}")
    
    def is_supported_image(self, filename: str) -> bool:
        """
        Check if the file is a supported image format
        
        Args:
            filename: Name of the file to check
            
        Returns:
            True if the file is a supported image format
        """
        if not filename:
            return False
        
        extension = os.path.splitext(filename.lower())[1]
        is_supported = extension in self.SUPPORTED_FORMATS
        self.logger.debug(f"Image support check for '{filename}': {is_supported} (extension: {extension})")
        return is_supported
    
    async def download_image(self, url: str, max_size: Optional[int] = None) -> Optional[bytes]:
        """
        Download an image from a URL
        
        Args:
            url: URL of the image to download
            max_size: Maximum size in bytes (defaults to MAX_IMAGE_SIZE)
            
        Returns:
            Image data as bytes, or None if download failed
        """
        if max_size is None:
            max_size = self.MAX_IMAGE_SIZE
        
        self.logger.debug(f"Downloading image from URL: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        self.logger.warning(f"Failed to download image: HTTP {response.status}")
                        return None
                    
                    # Check content length
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_size:
                        self.logger.warning(f"Image too large: {content_length} bytes (max: {max_size})")
                        return None
                    
                    # Download with size limit
                    image_data = b""
                    async for chunk in response.content.iter_chunked(8192):
                        image_data += chunk
                        if len(image_data) > max_size:
                            self.logger.warning(f"Image exceeded size limit during download: {len(image_data)} bytes")
                            return None
                    
                    self.logger.debug(f"Successfully downloaded image: {len(image_data)} bytes")
                    return image_data
        
        except Exception as e:
            self.logger.error(f"Error downloading image: {e}")
            return None
    
    def resize_image_if_needed(self, image_data: bytes) -> bytes:
        """
        Resize image if it exceeds maximum dimensions
        
        Args:
            image_data: Original image data
            
        Returns:
            Resized image data (or original if no resize needed)
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                original_size = img.size
                
                # Check if resize is needed
                if img.width <= self.MAX_WIDTH and img.height <= self.MAX_HEIGHT:
                    self.logger.debug(f"Image size OK: {original_size}")
                    return image_data
                
                # Calculate new size maintaining aspect ratio
                ratio = min(self.MAX_WIDTH / img.width, self.MAX_HEIGHT / img.height)
                new_size = (int(img.width * ratio), int(img.height * ratio))
                
                self.logger.info(f"Resizing image from {original_size} to {new_size}")
                
                # Resize image
                resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
                
                # Convert to RGB if necessary (for JPEG)
                if resized_img.mode != 'RGB':
                    resized_img = resized_img.convert('RGB')
                
                # Save to bytes
                output = io.BytesIO()
                resized_img.save(output, format='JPEG', quality=85, optimize=True)
                resized_data = output.getvalue()
                
                self.logger.debug(f"Resized image: {len(image_data)} -> {len(resized_data)} bytes")
                return resized_data
        
        except Exception as e:
            self.logger.error(f"Error resizing image: {e}")
            return image_data  # Return original if resize fails
    
    def encode_image_for_llm(self, image_data: bytes, format: str = "jpeg") -> str:
        """
        Encode image data as base64 for LLM input
        
        Args:
            image_data: Image data as bytes
            format: Image format (jpeg, png, etc.)
            
        Returns:
            Base64 encoded image string with data URI prefix
        """
        try:
            # Resize if needed
            processed_data = self.resize_image_if_needed(image_data)
            
            # Encode to base64
            base64_data = base64.b64encode(processed_data).decode('utf-8')
            
            # Create data URI
            mime_type = f"image/{format.lower()}"
            data_uri = f"data:{mime_type};base64,{base64_data}"
            
            self.logger.debug(f"Encoded image for LLM: {len(base64_data)} base64 characters")
            return data_uri
        
        except Exception as e:
            self.logger.error(f"Error encoding image for LLM: {e}")
            raise ValidationError(f"Failed to encode image: {str(e)}")
    
    async def process_discord_attachment(self, attachment) -> Optional[Dict[str, Any]]:
        """
        Process a Discord attachment for LLM input
        
        Args:
            attachment: Discord attachment object
            
        Returns:
            Dictionary with image data and metadata, or None if processing failed
        """
        if not self.is_supported_image(attachment.filename):
            self.logger.debug(f"Skipping non-image attachment: {attachment.filename}")
            return None
        
        if attachment.size > self.MAX_IMAGE_SIZE:
            self.logger.warning(f"Image too large: {attachment.filename} ({attachment.size} bytes)")
            return None
        
        self.logger.info(f"Processing image attachment: {attachment.filename} ({attachment.size} bytes)")
        
        # Download the image
        image_data = await self.download_image(attachment.url)
        if not image_data:
            return None
        
        try:
            # Get image format from filename
            extension = os.path.splitext(attachment.filename.lower())[1]
            format_name = extension[1:] if extension.startswith('.') else 'jpeg'
            
            # Handle special cases
            if format_name in ['jpg']:
                format_name = 'jpeg'
            
            # Encode for LLM
            encoded_image = self.encode_image_for_llm(image_data, format_name)
            
            return {
                'filename': attachment.filename,
                'size': len(image_data),
                'format': format_name,
                'encoded_data': encoded_image,
                'original_url': attachment.url
            }
        
        except Exception as e:
            self.logger.error(f"Error processing image attachment {attachment.filename}: {e}")
            return None
    
    async def process_multiple_attachments(self, attachments) -> List[Dict[str, Any]]:
        """
        Process multiple Discord attachments
        
        Args:
            attachments: List of Discord attachment objects
            
        Returns:
            List of processed image data dictionaries
        """
        processed_images = []
        
        for attachment in attachments:
            result = await self.process_discord_attachment(attachment)
            if result:
                processed_images.append(result)
        
        self.logger.info(f"Processed {len(processed_images)} images from {len(attachments)} attachments")
        return processed_images
    
    def get_image_description_prompt(self, images: List[Dict[str, Any]]) -> str:
        """
        Generate a prompt describing the attached images
        
        Args:
            images: List of processed image data
            
        Returns:
            Descriptive prompt for the LLM
        """
        if not images:
            return ""
        
        if len(images) == 1:
            img = images[0]
            return f"[User attached an image: {img['filename']} ({img['format'].upper()}, {img['size']} bytes)]"
        else:
            filenames = [img['filename'] for img in images]
            return f"[User attached {len(images)} images: {', '.join(filenames)}]"
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                os.makedirs(self.temp_dir, exist_ok=True)
            self.logger.debug("Cleaned up temporary image files")
        except Exception as e:
            self.logger.warning(f"Failed to cleanup temp files: {e}")
