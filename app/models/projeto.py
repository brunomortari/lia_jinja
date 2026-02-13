"""
Sistema LIA - Modelo de Projeto
================================
Define a estrutura da tabela de projetos de contratação

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, inspect, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.utils.datetime_utils import now_brasilia


class Projeto(Base):
    """
    Modelo de Projeto de Contratação
    
    Representa um projeto de contratação que pode envolver um ou mais itens do PAC.
    Cada projeto passa por etapas de elaboração de artefatos (DFD, ETP, TR, etc).
    """
    __tablename__ = "projetos"
    
    # ========== IDENTIFICAÇÃO ==========
    
    id = Column(Integer, primary_key=True, index=True, comment="ID único do projeto")
    
    titulo = Column(
        String(300),
        nullable=False,
        comment="Título descritivo do projeto"
    )
    
    descricao = Column(
        Text,
        nullable=True,
        comment="Descrição detalhada do projeto"
    )
    
    # ========== RELACIONAMENTO COM USUÁRIO ==========
    
    usuario_id = Column(
        Integer,
        ForeignKey("usuarios.id"),
        nullable=False,
        comment="ID do usuário que criou o projeto"
    )
    
    # ========== PROMPT INICIAL DA IA ==========
    
    prompt_inicial = Column(
        Text,
        nullable=True,
        comment="Prompt inicial fornecido pelo usuário para a IA"
    )
    
    # ========== ITENS DO PAC VINCULADOS ==========

    itens_pac = Column(
        JSON,
        nullable=True,
        comment="Lista de itens PAC: [{'id': 8, 'quantidade': 100}, ...]. Quantidade é específica do projeto."
    )

    intra_pac = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="True para projetos dentro do PAC (intra-PAC), False para fora do PAC (extra-PAC)"
    )

    # ========== INTEGRAÇÃO SEI ==========
    
    protocolo_sei = Column(
        JSON,
        nullable=True,
        comment="Dados do protocolo SEI: numero, assunto, link, etc."
    )
    
    # ========== STATUS E ARQUIVAMENTO ==========
    
    arquivado = Column(
        Integer, # Usando Integer como booleano (0/1) para compatibilidade simples ou Boolean se o banco suportar nativo
        default=0,
        nullable=False,
        comment="Define se o projeto está arquivado (1) ou ativo (0)"
    )
    
    # ========== STATUS DO PROJETO ==========
    
    status = Column(
        String(50),
        default="rascunho",
        nullable=False,
        comment="Status: rascunho, em_andamento, concluido, cancelado"
    )
    
    # ========== TIMESTAMPS ==========
    
    data_criacao = Column(
        DateTime,
        default=now_brasilia,
        nullable=False,
        comment="Data de criação do projeto"
    )

    data_atualizacao = Column(
        DateTime,
        default=now_brasilia,
        onupdate=now_brasilia,
        nullable=False,
        comment="Data da última atualização"
    )
    
    data_conclusao = Column(
        DateTime,
        nullable=True,
        comment="Data de conclusão do projeto"
    )
    
    # ========== RELACIONAMENTOS ==========
    
    # Relacionamento com usuário (muitos projetos para um usuário)
    usuario = relationship("User", back_populates="projetos")
    
    # Justificativa de Excepcionalidade (quando projeto não tem PAC)
    justificativas_excepcionalidade = relationship("JustificativaExcepcionalidade", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(JustificativaExcepcionalidade.data_criacao)", foreign_keys="JustificativaExcepcionalidade.projeto_id")

    # Relacionamento com DFDs (um projeto pode ter vários DFDs)
    dfds = relationship("DFD", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(DFD.data_criacao)")
    
    # Relacionamento com Riscos (um projeto pode ter vários Riscos/PGRs)
    riscos = relationship("Riscos", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(Riscos.data_criacao)")
    
    # Novos Artefatos (1:N - multiplas versoes)
    etps = relationship("ETP", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(ETP.data_criacao)")
    trs = relationship("TR", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(TR.data_criacao)")
    editais = relationship("Edital", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(Edital.data_criacao)")

    # Pesquisas de Precos (documento versionado)
    pesquisas_precos = relationship("PesquisaPrecos", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(PesquisaPrecos.data_criacao)")

    # Portarias de Designação (documento virtual vinculado a DFD aprovado)
    portarias_designacao = relationship("PortariaDesignacao", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(PortariaDesignacao.data_criacao)")

    # Fluxo de Adesão a Ata de Registro de Preços
    relatorios_vantagem_economica = relationship("RelatorioVantagemEconomica", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(RelatorioVantagemEconomica.data_criacao)", foreign_keys="RelatorioVantagemEconomica.projeto_id")
    justificativas_vantagem_adesao = relationship("JustificativaVantagemAdesao", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(JustificativaVantagemAdesao.data_criacao)", foreign_keys="JustificativaVantagemAdesao.projeto_id")
    termos_aceite_fornecedor = relationship("TermoAceiteFornecedorOrgao", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(TermoAceiteFornecedorOrgao.data_criacao)", foreign_keys="TermoAceiteFornecedorOrgao.projeto_id")

    # Fluxo de Dispensa por Valor Baixo
    trs_simplificados = relationship("TRSimplificado", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(TRSimplificado.data_criacao)", foreign_keys="TRSimplificado.projeto_id")
    avisos_dispensa_eletronica = relationship("AvisoDispensaEletronica", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(AvisoDispensaEletronica.data_criacao)", foreign_keys="AvisoDispensaEletronica.projeto_id")
    justificativas_preco_escolha = relationship("JustificativaPrecoEscolhaFornecedor", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(JustificativaPrecoEscolhaFornecedor.data_criacao)", foreign_keys="JustificativaPrecoEscolhaFornecedor.projeto_id")
    certidoes_enquadramento = relationship("CertidaoEnquadramento", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(CertidaoEnquadramento.data_criacao)", foreign_keys="CertidaoEnquadramento.projeto_id")

    # Fluxo de Licitação Normal
    checklists_conformidade = relationship("ChecklistConformidade", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(ChecklistConformidade.data_criacao)", foreign_keys="ChecklistConformidade.projeto_id")
    minutas_contrato = relationship("MinutaContrato", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(MinutaContrato.data_criacao)", foreign_keys="MinutaContrato.projeto_id")

    # Fluxo de Contratação Direta (Dispensa/Inexigibilidade)
    avisos_publicidade_direta = relationship("AvisoPublicidadeDireta", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(AvisoPublicidadeDireta.data_criacao)", foreign_keys="AvisoPublicidadeDireta.projeto_id")
    justificativas_fornecedor_escolhido = relationship("JustificativaFornecedorEscolhido", back_populates="projeto", cascade="all, delete-orphan", order_by="desc(JustificativaFornecedorEscolhido.data_criacao)", foreign_keys="JustificativaFornecedorEscolhido.projeto_id")

    def _is_relationship_loaded(self, attr_name: str) -> bool:
        """Verifica se um relacionamento foi carregado (eager loading)"""
        return attr_name not in inspect(self).unloaded

    def _safe_relationship_check(self, attr_name: str) -> bool | None:
        """
        Verifica se existe pelo menos um item no relacionamento.
        Retorna None se o relacionamento não foi carregado (evita lazy loading).
        """
        if not self._is_relationship_loaded(attr_name):
            return None
        val = getattr(self, attr_name)
        return len(val) > 0 if val else False

    # ========== PROPERTIES DINÂMICAS: FLUXO PRINCIPAL ==========
    
    @property
    def tem_dfd(self):
        """Verifica se o projeto tem pelo menos um DFD"""
        return self._safe_relationship_check('dfds')

    @property
    def tem_etp(self):
        """Verifica se o projeto tem pelo menos um ETP"""
        return self._safe_relationship_check('etps')

    @property
    def tem_pp(self):
        """Verifica se o projeto tem Pesquisa de Preços"""
        return self._safe_relationship_check('pesquisas_precos')

    @property
    def tem_pgr(self):
        """Verifica se o projeto tem PGR (Plano de Gerenciamento de Riscos)"""
        return self._safe_relationship_check('riscos')

    @property
    def tem_riscos(self):
        """Alias para tem_pgr (compatibilidade)"""
        return self.tem_pgr

    @property
    def tem_tr(self):
        """Verifica se o projeto tem Termo de Referência"""
        return self._safe_relationship_check('trs')

    @property
    def tem_edital(self):
        """Verifica se o projeto tem Edital"""
        return self._safe_relationship_check('editais')

    @property
    def tem_pd(self):
        """Verifica se o projeto tem Portaria de Designação"""
        return self._safe_relationship_check('portarias_designacao')

    # ========== PROPERTIES DINÂMICAS: ADESÃO A ATA ==========

    @property
    def tem_rdve(self):
        """Verifica se o projeto tem Relatório de Vantagem Econômica"""
        return self._safe_relationship_check('relatorios_vantagem_economica')

    @property
    def tem_jva(self):
        """Verifica se o projeto tem Justificativa de Vantagem da Adesão"""
        return self._safe_relationship_check('justificativas_vantagem_adesao')

    @property
    def tem_tafo(self):
        """Verifica se o projeto tem Termo de Aceite Fornecedor/Órgão"""
        return self._safe_relationship_check('termos_aceite_fornecedor')

    # ========== PROPERTIES DINÂMICAS: DISPENSA VALOR BAIXO ==========

    @property
    def tem_trs(self):
        """Verifica se o projeto tem TR Simplificado"""
        return self._safe_relationship_check('trs_simplificados')

    @property
    def tem_ade(self):
        """Verifica se o projeto tem Aviso de Dispensa Eletrônica"""
        return self._safe_relationship_check('avisos_dispensa_eletronica')

    @property
    def tem_jpef(self):
        """Verifica se o projeto tem Justificativa Preço/Escolha Fornecedor"""
        return self._safe_relationship_check('justificativas_preco_escolha')

    @property
    def tem_ce(self):
        """Verifica se o projeto tem Certidão de Enquadramento"""
        return self._safe_relationship_check('certidoes_enquadramento')

    # ========== PROPERTIES DINÂMICAS: LICITAÇÃO NORMAL ==========

    @property
    def tem_chk(self):
        """Verifica se o projeto tem Checklist de Conformidade"""
        return self._safe_relationship_check('checklists_conformidade')

    @property
    def tem_mc(self):
        """Verifica se o projeto tem Minuta de Contrato"""
        return self._safe_relationship_check('minutas_contrato')

    # ========== PROPERTIES DINÂMICAS: CONTRATAÇÃO DIRETA ==========

    @property
    def tem_apd(self):
        """Verifica se o projeto tem Aviso de Publicidade Direta"""
        return self._safe_relationship_check('avisos_publicidade_direta')

    @property
    def tem_jfe(self):
        """Verifica se o projeto tem Justificativa Fornecedor Escolhido"""
        return self._safe_relationship_check('justificativas_fornecedor_escolhido')

    def __repr__(self):
        return f"<Projeto(id={self.id}, titulo='{self.titulo}', status='{self.status}')>"

    def to_dict(self):
        """
        Converte o objeto para dicionário.

        Usa as properties que já verificam se os relacionamentos foram
        carregados, evitando lazy loading em contextos assíncronos.
        """
        # usuario_nome só se o relacionamento estiver carregado
        usuario_nome = None
        if self._is_relationship_loaded('usuario') and self.usuario:
            usuario_nome = self.usuario.nome

        return {
            "id": self.id,
            "titulo": self.titulo,
            "descricao": self.descricao,
            "usuario_id": self.usuario_id,
            "usuario_nome": usuario_nome,
            "prompt_inicial": self.prompt_inicial,
            "itens_pac": self.itens_pac,
            "intra_pac": bool(self.intra_pac),  # Converter 1/0 para True/False
            "status": self.status,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            "data_atualizacao": self.data_atualizacao.isoformat() if self.data_atualizacao else None,
            "data_conclusao": self.data_conclusao.isoformat() if self.data_conclusao else None,
            "arquivado": bool(self.arquivado),
            "protocolo_sei": self.protocolo_sei,
            # Fluxo Principal (7 artefatos)
            "tem_dfd": self.tem_dfd,
            "tem_etp": self.tem_etp,
            "tem_pp": self.tem_pp,
            "tem_pgr": self.tem_pgr,
            "tem_riscos": self.tem_riscos,  # alias
            "tem_tr": self.tem_tr,
            "tem_edital": self.tem_edital,
            "tem_pd": self.tem_pd,
            # Adesão a Ata (3 artefatos)
            "tem_rdve": self.tem_rdve,
            "tem_jva": self.tem_jva,
            "tem_tafo": self.tem_tafo,
            # Dispensa Valor Baixo (4 artefatos)
            "tem_trs": self.tem_trs,
            "tem_ade": self.tem_ade,
            "tem_jpef": self.tem_jpef,
            "tem_ce": self.tem_ce,
            # Licitação Normal (2 artefatos)
            "tem_chk": self.tem_chk,
            "tem_mc": self.tem_mc,
            # Contratação Direta (2 artefatos)
            "tem_apd": self.tem_apd,
            "tem_jfe": self.tem_jfe,
        }
