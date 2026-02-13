"""
Sistema LIA - Agente Conversacional Base
========================================
Classe base para agentes que conversam com o usuário
antes de gerar artefatos.

O agente mantém histórico de mensagens e detecta quando
tem informações suficientes para gerar o artefato.

Autor: Equipe TRE-GO
Data: Fevereiro 2026
"""

import json
import logging
from typing import AsyncGenerator, Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from openai import AsyncOpenAI
import asyncio

from app.config import settings
from app.database import AsyncSessionLocal
from .prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class ChatState(str, Enum):
    """Estados possíveis do chat."""
    CONVERSING = "conversing"      # Coletando informações
    READY = "ready"                # Pronto para gerar
    GENERATING = "generating"      # Gerando artefato
    COMPLETED = "completed"        # Artefato gerado


@dataclass
class Message:
    """Representa uma mensagem no chat."""
    role: str  # "user" ou "assistant"
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    attachments: Optional[List[Dict[str, Any]]] = None # List of {type: 'image'|'file', url: '...', content: '...'}


@dataclass 
class ChatContext:
    """Contexto coletado durante a conversa."""
    projeto_id: int
    projeto_titulo: str
    setor_usuario: str = "Unidade Requisitante"
    itens_pac: List[Dict] = field(default_factory=list)
    dfd: Optional[Dict] = None
    pesquisa_precos: Optional[Dict] = None
    etp: Optional[Dict] = None
    pgr: Optional[Dict] = None
    tr: Optional[Dict] = None
    # Dados coletados na conversa
    dados_coletados: Dict[str, Any] = field(default_factory=dict)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    # Skills (habilidades) ativas para este projeto
    skills: List[Dict[str, Any]] = field(default_factory=list)


