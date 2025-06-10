"""
Módulo de processadores de documentos
"""
from .xml_processor import XMLProcessor
from .pdf_processor import PDFProcessor
from .image_processor import ImageProcessor

__all__ = [
    "XMLProcessor",
    "PDFProcessor", 
    "ImageProcessor"
]

