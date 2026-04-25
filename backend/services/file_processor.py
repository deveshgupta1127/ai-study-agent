import pymupdf
import docx2txt
from pathlib import Path
import logging

logger=logging.getLogger(__name__)

def extract_text(file_path:str, file_type:str)->str:
    """ Extract text from PDF, DOCX, or TXT files. 
    Args: 
    file_path (str): Path to the file 
    file_type (str): 'pdf' | 'docx' | 'txt' 
    
    Returns: 
    str: Extracted cleaned text 
    
    Raises: 
    ValueError: Unsupported file type or empty content 
    FileNotFoundError: File does not exist 
    Exception: Any parsing-related failure 
    """

    path=Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found:{file_path}")
    
    file_type=file_type.lower()

    try:
        if file_type=="pdf":
            text=_extract_pdf(path)

        elif file_type=="docx":
            text=_extract_docx(path)
        
        elif file_type=="txt":
            text=_extract_txt(path)
        
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        raise
    
    cleaned_text=_clean_text(text)

    if len(cleaned_text)<50:
        raise ValueError("Document is too small or empty after extrcation")
    
    return cleaned_text

def _extract_pdf(path: Path)->str:
    try:
        doc=pymupdf,open(str(path))
        text=[]

        for page in doc:
            page_text=page.get_text()
            if page_text:
                text.append(page_text)
        
        doc.close()
        return "\n".join(text)
    except Exception as e:
        raise Exception(f"Failed to parse pdf: {str(e)}")

def _extract_docx(path:Path)->str:
    try:
        return docx2txt.process(str(path)) or ""
    except Exception as e:
        raise Exception(f"Failed to parse DOCX: {str(e)}")

def _extract_txt(path:Path)-> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
    except Exception as e:
        raise Exception(f"Failed to parse TXT: {str(e)}")


def _clean_text(text:str)->str:
    if not text:
        return ""
    
    text=text.replace("\r","\n")
    lines=[line.strip() for line in text.split("\n") if line.strip()]

    cleaned="\n".join(lines)
    return cleaned