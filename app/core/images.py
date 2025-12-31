import asyncio
from pathlib import Path
from io import BytesIO
from PIL import Image
import aiofiles
from fastapi import UploadFile
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
import hashlib
import os

logger = logging.getLogger(__name__)


@dataclass
class ImageVariant:
    format: str  # 'webp', 'avif', 'jpg'
    width: int
    height: int
    quality: int
    path: str


class ImageProcessor:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # Define image variants to generate
        self.variants = [
            # Thumbnail
            {"format": "webp", "width": 200, "height": 200, "quality": 80, "suffix": "_thumb"},
            {"format": "avif", "width": 200, "height": 200, "quality": 80, "suffix": "_thumb"},
            {"format": "jpg", "width": 200, "height": 200, "quality": 80, "suffix": "_thumb"},
            # Medium
            {"format": "webp", "width": 800, "height": 800, "quality": 85, "suffix": "_medium"},
            {"format": "avif", "width": 800, "height": 800, "quality": 85, "suffix": "_medium"},
            {"format": "jpg", "width": 800, "height": 800, "quality": 85, "suffix": "_medium"},
            # Large
            {"format": "webp", "width": 1920, "height": 1920, "quality": 90, "suffix": "_large"},
            {"format": "avif", "width": 1920, "height": 1920, "quality": 90, "suffix": "_large"},
            {"format": "jpg", "width": 1920, "height": 1920, "quality": 90, "suffix": "_large"},
        ]

    def _generate_filename(self, original_name: str, variant: dict) -> str:
        """Generate filename for image variant."""
        name_without_ext = Path(original_name).stem
        return f"{name_without_ext}{variant['suffix']}.{variant['format']}"

    def _calculate_hash(self, content: bytes) -> str:
        """Calculate MD5 hash of image content."""
        return hashlib.md5(content).hexdigest()

    async def process_image(self, file: UploadFile) -> dict:
        """Process uploaded image and generate all variants."""
        try:
            # Read file content
            content = await file.read()

            # Calculate hash for unique identifier
            file_hash = self._calculate_hash(content)

            # Create directory for this image
            image_dir = self.upload_dir / file_hash
            image_dir.mkdir(exist_ok=True)

            # Save original
            original_path = image_dir / file.filename
            async with aiofiles.open(original_path, 'wb') as f:
                await f.write(content)

            # Open image with PIL
            image = Image.open(BytesIO(content))

            # Convert RGBA to RGB if needed (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')

            # Generate variants
            variants_created = []

            for variant in self.variants:
                try:
                    # Resize image maintaining aspect ratio
                    img_copy = image.copy()
                    img_copy.thumbnail((variant['width'], variant['height']), Image.Resampling.LANCZOS)

                    # Generate filename
                    filename = self._generate_filename(file.filename, variant)
                    variant_path = image_dir / filename

                    # Save in specified format
                    save_kwargs = {'quality': variant['quality']}

                    if variant['format'] == 'webp':
                        img_copy.save(variant_path, 'WEBP', **save_kwargs)
                    elif variant['format'] == 'avif':
                        # Note: PIL may need AVIF support compiled in
                        try:
                            img_copy.save(variant_path, 'AVIF', **save_kwargs)
                        except:
                            # Fallback to WebP if AVIF not supported
                            img_copy.save(variant_path.with_suffix('.webp'), 'WEBP', **save_kwargs)
                            variant_path = variant_path.with_suffix('.webp')
                    else:  # jpg
                        img_copy.save(variant_path, 'JPEG', **save_kwargs)

                    variants_created.append(
                        {
                            "format": variant['format'],
                            "width": img_copy.width,
                            "height": img_copy.height,
                            "quality": variant['quality'],
                            "path": str(variant_path.relative_to(self.upload_dir)),
                            "size": variant_path.stat().st_size,
                            "suffix": variant['suffix'],
                        }
                    )

                except Exception as e:
                    logger.error(f"Failed to create variant {variant}: {e}")
                    continue

            return {
                "original_name": file.filename,
                "hash": file_hash,
                "original_path": str(original_path.relative_to(self.upload_dir)),
                "variants": variants_created,
                "total_size": sum(v['size'] for v in variants_created),
            }

        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            raise

    async def delete_image(self, image_hash: str):
        """Delete all files for an image."""
        image_dir = self.upload_dir / image_hash
        if image_dir.exists():
            import shutil

            shutil.rmtree(image_dir)
            return True
        return False

    def get_image_urls(self, image_hash: str, original_name: str) -> dict:
        """Generate URLs for all image variants."""
        base_url = "/uploads"
        image_dir = Path(image_hash)

        urls = {"original": f"{base_url}/{image_dir}/{original_name}", "variants": {}}

        for variant in self.variants:
            filename = self._generate_filename(original_name, variant)
            urls["variants"][variant['suffix'][1:]] = {variant['format']: f"{base_url}/{image_dir}/{filename}"}

        return urls


# Global instance
image_processor = ImageProcessor()