class ConversationalAgent:
    """
    Agente base para interação conversacional.
    
    O agente conversa com o usuário para coletar informações,
    e quando detecta que tem dados suficientes, sinaliza que
    está pronto para gerar o artefato.
    """
    
    # Configurações (sobrescrever em subclasses)
    temperature_chat: float = 0.7  # Mais criativo para conversa
    temperature_generate: float = 0.5  # Mais preciso para geração
    max_tokens_chat: int = 1024
    max_tokens_generate: int = 8192
    model: str = None
    
    # Tipo do agente para buscar prompts no banco (definido em cada subclasse)
    agent_type: str = ""
    
    # Prompts (carregados do banco na primeira geração)
    system_prompt_chat: str = ""
    system_prompt_generate: str = ""
    _prompts_loaded: bool = False
    
    # Checklist de dados necessários (sobrescrever em subclasses)
    dados_necessarios: List[str] = []
    
    # Nome do artefato para mensagens
    nome_artefato: str = "artefato"
    
    def __init__(self, model_override: Optional[str] = None):
        """Inicializa o cliente OpenAI apontando para OpenRouter. Permite override do modelo."""
        self.client = AsyncOpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            timeout=settings.OPENROUTER_TIMEOUT,
        )
        self.model = model_override or self.model or settings.OPENROUTER_DEFAULT_MODEL
    
    async def _load_prompts(self):
        """Carrega os prompts do banco se ainda não foram carregados."""
        if self._prompts_loaded or not self.agent_type:
            return
        
        try:
            async with AsyncSessionLocal() as session:
                loader = PromptLoader(session)
                prompts = await loader.get_prompts_multiple(
                    agent_type=self.agent_type,
                    prompt_types=["system_chat", "system_generate"]
                )
                
                if "system_chat" in prompts:
                    self.system_prompt_chat = prompts["system_chat"]
                if "system_generate" in prompts:
                    self.system_prompt_generate = prompts["system_generate"]
                
                self._prompts_loaded = True
                logger.debug(f"[{self.__class__.__name__}] Prompts carregados do banco")
        except Exception as e:
            logger.warning(
                f"[{self.__class__.__name__}] Erro ao carregar prompts do banco: {e}. "
                f"Usando prompts inline se disponíveis."
            )
            # Se falhar, mantém os prompts inline (backwards compatibility durante migração)
            self._prompts_loaded = True
    
    def build_chat_system_prompt(self, context: ChatContext) -> str:
        """
        Constrói o system prompt para o modo chat.
        Inclui contexto do projeto e checklist.
        """
        checklist = "\n".join([f"- {item}" for item in self.dados_necessarios])
        
        base_prompt = f"""{self.system_prompt_chat}

CONTEXTO DO PROJETO:
- ID: {context.projeto_id}
- Título: {context.projeto_titulo}
- Setor: {context.setor_usuario}
- Itens PAC: {len(context.itens_pac)} itens
"""
        
        if context.dfd:
            dfd_desc = context.dfd.get('descricao_objeto_padronizada') or context.dfd.get('descricao_objeto') or 'N/A'
            base_prompt += f"\n- DFD aprovado: Sim (objeto: {dfd_desc[:100]}...)"
        
        if context.pesquisa_precos:
            valor = context.pesquisa_precos.get('valor_total_cotacao', context.pesquisa_precos.get('valor_total', 0))
            base_prompt += f"\n- Pesquisa de Preços: R$ {valor:,.2f}"

        # Dados já coletados (formulário preenchido pelo usuário)
        if context.dados_coletados:
            base_prompt += "\n\nDADOS JÁ INFORMADOS PELO USUÁRIO (NÃO PERGUNTE NOVAMENTE):"
            if context.dados_coletados.get('responsavel_gestor'):
                base_prompt += f"\n- Gestor: {context.dados_coletados.get('responsavel_gestor')}"
            if context.dados_coletados.get('responsavel_fiscal'):
                base_prompt += f"\n- Fiscal: {context.dados_coletados.get('responsavel_fiscal')}"
            if context.dados_coletados.get('data_pretendida'):
                base_prompt += f"\n- Data limite: {context.dados_coletados.get('data_pretendida')}"
            logger.info(f"[Agent] Dados coletados incluídos no prompt: {list(context.dados_coletados.keys())}")
        else:
            logger.info("[Agent] Nenhum dado coletado no contexto")

        # Anexos/base de conhecimento
        if context.attachments:
            base_prompt += "\n\nBASE DE CONHECIMENTO (arquivos anexados pelo usuário):"
            base_prompt += "\nIMPORTANTE: Analise CRITICAMENTE se cada documento é relevante para o artefato sendo elaborado."
            base_prompt += "\nSe um documento NÃO tem relação com o artefato, informe honestamente ao usuário que o documento não é relevante para este contexto."
            base_prompt += "\nNUNCA invente conexões forçadas entre documentos e o artefato."
            for att in context.attachments:
                if att.get("extracted_text"):
                    base_prompt += f"\n\n--- {att.get('filename', 'arquivo')} ---\n{att['extracted_text'][:2000]}"
            logger.info(f"[Agent] {len(context.attachments)} anexo(s) incluído(s) no prompt")

        # Skills (habilidades) ativas
        if context.skills:
            base_prompt += "\n\n========== HABILIDADES ATIVAS =========="
            base_prompt += "\nVoce DEVE aplicar estas instrucoes durante toda a interacao:\n"
            for skill in context.skills:
                base_prompt += f"\n--- {skill.get('nome', 'Skill')} ({skill.get('icone', '⚡')}) ---\n"
                if skill.get('descricao'):
                    base_prompt += f"Descricao: {skill['descricao']}\n"
                
                # Injetar textos base da skill (RAG via contexto)
                if skill.get('textos_base'):
                    base_prompt += "\n  [DOCUMENTOS DE REFERENCIA DA SKILL]:"
                    for doc in skill['textos_base']:
                        titulo = doc.get('titulo', 'Documento')
                        conteudo = doc.get('conteudo', '')[:5000] # Limite de seguranca por doc
                        base_prompt += f"\n  - {titulo}:\n'''{conteudo}'''\n"

                base_prompt += f"{skill.get('instrucoes', '')}\n"
            base_prompt += "\n========== FIM DAS HABILIDADES ==========\n"
            logger.info(f"[Agent] {len(context.skills)} skill(s) injetada(s) no prompt")

        base_prompt += f"""

DADOS IMPORTANTES A COLETAR:
{checklist}

INSTRUÇÕES:
1. Converse naturalmente para coletar as informações
2. Use os dados do projeto que já temos (PAC, etc.)
3. NÃO pergunte sobre item do PAC - já está vinculado automaticamente
4. Quando tiver informações suficientes, faça um resumo e pergunte: "Posso gerar o {self.nome_artefato} agora?"
5. OBRIGATÓRIO: Se o usuário confirmar, você DEVE PRIMEIRO responder com uma frase natural confirmando a ação (ex: "Entendido, vou gerar agora o documento.") e SÓ DEPOIS adicionar a tag [GERAR_{self.nome_artefato.upper()}] ao final da mensagem.
6. NUNCA envie a tag [GERAR_{self.nome_artefato.upper()}] sozinha ou no início da mensagem.
7. NUNCA mencione JSON, schemas ou formatos técnicos para o usuário
8. Seja conciso e objetivo nas perguntas"""
        
        return base_prompt
    
    async def chat(
        self,
        message: str,
        history: List[Message],
        context: ChatContext,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        Processa uma mensagem do usuário e retorna resposta em streaming.
        
        Args:
            message: Mensagem do usuário
            history: Histórico de mensagens anteriores
            context: Contexto do projeto
            attachments: Lista de anexos {type, url, content, ...}
            
        Yields:
            Chunks de texto da resposta
        """
        # Carregar prompts do banco se necessário
        await self._load_prompts()
        
        # Montar mensagens para a API
        messages = [
            {"role": "system", "content": self.build_chat_system_prompt(context)}
        ]
        
        # Adicionar histórico (últimas 10 mensagens para economizar tokens)
        for msg in history[-10:]:
            # TODO: Se o histórico tiver imagens, precisaríamos tratar aqui também.
            # Por enquanto, assumimos que histórico é apenas texto ou simplificado.
            messages.append({"role": msg.role, "content": msg.content})
        
        # Construir mensagem do usuário (multimodal se houver anexos)
        if attachments:
            content_parts = [{"type": "text", "text": message}]
            
            for att in attachments:
                if att.get("type", "").startswith("image/"):
                    # Suporte a imagens (URL ou base64 se suportado)
                    # OpenRouter geralmente aceita URL pública ou data URI
                    # Aqui assumimos que 'url' é acessível ou é um data URI
                    url = att.get("url")
                    if url:
                         content_parts.append({
                            "type": "image_url",
                            "image_url": {"url": url}
                        })
                elif att.get("extracted_text"):
                    # Se for PDF/texto com conteúdo extraído, adicionar como texto
                    text_content = f"\n\n[CONTEÚDO DO ARQUIVO ANEXADO ({att.get('filename')}):]\n{att.get('extracted_text')}\n"
                    content_parts[0]["text"] += text_content

            messages.append({"role": "user", "content": content_parts})
        else:
            messages.append({"role": "user", "content": message})
        
        logger.info(f"[{self.__class__.__name__}] Chat com {len(messages)} mensagens")
        logger.info(f"[{self.__class__.__name__}] ===== PAYLOAD ENVIADO À IA (chat) =====")
        for i, msg in enumerate(messages):
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, list):
                # Multimodal: resumir partes
                parts_summary = []
                for part in content:
                    if part.get("type") == "text":
                        parts_summary.append(f"text({len(part['text'])} chars)")
                    elif part.get("type") == "image_url":
                        parts_summary.append("image_url")
                logger.info(f"  [{i}] {role}: [multimodal: {', '.join(parts_summary)}]")
                # Logar o texto completo separado
                for part in content:
                    if part.get("type") == "text":
                        logger.info(f"  [{i}] {role} (text): {part['text']}")
            else:
                logger.info(f"  [{i}] {role}: {content}")
        logger.info(f"[{self.__class__.__name__}] ===== FIM PAYLOAD (chat) =====")

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature_chat,
                max_tokens=self.max_tokens_chat,
                stream=True,
            )
            
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta:
                    # Verificar se há campo de raciocínio (OpenRouter/DeepSeek)
                    # Pode vir em 'reasoning', 'reasoning_content' ou model_extra
                    reasoning_content = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
                    
                    # Fallback para model_extra se disponível
                    if not reasoning_content and hasattr(delta, "model_extra") and delta.model_extra:
                        reasoning_content = delta.model_extra.get("reasoning") or delta.model_extra.get("reasoning_content")

                    if reasoning_content:
                        # Yield reasoning as a structured event
                        yield {"type": "reasoning", "content": reasoning_content}

                    # Content normal
                    if delta.content:
                        yield {"type": "content", "content": delta.content}
                    
                    # Forcar flush do evento no loop interno
                    await asyncio.sleep(0)
                    
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Erro no chat: {e}")
            raise
    
    async def gerar(
        self,
        context: ChatContext,
        history: List[Message],
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        Gera o artefato completo usando o contexto coletado na conversa.
        
        Args:
            context: Contexto do projeto com dados coletados
            history: Histórico da conversa (para referência)
            
        Yields:
            Chunks de texto do artefato sendo gerado (dicts)
        """
        logger.info(f"[{self.__class__.__name__}] === INICIANDO MÉTODO GERAR ===")
        
        # Carregar prompts do banco se necessário
        await self._load_prompts()
        
        # Extrair informações relevantes do histórico
        conversa_resumo = self._resumir_conversa(history)
        logger.info(f"[{self.__class__.__name__}] Conversa resumida: {conversa_resumo[:300]}...")
        
        # Construir prompt de geração
        user_prompt = self.build_generate_prompt(context, conversa_resumo)
        logger.info(f"[{self.__class__.__name__}] Prompt de geração (primeiros 500 chars): {user_prompt[:500]}...")
        
        messages = [
            {"role": "system", "content": self.system_prompt_generate},
            {"role": "user", "content": user_prompt},
        ]
        
        logger.info(f"[{self.__class__.__name__}] Iniciando geração de {self.nome_artefato}")
        logger.info(f"[{self.__class__.__name__}] Model: {self.model}")
        logger.info(f"[{self.__class__.__name__}] Temperature: {self.temperature_generate}")
        logger.info(f"[{self.__class__.__name__}] Max tokens: {self.max_tokens_generate}")
        logger.info(f"[{self.__class__.__name__}] ===== PAYLOAD ENVIADO À IA (gerar) =====")
        for i, msg in enumerate(messages):
            logger.info(f"  [{i}] {msg['role']}: {msg['content']}")
        logger.info(f"[{self.__class__.__name__}] ===== FIM PAYLOAD (gerar) =====")

        try:
            logger.info(f"[{self.__class__.__name__}] Chamando API OpenRouter...")
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature_generate,
                max_tokens=self.max_tokens_generate,
                stream=True,
            )
            logger.info(f"[{self.__class__.__name__}] Stream criado com sucesso")
            
            chunk_count = 0
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta:
                    # Tratamento de raciocínio (thinking)
                    reasoning_content = getattr(delta, "reasoning", None) or getattr(delta, "reasoning_content", None)
                    if not reasoning_content and hasattr(delta, "model_extra") and delta.model_extra:
                        reasoning_content = delta.model_extra.get("reasoning") or delta.model_extra.get("reasoning_content")

                    if reasoning_content:
                        yield {"type": "reasoning", "content": reasoning_content}

                    # Conteúdo principal
                    if delta.content:
                        chunk_count += 1
                        if chunk_count <= 3:
                            logger.debug(f"[{self.__class__.__name__}] Chunk #{chunk_count}: {delta.content[:50]}...")
                        yield {"type": "content", "content": delta.content}
            
            logger.info(f"[{self.__class__.__name__}] Geração completa. Total chunks: {chunk_count}")
                    
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] === ERRO NA GERAÇÃO ===: {e}", exc_info=True)
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
        await self._load_prompts()

        regenerate_system = f"""Você é um Especialista em Contratações Públicas (Lei 14.133/2021).
Sua tarefa é regenerar APENAS o campo '{campo}' do documento.

DIRETRIZES:
1. Pense profundamente sobre a solicitação.
2. O texto deve ser técnico, formal e direto.
3. Retorne APENAS o conteúdo do texto regenerado, sem preâmbulos, sem JSON, sem explicações.
4. Mantenha o mesmo estilo e nível de detalhe esperado para este tipo de documento."""

        user_parts = [f"CAMPO A REGENERAR: {campo}"]

        if contexto.get("projeto_titulo"):
            user_parts.append(f"TÍTULO DO PROJETO: {contexto['projeto_titulo']}")
        if contexto.get("setor_usuario"):
            user_parts.append(f"SETOR: {contexto['setor_usuario']}")
        if contexto.get("itens_pac"):
            user_parts.append(f"ITENS PAC: {json.dumps(contexto['itens_pac'], ensure_ascii=False)}")

        if valor_atual:
            user_parts.append(f"\nVALOR ATUAL DO CAMPO:\n{valor_atual}")

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
                temperature=self.temperature_chat + 0.1,
                max_tokens=2048,
                stream=True,
            )

            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Erro ao regenerar campo: {e}")
            raise

    def build_generate_prompt(self, context: ChatContext, conversa_resumo: str) -> str:
        """
        Constrói o prompt para geração do artefato.
        Sobrescrever em subclasses para customizar.
        """
        prompt = f"""DADOS DO PROJETO:
- Título: {context.projeto_titulo}
- Setor: {context.setor_usuario}
- Itens PAC: {json.dumps(context.itens_pac, ensure_ascii=False)}

INFORMAÇÕES COLETADAS NA CONVERSA:
{conversa_resumo}"""

        # Incluir base de conhecimento se disponível
        base_conhecimento = context.dados_coletados.get('base_conhecimento')
        if base_conhecimento:
            prompt += f"""

BASE DE CONHECIMENTO (documentos anexados pelo usuário - USE estas informações):
{base_conhecimento}"""

        # Incluir skills ativas
        if context.skills:
            prompt += "\n\nHABILIDADES ATIVAS (aplique estas instrucoes na geracao):"
            for skill in context.skills:
                prompt += f"\n- {skill.get('nome', 'Skill')}: {skill.get('instrucoes', '')}"
                if skill.get('textos_base'):
                    prompt += "\n  [REFERENCIA]: " + ", ".join([d.get('titulo', 'Doc') for d in skill['textos_base']])

        prompt += f"""

Gere o {self.nome_artefato} completo em formato JSON."""
        return prompt
    
    def _resumir_conversa(self, history: List[Message]) -> str:
        """Resume o histórico da conversa para o prompt de geração."""
        if not history:
            return "Nenhuma informação adicional coletada."
        
        partes = []
        for msg in history:
            prefixo = "Usuário:" if msg.role == "user" else "IA:"
            partes.append(f"{prefixo} {msg.content[:200]}")
        
        return "\n".join(partes[-10:])  # Últimas 10 mensagens
    
    def get_mensagem_inicial(self, context: ChatContext) -> str:
        """
        Retorna a mensagem inicial do chat.
        Sobrescrever em subclasses para customizar.
        """
        return f"""Olá! Sou a LIA, sua assistente para elaboração de documentos de contratação.

Vi que você está trabalhando no projeto **{context.projeto_titulo}**.

Encontrei {len(context.itens_pac)} item(ns) no PAC vinculados a este projeto.

Me conta: qual a necessidade que motivou essa contratação?"""
