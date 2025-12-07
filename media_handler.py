import os
import shutil
import mimetypes
from datetime import datetime
from typing import Dict, List, Optional, Tuple, BinaryIO
import aiofiles
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import io
import base64
from logger import Logger
from config import Config

class MediaHandler:
    """Advanced Media Handling System v15.0.00"""
    
    def __init__(self):
        self.config = Config()
        self.logger = Logger.get_logger(__name__)
        
        # Media directories
        self.media_dirs = {
            'images': 'media/images',
            'videos': 'media/videos',
            'audio': 'media/audio',
            'documents': 'media/documents',
            'thumbnails': 'media/thumbnails',
            'temp': 'media/temp'
        }
        
        # Create directories
        for directory in self.media_dirs.values():
            os.makedirs(directory, exist_ok=True)
        
        # Supported media types
        self.supported_formats = {
            'images': ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'],
            'videos': ['mp4', 'avi', 'mov', 'mkv', 'webm'],
            'audio': ['mp3', 'wav', 'ogg', 'm4a'],
            'documents': ['pdf', 'doc', 'docx', 'txt', 'csv', 'xlsx']
        }
        
        # Maximum file sizes (in bytes)
        self.max_sizes = {
            'images': 10 * 1024 * 1024,      # 10 MB
            'videos': 50 * 1024 * 1024,      # 50 MB
            'audio': 20 * 1024 * 1024,       # 20 MB
            'documents': 5 * 1024 * 1024     # 5 MB
        }
        
        # Image processing settings
        self.image_settings = {
            'thumbnail_size': (200, 200),
            'preview_size': (800, 600),
            'quality': 85,
            'watermark_text': f"© {self.config.BOT_NAME}",
            'watermark_position': 'bottom-right'
        }
        
        self.logger.info("📁 Media Handler v15.0.00 Initialized")
    
    async def save_media(self, file_data: bytes, filename: str, 
                        media_type: str = 'auto') -> Dict:
        """Save media file with validation"""
        try:
            # Detect media type if auto
            if media_type == 'auto':
                media_type = self._detect_media_type(filename)
            
            # Validate media type
            if media_type not in self.supported_formats:
                return {
                    'success': False,
                    'message': f'অসমর্থিত মিডিয়া টাইপ: {media_type}'
                }
            
            # Get file extension
            file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
            
            # Check if extension is supported
            if file_ext not in self.supported_formats[media_type]:
                return {
                    'success': False,
                    'message': f'অসমর্থিত ফাইল ফরম্যাট: .{file_ext}'
                }
            
            # Check file size
            file_size = len(file_data)
            if file_size > self.max_sizes[media_type]:
                max_mb = self.max_sizes[media_type] / (1024 * 1024)
                return {
                    'success': False,
                    'message': f'ফাইল খুব বড়! সর্বোচ্চ {max_mb}MB ফাইল আপলোড করতে পারবেন'
                }
            
            # Generate unique filename
            unique_filename = self._generate_unique_filename(filename, media_type)
            file_path = os.path.join(self.media_dirs[media_type], unique_filename)
            
            # Save file
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_data)
            
            # Get file info
            file_info = await self._get_file_info(file_path, media_type)
            
            # Create thumbnail for images
            thumbnail_path = None
            if media_type == 'images':
                thumbnail_path = await self.create_thumbnail(file_path)
            
            # Create preview for images
            preview_path = None
            if media_type == 'images':
                preview_path = await self.create_preview(file_path)
            
            self.logger.info(f"Media saved: {unique_filename} ({file_size:,} bytes)")
            
            return {
                'success': True,
                'message': 'মিডিয়া সফলভাবে সেভ হয়েছে',
                'file_info': {
                    'filename': unique_filename,
                    'original_name': filename,
                    'type': media_type,
                    'size': file_size,
                    'path': file_path,
                    'thumbnail': thumbnail_path,
                    'preview': preview_path,
                    'url': self._get_file_url(unique_filename, media_type),
                    **file_info
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save media: {e}")
            return {
                'success': False,
                'message': f'মিডিয়া সেভ ব্যর্থ: {str(e)}'
            }
    
    async def create_thumbnail(self, image_path: str, size: Tuple[int, int] = None) -> Optional[str]:
        """Create thumbnail for an image"""
        try:
            if size is None:
                size = self.image_settings['thumbnail_size']
            
            # Open image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create thumbnail
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create output path
                filename = os.path.basename(image_path)
                thumb_filename = f"thumb_{filename}"
                thumb_path = os.path.join(self.media_dirs['thumbnails'], thumb_filename)
                
                # Save thumbnail
                img.save(thumb_path, 'JPEG', quality=self.image_settings['quality'])
                
                self.logger.debug(f"Thumbnail created: {thumb_path}")
                return thumb_path
            
        except Exception as e:
            self.logger.error(f"Failed to create thumbnail: {e}")
            return None
    
    async def create_preview(self, image_path: str, size: Tuple[int, int] = None) -> Optional[str]:
        """Create preview image with watermark"""
        try:
            if size is None:
                size = self.image_settings['preview_size']
            
            with Image.open(image_path) as img:
                # Convert to RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize for preview
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Add watermark
                img = await self._add_watermark(img)
                
                # Create output path
                filename = os.path.basename(image_path)
                preview_filename = f"preview_{filename}"
                preview_path = os.path.join(self.media_dirs['thumbnails'], preview_filename)
                
                # Save preview
                img.save(preview_path, 'JPEG', quality=self.image_settings['quality'])
                
                self.logger.debug(f"Preview created: {preview_path}")
                return preview_path
            
        except Exception as e:
            self.logger.error(f"Failed to create preview: {e}")
            return None
    
    async def _add_watermark(self, image: Image.Image) -> Image.Image:
        """Add watermark to image"""
        try:
            # Create a copy to work with
            watermarked = image.copy()
            
            # Get image dimensions
            width, height = watermarked.size
            
            # Create drawing context
            draw = ImageDraw.Draw(watermarked)
            
            # Try to load font, fallback to default
            try:
                # You need to have a font file in your system
                font = ImageFont.truetype("arial.ttf", 20)
            except:
                # Use default font
                font = ImageFont.load_default()
            
            # Get watermark text
            watermark = self.image_settings['watermark_text']
            
            # Calculate text size
            text_bbox = draw.textbbox((0, 0), watermark, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Calculate position based on settings
            position = self.image_settings['watermark_position']
            
            if position == 'bottom-right':
                x = width - text_width - 10
                y = height - text_height - 10
            elif position == 'top-left':
                x = 10
                y = 10
            elif position == 'center':
                x = (width - text_width) // 2
                y = (height - text_height) // 2
            else:  # bottom-right default
                x = width - text_width - 10
                y = height - text_height - 10
            
            # Add semi-transparent background for watermark
            bg_padding = 5
            draw.rectangle(
                [x - bg_padding, y - bg_padding, 
                 x + text_width + bg_padding, y + text_height + bg_padding],
                fill=(0, 0, 0, 128)  # Semi-transparent black
            )
            
            # Add watermark text
            draw.text((x, y), watermark, font=font, fill=(255, 255, 255, 255))
            
            return watermarked
            
        except Exception as e:
            self.logger.error(f"Failed to add watermark: {e}")
            return image  # Return original image if watermark fails
    
    async def compress_image(self, image_path: str, quality: int = None) -> Optional[str]:
        """Compress image to reduce file size"""
        try:
            if quality is None:
                quality = self.image_settings['quality']
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Create output path
                filename = os.path.basename(image_path)
                compressed_filename = f"compressed_{filename}"
                compressed_path = os.path.join(self.media_dirs['temp'], compressed_filename)
                
                # Save compressed image
                img.save(compressed_path, 'JPEG', quality=quality, optimize=True)
                
                # Get file sizes
                original_size = os.path.getsize(image_path)
                compressed_size = os.path.getsize(compressed_path)
                
                # Calculate compression ratio
                compression_ratio = ((original_size - compressed_size) / original_size) * 100
                
                self.logger.info(
                    f"Image compressed: {compressed_size:,} bytes "
                    f"({compression_ratio:.1f}% reduction)"
                )
                
                return compressed_path
            
        except Exception as e:
            self.logger.error(f"Failed to compress image: {e}")
            return None
    
    async def convert_image_format(self, image_path: str, target_format: str) -> Optional[str]:
        """Convert image to different format"""
        try:
            supported_formats = ['jpg', 'jpeg', 'png', 'webp']
            
            if target_format.lower() not in supported_formats:
                return None
            
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    if target_format.lower() in ['jpg', 'jpeg']:
                        img = img.convert('RGB')
                
                # Create output path
                filename = os.path.splitext(os.path.basename(image_path))[0]
                converted_filename = f"{filename}.{target_format}"
                converted_path = os.path.join(self.media_dirs['temp'], converted_filename)
                
                # Save in new format
                img.save(converted_path, target_format.upper(), 
                        quality=self.image_settings['quality'], optimize=True)
                
                self.logger.info(f"Image converted to {target_format}: {converted_path}")
                return converted_path
            
        except Exception as e:
            self.logger.error(f"Failed to convert image: {e}")
            return None
    
    async def extract_metadata(self, file_path: str) -> Dict:
        """Extract metadata from media file"""
        try:
            metadata = {
                'filename': os.path.basename(file_path),
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                'created': datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                'mime_type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            }
            
            # Try to extract image metadata
            if metadata['mime_type'].startswith('image/'):
                with Image.open(file_path) as img:
                    metadata.update({
                        'format': img.format,
                        'mode': img.mode,
                        'size': img.size,
                        'width': img.width,
                        'height': img.height,
                        'info': img.info
                    })
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Failed to extract metadata: {e}")
            return {}
    
    async def get_media_list(self, media_type: str = None, 
                           limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get list of media files"""
        try:
            media_list = []
            
            if media_type:
                # Specific media type
                if media_type in self.media_dirs:
                    media_dir = self.media_dirs[media_type]
                    files = os.listdir(media_dir)
                    
                    for filename in files[offset:offset + limit]:
                        file_path = os.path.join(media_dir, filename)
                        
                        if os.path.isfile(file_path):
                            file_info = await self._get_file_info(file_path, media_type)
                            media_list.append({
                                'filename': filename,
                                'type': media_type,
                                'path': file_path,
                                'url': self._get_file_url(filename, media_type),
                                **file_info
                            })
            else:
                # All media types
                for media_type, media_dir in self.media_dirs.items():
                    if os.path.exists(media_dir):
                        files = os.listdir(media_dir)
                        
                        for filename in files[:limit]:
                            file_path = os.path.join(media_dir, filename)
                            
                            if os.path.isfile(file_path):
                                file_info = await self._get_file_info(file_path, media_type)
                                media_list.append({
                                    'filename': filename,
                                    'type': media_type,
                                    'path': file_path,
                                    'url': self._get_file_url(filename, media_type),
                                    **file_info
                                })
            
            # Sort by modification time (newest first)
            media_list.sort(key=lambda x: x.get('modified', ''), reverse=True)
            
            return media_list[:limit]
            
        except Exception as e:
            self.logger.error(f"Failed to get media list: {e}")
            return []
    
    async def delete_media(self, filename: str, media_type: str) -> Dict:
        """Delete media file"""
        try:
            file_path = os.path.join(self.media_dirs[media_type], filename)
            
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'message': 'ফাইল খুঁজে পাওয়া যায়নি'
                }
            
            # Delete the file
            os.remove(file_path)
            
            # Delete associated thumbnails/previews
            thumbnail_path = os.path.join(self.media_dirs['thumbnails'], f"thumb_{filename}")
            preview_path = os.path.join(self.media_dirs['thumbnails'], f"preview_{filename}")
            
            for path in [thumbnail_path, preview_path]:
                if os.path.exists(path):
                    os.remove(path)
            
            self.logger.info(f"Media deleted: {filename}")
            
            return {
                'success': True,
                'message': 'মিডিয়া ডিলিট করা হয়েছে'
            }
            
        except Exception as e:
            self.logger.error(f"Failed to delete media: {e}")
            return {
                'success': False,
                'message': f'ডিলিট ব্যর্থ: {str(e)}'
            }
    
    async def cleanup_temp_files(self, hours_old: int = 24):
        """Cleanup temporary files older than specified hours"""
        try:
            temp_dir = self.media_dirs['temp']
            if not os.path.exists(temp_dir):
                return 0
            
            cutoff_time = datetime.now().timestamp() - (hours_old * 3600)
            deleted_count = 0
            
            for filename in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, filename)
                
                if os.path.isfile(file_path):
                    file_mtime = os.path.getmtime(file_path)
                    
                    if file_mtime < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_count += 1
                        except Exception as e:
                            self.logger.error(f"Failed to delete temp file {filename}: {e}")
            
            self.logger.info(f"🧹 Cleaned up {deleted_count} temp files")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup temp files: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        stats = {
            'total_files': 0,
            'total_size': 0,
            'by_type': {},
            'free_space': 0
        }
        
        try:
            # Calculate for each media type
            for media_type, media_dir in self.media_dirs.items():
                if os.path.exists(media_dir):
                    type_stats = {
                        'count': 0,
                        'size': 0
                    }
                    
                    for filename in os.listdir(media_dir):
                        file_path = os.path.join(media_dir, filename)
                        
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            
                            type_stats['count'] += 1
                            type_stats['size'] += file_size
                            
                            stats['total_files'] += 1
                            stats['total_size'] += file_size
                    
                    stats['by_type'][media_type] = type_stats
            
            # Get free disk space
            try:
                import shutil
                total, used, free = shutil.disk_usage(os.path.dirname(self.media_dirs['images']))
                stats['free_space'] = free
                stats['total_space'] = total
                stats['used_space'] = used
                stats['used_percentage'] = (used / total) * 100
            except:
                pass
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get storage stats: {e}")
            return stats
    
    async def create_image_from_text(self, text: str, 
                                   size: Tuple[int, int] = (400, 200),
                                   bg_color: str = '#3498db',
                                   text_color: str = '#ffffff') -> Optional[str]:
        """Create image from text"""
        try:
            # Create image
            image = Image.new('RGB', size, bg_color)
            draw = ImageDraw.Draw(image)
            
            # Try to load font
            try:
                font_size = min(size) // 10
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (size[0] - text_width) // 2
            y = (size[1] - text_height) // 2
            
            # Draw text
            draw.text((x, y), text, font=font, fill=text_color)
            
            # Save image
            filename = f"text_{int(time.time())}.jpg"
            file_path = os.path.join(self.media_dirs['images'], filename)
            
            image.save(file_path, 'JPEG', quality=self.image_settings['quality'])
            
            self.logger.info(f"Text image created: {filename}")
            return file_path
            
        except Exception as e:
            self.logger.error(f"Failed to create text image: {e}")
            return None
    
    async def image_to_base64(self, image_path: str) -> Optional[str]:
        """Convert image to base64 string"""
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Get mime type
            mime_type = mimetypes.guess_type(image_path)[0] or 'image/jpeg'
            
            # Encode to base64
            base64_str = base64.b64encode(image_data).decode('utf-8')
            
            return f"data:{mime_type};base64,{base64_str}"
            
        except Exception as e:
            self.logger.error(f"Failed to convert image to base64: {e}")
            return None
    
    # Helper methods
    def _detect_media_type(self, filename: str) -> str:
        """Detect media type from filename"""
        ext = filename.split('.')[-1].lower() if '.' in filename else ''
        
        for media_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return media_type
        
        return 'documents'  # Default
    
    def _generate_unique_filename(self, original_name: str, media_type: str) -> str:
        """Generate unique filename"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_str = os.urandom(4).hex()
        
        # Get extension
        if '.' in original_name:
            ext = original_name.split('.')[-1].lower()
        else:
            ext = self.supported_formats[media_type][0]
        
        return f"{timestamp}_{random_str}.{ext}"
    
    async def _get_file_info(self, file_path: str, media_type: str) -> Dict:
        """Get file information"""
        try:
            stats = os.stat(file_path)
            
            return {
                'size': stats.st_size,
                'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stats.st_ctime).isoformat(),
                'mime_type': mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            }
        except:
            return {}
    
    def _get_file_url(self, filename: str, media_type: str) -> str:
        """Generate file URL (for API responses)"""
        # In production, this would return actual URL
        # For now, return path
        return f"/media/{media_type}/{filename}"
    
    async def validate_image(self, image_path: str) -> Dict:
        """Validate image file"""
        try:
            with Image.open(image_path) as img:
                # Check image size
                width, height = img.size
                
                # Check for minimum dimensions
                if width < 50 or height < 50:
                    return {
                        'valid': False,
                        'message': 'ছবি খুব ছোট! ন্যূনতম 50x50 পিক্সেল প্রয়োজন'
                    }
                
                # Check for maximum dimensions
                max_dimension = 5000
                if width > max_dimension or height > max_dimension:
                    return {
                        'valid': False,
                        'message': f'ছবি খুব বড়! সর্বোচ্চ {max_dimension}x{max_dimension} পিক্সেল'
                    }
                
                # Check file size
                file_size = os.path.getsize(image_path)
                if file_size > self.max_sizes['images']:
                    max_mb = self.max_sizes['images'] / (1024 * 1024)
                    return {
                        'valid': False,
                        'message': f'ছবি খুব বড়! সর্বোচ্চ {max_mb}MB'
                    }
                
                return {
                    'valid': True,
                    'message': 'ছবি বৈধ',
                    'dimensions': {'width': width, 'height': height},
                    'format': img.format,
                    'mode': img.mode,
                    'size': file_size
                }
                
        except Exception as e:
            return {
                'valid': False,
                'message': f'ছবি ভ্যালিডেশন ব্যর্থ: {str(e)}'
            }
    
    async def batch_process_images(self, image_paths: List[str], 
                                 operation: str = 'compress') -> List[Dict]:
        """Batch process multiple images"""
        results = []
        
        for image_path in image_paths:
            try:
                if operation == 'compress':
                    result_path = await self.compress_image(image_path)
                    operation_name = 'কমপ্রেস'
                elif operation == 'thumbnail':
                    result_path = await self.create_thumbnail(image_path)
                    operation_name = 'থাম্বনেইল'
                elif operation == 'preview':
                    result_path = await self.create_preview(image_path)
                    operation_name = 'প্রিভিউ'
                else:
                    result_path = None
                    operation_name = 'প্রক্রিয়া'
                
                if result_path:
                    results.append({
                        'original': image_path,
                        'processed': result_path,
                        'success': True,
                        'operation': operation_name
                    })
                else:
                    results.append({
                        'original': image_path,
                        'success': False,
                        'error': f'{operation_name} ব্যর্থ'
                    })
                    
            except Exception as e:
                results.append({
                    'original': image_path,
                    'success': False,
                    'error': str(e)
                })
        
        return results