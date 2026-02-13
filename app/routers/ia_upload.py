"""
Router para Upload de Arquivos para IA
======================================
Gerencia o upload de arquivos (imagens, PDFs) para uso no contexto da IA.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import os
import shutil
import uuid
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings

router = APIRouter(prefix="/api/ia-upload", tags=["IA Utils"])

# Configuração de diretório de upload temporário
UPLOAD_DIR = Path("tmp/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class UploadResponse(BaseModel):
    file_id: str
    filename: str
    content_type: str
    size: int
    url: Optional[str] = None
    extracted_text: Optional[str] = None

@router.post("/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """
    Faz upload de um arquivo para uso no contexto da IA.
    Suporta Imagens (PNG, JPG) e PDF.
    """
    
    # Validar tipo de arquivo
    allowed_types = [
        "image/jpeg", "image/png", "image/webp", 
        "application/pdf", 
        "text/plain", "text/markdown", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # Alguns browsers enviam markdown como text/x-markdown ou vazios, entao validamos extensao tambem
    filename_lower = file.filename.lower()
    is_markdown = filename_lower.endswith('.md')
    is_docx = filename_lower.endswith('.docx')
    
    if file.content_type not in allowed_types and not (is_markdown or is_docx):
         # Logar para debug se necessario, mas por hora apenas rejeitar se nao for compativel
         pass
         # raise HTTPException(status_code=400, detail=f"Tipo de arquivo não suportado. Permitidos: {', '.join(allowed_types)}")
    
    # Validar tamanho (ex: 10MB)
    MAX_SIZE = 10 * 1024 * 1024
    
    # Gerar ID único
    file_id = str(uuid.uuid4())
    extension = Path(file.filename).suffix
    safe_filename = f"{file_id}{extension}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # Salvar arquivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        file_size = file_path.stat().st_size
        if file_size > MAX_SIZE:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Arquivo muito grande (max 10MB)")

        extracted_text = None
        content_type = file.content_type

        # Normalizar content type baseada na extensao se necessario
        if is_markdown: content_type = "text/markdown"
        if is_docx: content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        # Se for PDF
        if content_type == "application/pdf":
            try:
                import fitz  # pymupdf
                doc = fitz.open(str(file_path))
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                extracted_text = text.strip()
            except ImportError:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                text = ""
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"
                extracted_text = text.strip()
            except Exception as e:
                print(f"Erro PDF: {e}")
        
        # Se for Texto ou Markdown
        elif content_type in ["text/plain", "text/markdown"] or is_markdown:
             with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                 extracted_text = f.read()

        # Se for DOCX
        elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or is_docx:
            try:
                import docx
                doc = docx.Document(file_path)
                extracted_text = "\n".join([para.text for para in doc.paragraphs])
            except Exception as e:
                 print(f"Erro DOCX: {e}")
                 extracted_text = f"Erro ao ler DOCX: {str(e)}"

        # URL para servir o arquivo (se necessário, para o frontend mostrar preview)
        # Por enquanto, assumimos que o frontend usa URL.createObjectURL para preview local
        # e o backend usa o caminho físico ou base64 para mandar pra IA.
        
        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            content_type=file.content_type,
            size=file_size,
            url=f"/static/uploads/{safe_filename}", # Exemplo hipotético
            extracted_text=extracted_text
        )

    except Exception as e:
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erro ao salvar arquivo: {str(e)}")
