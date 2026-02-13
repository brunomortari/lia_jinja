"""
Sistema LIA - Agente Base
=========================
Classe base para todos os agentes de IA.
Usa OpenAI SDK com OpenRouter como backend.

Autor: Equipe TRE-GO
Data: Janeiro 2026
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional, List
from openai import AsyncOpenAI

from app.config import settings
from app.database import AsyncSessionLocal
from .prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Classe base abstrata para agentes de IA.
    
    Cada agente deve implementar:
    - agent_type: Tipo do agente para buscar prompt no banco (ex: "dfd", "etp")
    - build_user_prompt(): Construir o prompt do usuário com contexto
    - campos: Lista de campos que o agente gera
    
    O system_prompt agora é carregado do banco na primeira geração.
    """
    
    # Configurações padrão (podem ser sobrescritas por subclasses)
    temperature: float = 0.5
    max_tokens: int = 8192
    model: str = None  # Usa settings.OPENROUTER_DEFAULT_MODEL se None
    
    # Tipo do agente para buscar prompt no banco (definido em cada subclasse)
    agent_type: str = ""
    
    # Prompt do sistema (carregado do banco na primeira geração)
    system_prompt: str = ""
    _prompt_loaded: bool = False
    
    # Lista de campos que este agente gera
    campos: List[str] = []
    
    def __init__(self, model_override: Optional[str] = None):
        """Inicializa o cliente OpenAI apontando para OpenRouter. Permite override do modelo."""
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.OPENROUTER_TIMEOUT,
        )
        # Se o usuário selecionou um modelo, usa ele; senão, usa o default
        self.model = model_override or self.model or settings.OPENROUTER_DEFAULT_MODEL
    
    async def _load_prompt(self):
        """Carrega o system_prompt do banco se ainda não foi carregado."""
        if self._prompt_loaded or not self.agent_type:
            return
        
        try:
            async with AsyncSessionLocal() as session:
                loader = PromptLoader(session)
                self.system_prompt = await loader.get_prompt(
                    agent_type=self.agent_type,
                    prompt_type="system"
                )
                self._prompt_loaded = True
                logger.debug(f"[{self.__class__.__name__}] Prompt carregado do banco")
        except Exception as e:
            logger.warning(
                f"[{self.__class__.__name__}] Erro ao carregar prompt do banco: {e}. "
                f"Usando prompt inline se disponível."
            )
            # Se falhar, mantém o prompt inline (backwards compatibility durante migração)
            self._prompt_loaded = True
    
    @abstractmethod
    def build_user_prompt(self, contexto: Dict[str, Any]) -> str:
        """
        Constrói o prompt do usuário com base no contexto.
        
        Args:
            contexto: Dicionário com dados do projeto, itens PAC, etc.
            
        Returns:
            String com o prompt formatado.
        """
        pass
    
    async def gerar(
        self,
        contexto: Dict[str, Any],
        prompt_adicional: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Gera o artefato completo usando streaming.
        
        Args:
            contexto: Dados do projeto e itens PAC
            prompt_adicional: Instruções extras do usuário
            
        Yields:
            Chunks de texto conforme são gerados pela IA
        """
        # Carregar prompt do banco se necessário
        await self._load_prompt()
        
        user_prompt = self.build_user_prompt(contexto)
        
        if prompt_adicional:
            user_prompt += f"\n\nINSTRUÇÕES ADICIONAIS DO USUÁRIO:\n{prompt_adicional}"
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.info(f"[{self.__class__.__name__}] Iniciando geração com modelo {self.model}")
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
                    
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Erro na geração: {e}")
            raise
    
    async def regenerar_campo(
        self,
        campo: str,
        contexto: Dict[str, Any],
        valor_atual: Optional[str] = None,
        instrucoes: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Regenera um campo específico do artefato.
        
        Args:
            campo: Nome do campo a regenerar
            contexto: Dados do projeto e itens PAC
            valor_atual: Valor atual do campo (para referência)
            instrucoes: Instruções específicas para regeneração
            
        Yields:
            Chunks de texto conforme são gerados pela IA
        """
        # Prompt especializado para regeneração de campo
        regenerate_system = f"""Você é um Especialista em Contratações Públicas (Lei 14.133/2021).
Sua tarefa é regenerar APENAS o campo '{campo}' do documento.

DIRETRIZES:
1. Pense profundamente sobre a solicitação.
2. O texto deve ser técnico, formal e direto.
3. Retorne APENAS o conteúdo do texto regenerado, sem preâmbulos, sem JSON, sem explicações.
4. Mantenha o mesmo estilo e nível de detalhe esperado para este tipo de documento."""
        
        # Construir prompt do usuário
        user_parts = [f"CAMPO A REGENERAR: {campo}"]
        
        # Adicionar contexto do projeto
        if contexto.get("projeto_titulo"):
            user_parts.append(f"TÍTULO DO PROJETO: {contexto['projeto_titulo']}")
        if contexto.get("setor_usuario"):
            user_parts.append(f"SETOR: {contexto['setor_usuario']}")
        if contexto.get("itens_pac"):
            user_parts.append(f"ITENS PAC: {json.dumps(contexto['itens_pac'], ensure_ascii=False)}")
        
        # Valor atual (se existir)
        if valor_atual:
            user_parts.append(f"\nVALOR ATUAL DO CAMPO:\n{valor_atual}")
        
        # Instruções do usuário
        if instrucoes:
            user_parts.append(f"\nINSTRUÇÕES DO USUÁRIO:\n{instrucoes}")
        else:
            user_parts.append("\nGere uma nova versão melhorada deste campo.")
        
        user_prompt = "\n".join(user_parts)
        
        messages = [
            {"role": "system", "content": regenerate_system},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.info(f"[{self.__class__.__name__}] Regenerando campo '{campo}'")
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature + 0.1,  # Ligeiramente mais criativo
                max_tokens=2048,  # Campo único precisa menos tokens
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
                    
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Erro ao regenerar campo: {e}")
            raise
    
    async def gerar_json(
        self,
        contexto: Dict[str, Any],
        prompt_adicional: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Gera o artefato e retorna como dicionário JSON.
        Útil quando não precisa de streaming.
        
        Args:
            contexto: Dados do projeto e itens PAC
            prompt_adicional: Instruções extras do usuário
            
        Returns:
            Dicionário com os campos gerados
        """
        full_response = ""
        
        async for chunk in self.gerar(contexto, prompt_adicional):
            full_response += chunk
        
        # Tentar parsear como JSON
        try:
            # Limpar possíveis markdown
            cleaned = full_response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            logger.warning(f"Resposta não é JSON válido: {e}")
            # Retornar resposta bruta em campo genérico
            return {"conteudo_bruto": full_response}
