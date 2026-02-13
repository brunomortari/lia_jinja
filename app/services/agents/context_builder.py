"""
Context Builder - Construtor de contexto compartilhado para agents
Elimina duplicação nos métodos build_user_prompt/build_generate_prompt
"""
import json
from typing import Dict, Any, List


class ContextBuilder:
    """
    Classe utilitária para construir blocos de contexto padronizados
    que são reutilizados pelos agents.
    
    Uso:
        builder = ContextBuilder(contexto)
        parts = [
            "TÍTULO DO DOCUMENTO",
            "",
            builder.projeto(),
            builder.setor(),
            builder.itens_pac(),
            builder.dfd(),
            builder.pesquisa_precos(),
        ]
        prompt = "\n".join(filter(None, parts))
    """
    
    def __init__(self, contexto: Dict[str, Any]):
        """
        Args:
            contexto: Dicionário com dados do projeto, DFD, pesquisa, etc.
        """
        self.contexto = contexto
    
    def projeto(self) -> str:
        """Retorna linha com título do projeto."""
        titulo = self.contexto.get("projeto_titulo", "")
        if titulo:
            return f"PROJETO: {titulo}"
        return ""
    
    def setor(self) -> str:
        """Retorna linha com setor requisitante."""
        setor = self.contexto.get("setor_usuario", "Unidade Requisitante")
        return f"SETOR REQUISITANTE: {setor}"
    
    def valor_estimado(self) -> str:
        """Retorna linha com valor estimado."""
        valor = self.contexto.get("valor_estimado", "")
        if valor and valor != "N/A":
            return f"VALOR ESTIMADO: {valor}"
        return ""
    
    def itens_pac(self) -> str:
        """Retorna bloco com itens do PAC se existirem."""
        itens = self.contexto.get("itens_pac", [])
        if itens:
            return f"\nITENS DO PAC: {json.dumps(itens, ensure_ascii=False)}"
        return ""
    
    def dfd(self) -> str:
        """Retorna bloco com dados do DFD se existir."""
        dfd = self.contexto.get("dfd", {})
        if not dfd:
            return ""
        
        lines = ["\nDADOS DO DFD:"]
        
        if dfd.get("justificativa_tecnica"):
            lines.append(f"- Justificativa: {dfd['justificativa_tecnica']}")
        
        if dfd.get("descricao_objeto_padronizada"):
            lines.append(f"- Objeto: {dfd['descricao_objeto_padronizada']}")
        
        if dfd.get("prioridade_sugerida"):
            lines.append(f"- Prioridade: {dfd['prioridade_sugerida']}")
        
        if dfd.get("data_pretendida"):
            lines.append(f"- Data Pretendida: {dfd['data_pretendida']}")
        
        return "\n".join(lines) if len(lines) > 1 else ""
    
    def pesquisa_precos(self) -> str:
        """Retorna bloco com dados da pesquisa de preços se existir."""
        pesquisa = self.contexto.get("pesquisa_precos", {})
        if not pesquisa:
            return ""
        
        lines = ["\nDADOS DA PESQUISA DE PREÇOS:"]
        
        if pesquisa.get("valor_total"):
            valor = pesquisa["valor_total"]
            lines.append(f"- Valor Total Estimado: R$ {valor:,.2f}")
        
        if pesquisa.get("quantidade_fornecedores"):
            qtd = pesquisa["quantidade_fornecedores"]
            lines.append(f"- Fornecedores Consultados: {qtd}")
        
        if pesquisa.get("coeficiente_variacao"):
            cv = pesquisa["coeficiente_variacao"]
            lines.append(f"- Coeficiente de Variação: {cv:.1f}%")
        
        if pesquisa.get("itens"):
            lines.append(f"- Itens Cotados: {len(pesquisa['itens'])}")
        
        return "\n".join(lines) if len(lines) > 1 else ""
    
    def etp(self) -> str:
        """Retorna bloco com dados do ETP se existir."""
        etp = self.contexto.get("etp", {})
        if not etp:
            return ""
        
        lines = ["\nDADOS DO ETP:"]
        
        if etp.get("descricao_necessidade"):
            lines.append(f"- Necessidade: {etp['descricao_necessidade'][:200]}...")
        
        if etp.get("descricao_solucao"):
            lines.append(f"- Solução: {etp['descricao_solucao'][:200]}...")
        
        if etp.get("estimativa_valor"):
            lines.append(f"- Estimativa: {etp['estimativa_valor']}")
        
        return "\n".join(lines) if len(lines) > 1 else ""
    
    def riscos(self) -> str:
        """Retorna bloco com sumário de riscos se existir."""
        riscos = self.contexto.get("riscos", {})
        if not riscos or not riscos.get("itens_risco"):
            return ""
        
        itens = riscos.get("itens_risco", [])
        lines = [f"\nRISCOS IDENTIFICADOS: {len(itens)} riscos"]
        
        # Contar por nível de severidade (prob * impacto)
        altos = sum(1 for r in itens if r.get("probabilidade", 0) * r.get("impacto", 0) >= 12)
        medios = sum(1 for r in itens if 6 <= r.get("probabilidade", 0) * r.get("impacto", 0) < 12)
        baixos = len(itens) - altos - medios
        
        if altos:
            lines.append(f"- Riscos Altos: {altos}")
        if medios:
            lines.append(f"- Riscos Médios: {medios}")
        if baixos:
            lines.append(f"- Riscos Baixos: {baixos}")
        
        return "\n".join(lines) if len(lines) > 1 else ""
    
    def atribuicoes(self) -> str:
        """Retorna bloco com atribuições regimentais do setor."""
        atrib = self.contexto.get("contexto_atribuicoes", "")
        if atrib:
            return f"\nATRIBUIÇÕES REGIMENTAIS DO SETOR:\n{atrib}"
        return ""
    
    def input_usuario(self) -> str:
        """Retorna o input/descrição fornecido pelo usuário."""
        input_txt = self.contexto.get("input_usuario") or self.contexto.get("descricao_necessidade", "")
        if input_txt:
            return f"\nDESCRIÇÃO DO USUÁRIO:\n{input_txt}"
        return ""
    
    def modalidade(self) -> str:
        """Retorna a modalidade de licitação se especificada."""
        mod = self.contexto.get("modalidade", "")
        if mod:
            return f"\nMODALIDADE: {mod}"
        return ""
    
    def criterio_julgamento(self) -> str:
        """Retorna o critério de julgamento se especificado."""
        criterio = self.contexto.get("criterio_julgamento", "")
        if criterio:
            return f"CRITÉRIO DE JULGAMENTO: {criterio}"
        return ""
    
    def regime_execucao(self) -> str:
        """Retorna o regime de execução se especificado."""
        regime = self.contexto.get("regime_execucao", "")
        if regime:
            return f"REGIME DE EXECUÇÃO: {regime}"
        return ""
    
    def build_header(self, titulo_documento: str) -> str:
        """
        Constrói um header padrão para documentos.
        
        Args:
            titulo_documento: Ex: "ELABORAR ESTUDO TÉCNICO PRELIMINAR"
        
        Returns:
            String com header formatado
        """
        parts = [
            titulo_documento,
            "",
            self.projeto(),
            self.setor(),
        ]
        
        valor = self.valor_estimado()
        if valor:
            parts.append(valor)
        
        return "\n".join(filter(None, parts))
    
    def build_all_context(self, include_campos: List[str] = None) -> str:
        """
        Constrói todos os blocos de contexto disponíveis.
        
        Args:
            include_campos: Lista de campos a incluir. Se None, inclui todos.
                           Ex: ["dfd", "pesquisa_precos", "etp"]
        
        Returns:
            String com todos os blocos concatenados
        """
        all_blocks = {
            "itens_pac": self.itens_pac,
            "dfd": self.dfd,
            "pesquisa_precos": self.pesquisa_precos,
            "etp": self.etp,
            "riscos": self.riscos,
            "atribuicoes": self.atribuicoes,
            "input_usuario": self.input_usuario,
            "modalidade": self.modalidade,
            "criterio_julgamento": self.criterio_julgamento,
            "regime_execucao": self.regime_execucao,
        }
        
        if include_campos:
            blocks = [all_blocks[campo]() for campo in include_campos if campo in all_blocks]
        else:
            blocks = [fn() for fn in all_blocks.values()]
        
        return "\n".join(filter(None, blocks))
