"""
Sistema LIA - Modelo de Usuário SIMPLIFICADO
============================================
Usa FastAPI-Users (auth completo pronto!)

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from fastapi_users.db import SQLAlchemyBaseUserTable
from app.database import Base
from app.utils.datetime_utils import now_brasilia


class User(SQLAlchemyBaseUserTable[int], Base):
    """
    Modelo de Usuário - Compatível com FastAPI-Users
    Herda tudo de SQLAlchemyBaseUserTable: id, email, hashed_password, is_active, is_verified, is_superuser
    """
    __tablename__ = "usuarios"
    
    # Primary Key (explicit declaration to prevent mapper conflicts)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Campos customizados do TRE-GO
    nome = Column(String(200), nullable=False)
    cargo = Column(String(100), nullable=True)
    setor = Column(String(200), nullable=True)  # Seção/Unidade onde o usuário está lotado
    grupo = Column(String(100), nullable=True)  # TIC, SAO, GAB, etc
    perfil = Column(String(50), default="operador", nullable=False)  # admin, operador, visualizador
    
    # Timestamps
    data_criacao = Column(DateTime, default=now_brasilia, nullable=False)
    ultimo_acesso = Column(DateTime, nullable=True)
    
    # Relacionamentos
    projetos = relationship("Projeto", back_populates="usuario", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="usuario", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', nome='{self.nome}')>"
    
    def to_dict(self):
        """Converte para dict (sem senha)"""
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "cargo": self.cargo,
            "setor": self.setor,
            "grupo": self.grupo,
            "perfil": self.perfil,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "is_verified": self.is_verified,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            "ultimo_acesso": self.ultimo_acesso.isoformat() if self.ultimo_acesso else None,
        }
