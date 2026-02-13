""" 
Sistema LIA - Base Classes para Artefatos
==========================================
Classe base abstrata para todos os artefatos do sistema LIA.

Fornece:
- Campos comuns (id, versao, status, datas, etc)
- Métodos de workflow (aprovar, publicar, alterar_status)
- Métodos de versionamento (clonar, próxima versão)
- Métodos de auditoria (registrar edições, gerações IA)
- Queries comuns como classmethods

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, select
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.database import Base
from app.utils.datetime_utils import now_brasilia, BRASILIA_TZ

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class ArtefatoBloqueadoError(Exception):
    """Artefato publicado no SEI não pode ser modificado."""
    pass


class ArtefatoBase(Base):
    """
    Classe base abstrata para todos os artefatos do sistema LIA.
    
    Fornece funcionalidades comuns de workflow, versionamento e auditoria.
    """
    __abstract__ = True

    # ========== CAMPOS COMUNS ==========
    id = Column(Integer, primary_key=True, index=True)
    versao = Column(Integer, default=1, nullable=False)
    status = Column(String(50), default="rascunho", nullable=False)
    
    # IA e Auditoria
    gerado_por_ia = Column(Boolean, default=False)
    prompt_ia = Column(Text, nullable=True)
    metadata_ia = Column(JSON, nullable=True)
    campos_editados = Column(JSON, nullable=True)
    campos_regenerados = Column(JSON, nullable=True)

    # Timestamps
    data_criacao = Column(DateTime, default=now_brasilia)
    data_atualizacao = Column(DateTime, default=now_brasilia, onupdate=now_brasilia)
    data_aprovacao = Column(DateTime, nullable=True)
    
    # Integração SEI
    protocolo_sei = Column(JSON, nullable=True, comment="Protocolo de publicação no SEI")

    # Campos que não devem ser clonados
    _CAMPOS_NAO_CLONADOS = {'id', 'versao', 'status', 'data_criacao', 'data_atualizacao', 
                            'data_aprovacao', 'protocolo_sei', 'projeto'}

    # ========== PROPRIEDADES ==========
    
    @property
    def esta_bloqueado(self) -> bool:
        """Retorna True se artefato está bloqueado (publicado no SEI)."""
        return self.protocolo_sei is not None
    
    @property
    def pode_editar(self) -> bool:
        """Retorna True se artefato pode ser editado."""
        return not self.esta_bloqueado and self.status not in ('publicado',)
    
    @property
    def esta_aprovado(self) -> bool:
        """Retorna True se artefato está aprovado ou publicado."""
        return self.status in ('aprovado', 'publicado')

    # ========== MÉTODOS DE WORKFLOW ==========
    
    def validar_edicao(self) -> None:
        """Lança exceção se artefato está bloqueado para edição."""
        if self.esta_bloqueado:
            raise ArtefatoBloqueadoError(
                f"Artefato {self.__class__.__name__} (id={self.id}) publicado no SEI não pode ser modificado."
            )
    
    def alterar_status(self, novo_status: str) -> None:
        """
        Transição de status com atualização automática de timestamps.
        
        Status válidos: rascunho, em_revisao, aprovado, rejeitado, publicado
        """
        status_validos = {'rascunho', 'em_revisao', 'aprovado', 'rejeitado', 'publicado'}
        if novo_status not in status_validos:
            raise ValueError(f"Status inválido: {novo_status}. Válidos: {status_validos}")
        
        if novo_status == 'aprovado':
            self.data_aprovacao = now_brasilia()
        
        self.status = novo_status
        self.data_atualizacao = now_brasilia()
    
    def aprovar(self) -> None:
        """Aprova o artefato."""
        self.alterar_status('aprovado')
    
    def rejeitar(self) -> None:
        """Rejeita o artefato, voltando para rascunho."""
        self.alterar_status('rascunho')
        self.data_aprovacao = None
    
    def publicar_sei(self, numero_protocolo: str, assunto: str, link: str = None) -> None:
        """
        Registra publicação no SEI e bloqueia artefato para edições.
        
        Args:
            numero_protocolo: Número do processo SEI
            assunto: Assunto do documento
            link: URL para o documento no SEI
        """
        self.protocolo_sei = {
            "numero": numero_protocolo,
            "assunto": assunto,
            "data_autuacao": now_brasilia().strftime("%Y-%m-%d"),
            "status": "publicado",
            "link": link or f"https://sei.tre-go.jus.br/sei/protocolo/{numero_protocolo}"
        }
        self.alterar_status('publicado')

    # ========== MÉTODOS DE EDIÇÃO ==========
    
    def atualizar_campos(self, dados: Dict[str, Any], campos_permitidos: List[str] = None) -> List[str]:
        """
        Atualiza campos do artefato dinamicamente.
        
        Args:
            dados: Dicionário com campos e valores
            campos_permitidos: Lista de campos permitidos (None = todos)
            
        Returns:
            Lista de campos atualizados
        """
        self.validar_edicao()
        campos_atualizados = []
        
        for campo, valor in dados.items():
            if campos_permitidos and campo not in campos_permitidos:
                continue
            if hasattr(self, campo) and campo not in self._CAMPOS_NAO_CLONADOS:
                setattr(self, campo, valor)
                campos_atualizados.append(campo)
        
        if campos_atualizados:
            self.data_atualizacao = now_brasilia()
        
        return campos_atualizados
    
    def registrar_edicao_campo(self, campo: str) -> None:
        """Registra que um campo foi editado manualmente pelo usuário."""
        campos = self.campos_editados or []
        if campo not in campos:
            campos.append(campo)
        self.campos_editados = campos
        self.data_atualizacao = now_brasilia()
    
    def registrar_regeneracao_campo(self, campo: str, prompt: str = None) -> None:
        """Registra que um campo foi regenerado por IA."""
        regeneracoes = self.campos_regenerados or []
        regeneracoes.append({
            "campo": campo,
            "data": now_brasilia().isoformat(),
            "prompt": prompt
        })
        self.campos_regenerados = regeneracoes
        self.data_atualizacao = now_brasilia()
    
    def registrar_geracao_ia(self, prompt: str = None, metadata: Dict[str, Any] = None) -> None:
        """Registra que o artefato foi gerado/atualizado por IA."""
        self.gerado_por_ia = True
        if prompt:
            self.prompt_ia = prompt
        if metadata:
            self.metadata_ia = {**(self.metadata_ia or {}), **metadata}
        self.data_atualizacao = now_brasilia()

    # ========== MÉTODOS DE VERSIONAMENTO ==========
    
    def clonar_para_nova_versao(self, nova_versao: int) -> "ArtefatoBase":
        """
        Cria uma cópia do artefato como rascunho na nova versão.
        
        Args:
            nova_versao: Número da nova versão
            
        Returns:
            Nova instância do artefato clonado
        """
        dados = self.to_dict()
        
        # Remover campos que não devem ser clonados
        for campo in self._CAMPOS_NAO_CLONADOS:
            dados.pop(campo, None)
        
        # Definir nova versão e status
        dados['versao'] = nova_versao
        dados['status'] = 'rascunho'
        dados['projeto_id'] = getattr(self, 'projeto_id', None)
        
        # Limpar campos de auditoria
        dados['campos_editados'] = None
        dados['campos_regenerados'] = None
        
        return self.__class__(**dados)
    
    def to_versao_resumida(self) -> Dict[str, Any]:
        """Retorna resumo do artefato para listagem de versões."""
        return {
            "id": self.id,
            "versao": self.versao,
            "status": self.status,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            "data_atualizacao": self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            "gerado_por_ia": self.gerado_por_ia,
            "publicado_sei": self.esta_bloqueado
        }

    # ========== MÉTODOS DE CLASSE (QUERIES) ==========
    
    @classmethod
    async def proxima_versao(cls, projeto_id: int, db: AsyncSession) -> int:
        """Retorna o número da próxima versão disponível para o projeto."""
        result = await db.execute(
            select(cls.versao)
            .filter(cls.projeto_id == projeto_id)
            .order_by(cls.versao.desc())
            .limit(1)
        )
        ultima = result.scalar()
        return (ultima or 0) + 1
    
    @classmethod
    async def buscar_versao_ativa(cls, projeto_id: int, db: AsyncSession) -> Optional["ArtefatoBase"]:
        """Busca a versão aprovada/publicada do artefato no projeto."""
        result = await db.execute(
            select(cls)
            .filter(cls.projeto_id == projeto_id)
            .filter(cls.status.in_(['aprovado', 'publicado']))
            .order_by(cls.versao.desc())
            .limit(1)
        )
        return result.scalars().first()
    
    @classmethod
    async def tem_versao_aprovada(cls, projeto_id: int, db: AsyncSession, excluir_id: int = None) -> bool:
        """Verifica se existe versão aprovada/publicada do artefato no projeto."""
        query = select(cls.id).filter(
            cls.projeto_id == projeto_id,
            cls.status.in_(['aprovado', 'publicado'])
        )
        if excluir_id:
            query = query.filter(cls.id != excluir_id)
        
        result = await db.execute(query.limit(1))
        return result.scalar() is not None
    
    @classmethod
    async def listar_versoes(cls, projeto_id: int, db: AsyncSession) -> List[Dict[str, Any]]:
        """Retorna histórico de todas as versões do artefato no projeto."""
        result = await db.execute(
            select(cls)
            .filter(cls.projeto_id == projeto_id)
            .order_by(cls.versao.desc())
        )
        artefatos = result.scalars().all()
        return [a.to_versao_resumida() for a in artefatos]

    # ========== SERIALIZAÇÃO ==========
    
    def __getitem__(self, key):
        """Permite acesso via artefato['campo'] no template Jinja2."""
        return getattr(self, key, None)

    def to_dict(self, include_relations: bool = False, campos: List[str] = None) -> Dict[str, Any]:
        """
        Serializa o artefato para dicionário.
        
        Args:
            include_relations: Se True, inclui relacionamentos
            campos: Lista de campos específicos (None = todos)
            
        Returns:
            Dicionário com dados do artefato
        """
        if campos:
            d = {c: getattr(self, c, None) for c in campos if hasattr(self, c)}
        else:
            d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        
        # Formatar datas para ISO
        for campo in ['data_criacao', 'data_atualizacao', 'data_aprovacao']:
            if campo in d and d[campo]:
                d[campo] = d[campo].isoformat()
        
        return d
    
    def to_json(self) -> str:
        """Serializa o artefato para JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False, default=str)
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(id={self.id}, versao={self.versao}, status='{self.status}')>"
