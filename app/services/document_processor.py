import os
import logging
import base64
from typing import Optional, Dict, Any
from pathlib import Path
import mimetypes

# PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# DOCX processing
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# Text file processing is always available

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for extracting text content from various document types"""

    def __init__(self):
        self.supported_types = {
            'application/pdf': self._extract_pdf_text,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': self._extract_docx_text,
            'application/msword': self._extract_docx_text,
            'text/plain': self._extract_text_file,
        }

        # Log availability of optional dependencies
        if not PDF_AVAILABLE:
            logger.warning("PyPDF2 not available - PDF text extraction disabled")
        if not DOCX_AVAILABLE:
            logger.warning("python-docx not available - DOCX text extraction disabled")

    def extract_text(self, file_path: str, mime_type: str = None) -> Optional[str]:
        """Extract text content from a document file"""

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        # Determine MIME type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file_path)

        if not mime_type:
            logger.warning(f"Could not determine MIME type for {file_path}")
            return None

        # Find appropriate extractor
        extractor = self.supported_types.get(mime_type)
        if not extractor:
            logger.warning(f"No text extractor available for MIME type: {mime_type}")
            return None

        try:
            text = extractor(file_path)
            if text:
                # Clean up the text
                text = self._clean_text(text)
                logger.info(f"Extracted {len(text)} characters from {Path(file_path).name}")
                return text
            else:
                logger.warning(f"No text extracted from {file_path}")
                return None

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return None

    def _extract_pdf_text(self, file_path: str) -> Optional[str]:
        """Extract text from PDF files"""
        if not PDF_AVAILABLE:
            logger.error("PyPDF2 not available for PDF processing")
            return None

        try:
            text_content = []

            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_content.append(page_text)
                    except Exception as e:
                        logger.warning(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue

            return '\n\n'.join(text_content) if text_content else None

        except Exception as e:
            logger.error(f"Error reading PDF file: {str(e)}")
            return None

    def _extract_docx_text(self, file_path: str) -> Optional[str]:
        """Extract text from DOCX files"""
        if not DOCX_AVAILABLE:
            logger.error("python-docx not available for DOCX processing")
            return None

        try:
            doc = Document(file_path)
            paragraphs = []

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text)

            return '\n\n'.join(paragraphs) if paragraphs else None

        except Exception as e:
            logger.error(f"Error reading DOCX file: {str(e)}")
            return None

    def _extract_text_file(self, file_path: str) -> Optional[str]:
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"Error reading text file with latin-1 encoding: {str(e)}")
                return None
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            return None

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        if not text:
            return ""

        # Remove excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines

        # Join with single newlines
        cleaned = '\n'.join(lines)

        # Limit text length to prevent overwhelming the AI
        max_length = 5000  # Reasonable limit for AI context
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + "\n... (text truncated)"
            logger.info(f"Text truncated to {max_length} characters")

        return cleaned

    def generate_summary(self, text: str, max_length: int = 500) -> str:
        """Generate a brief summary of the text content"""
        if not text:
            return ""

        # Simple summary: first few sentences up to max_length
        sentences = text.split('. ')
        summary = ""

        for sentence in sentences:
            if len(summary + sentence) <= max_length:
                summary += sentence + ". "
            else:
                break

        return summary.strip()

    def get_document_for_vision_analysis(self, file_path: str, mime_type: str = None, first_page_only: bool = True) -> Optional[str]:
        """Get document as base64 string for AI vision analysis"""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        # Determine MIME type if not provided
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file_path)

        # Only process supported visual formats (PDFs and images)
        visual_types = {
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'image/gif',
            'image/webp'
        }

        if mime_type not in visual_types:
            logger.warning(f"File type {mime_type} not supported for vision analysis")
            return None

        try:
            # For PDFs, extract first page only to reduce size and rate limits
            if mime_type == 'application/pdf' and first_page_only and PDF_AVAILABLE:
                return self._get_pdf_first_page_for_vision(file_path)
            else:
                # For images or full PDFs, use original approach
                with open(file_path, 'rb') as file:
                    file_data = file.read()
                    base64_data = base64.b64encode(file_data).decode('utf-8')
                    logger.info(f"Prepared {Path(file_path).name} for vision analysis ({len(base64_data)} chars)")
                    return base64_data
        except Exception as e:
            logger.error(f"Error reading file for vision analysis: {str(e)}")
            return None

    def _get_pdf_first_page_for_vision(self, file_path: str) -> Optional[str]:
        """Extract first page of PDF as image for vision analysis"""
        try:
            # Try to use pdf2image if available (more efficient)
            try:
                from pdf2image import convert_from_path
                import io

                # Convert first page only to reduce size
                images = convert_from_path(file_path, first_page=1, last_page=1, dpi=200)

                if images:
                    # Convert PIL image to bytes
                    img_buffer = io.BytesIO()
                    images[0].save(img_buffer, format='PNG', optimize=True)
                    img_data = img_buffer.getvalue()

                    base64_data = base64.b64encode(img_data).decode('utf-8')
                    logger.info(f"Extracted first page of PDF for vision analysis ({len(base64_data)} chars)")
                    return base64_data
            except ImportError:
                logger.info("pdf2image not available, falling back to full PDF")

            # Fallback: use full PDF but log the size concern
            with open(file_path, 'rb') as file:
                file_data = file.read()
                base64_data = base64.b64encode(file_data).decode('utf-8')

                # Warn if PDF is very large
                if len(base64_data) > 1000000:  # ~1MB base64
                    logger.warning(f"Large PDF for vision analysis: {len(base64_data)} chars - may hit rate limits")

                logger.info(f"Using full PDF for vision analysis ({len(base64_data)} chars)")
                return base64_data

        except Exception as e:
            logger.error(f"Error extracting PDF for vision analysis: {str(e)}")
            return None

# Global document processor instance
document_processor = DocumentProcessor()