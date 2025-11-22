import os
import aiohttp
import aiofiles
from pathlib import Path
from typing import List, Optional
from loguru import logger
from llama_index.core import SimpleDirectoryReader, Document

class DocumentProcessor:
    def __init__(self, temp_dir: str = "temp_downloads"):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def process_local_file(self, file_path: Path) -> str:
        """
        Extracts text from a local file using LlamaIndex.
        """
        try:
            # 2. Parse with LlamaIndex
            # SimpleDirectoryReader supports many formats (pdf, txt, docx, etc.)
            # We point it to the specific file
            reader = SimpleDirectoryReader(input_files=[str(file_path)])
            
            # Run in executor to avoid blocking the event loop
            import asyncio
            loop = asyncio.get_running_loop()
            documents = await loop.run_in_executor(None, reader.load_data)
            
            # 3. Combine text
            full_text = "\n\n".join([doc.text for doc in documents])
            
            logger.info(f"Extracted {len(full_text)} characters from {file_path.name}")
            return full_text
        except Exception as e:
            logger.error(f"LlamaIndex extraction failed for {file_path.name}: {e}")
            raise e

    async def process_attachment(self, attachment_url: str, filename: str) -> str:
        """
        Downloads a file from a URL and extracts its text content using LlamaIndex.
        """
        file_path = self.temp_dir / filename
        
        try:
            # 1. Download the file
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment_url) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to download file: {resp.status}")
                        return f"Error: Could not download file {filename}."
                    
                    async with aiofiles.open(file_path, mode='wb') as f:
                        await f.write(await resp.read())
            
            logger.info(f"Downloaded file to {file_path}")

            return await self.process_local_file(file_path)

        except Exception as e:
            logger.error(f"Failed to process document {filename}: {e}")
            return f"Error processing file {filename}: {str(e)}"
            
        finally:
            # Cleanup
            if file_path.exists():
                try:
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete temp file: {e}")

# Global instance
document_processor = DocumentProcessor()
