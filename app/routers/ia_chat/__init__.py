"""
Sistema LIA - IA Chat Routers Package
=====================================
Modular chat handlers for all artefact types via factory pattern.

Each artefact has a config file (dfd.py, etp.py, etc.) that defines:
- Agent classes (chat + generation)
- Marker for generation readiness detection
- Context dependencies (which artefacts to load)
- Optional extra fields

The factory (criar_chat_router) generates 4 endpoints per config:
- GET /{tipo}/chat/init/{projeto_id}
- POST /{tipo}/chat/{projeto_id}
- POST /{tipo}/chat/{projeto_id}/gerar
- POST /{tipo}/chat/{projeto_id}/regenerar-campo
"""

from fastapi import APIRouter
from ._factory import criar_chat_router
from . import dfd, etp, pgr, tr, edital, je, pesquisa_precos, chk
# Fluxos alternativos
from . import rdve, jva, trs, ade, jpef

# Create individual routers via factory - Fluxo Principal
dfd_router = criar_chat_router(dfd.config)
etp_router = criar_chat_router(etp.config)
pgr_router = criar_chat_router(pgr.config)
tr_router = criar_chat_router(tr.config)
edital_router = criar_chat_router(edital.config)
je_router = criar_chat_router(je.config)
pesquisa_precos_router = criar_chat_router(pesquisa_precos.config)
chk_router = criar_chat_router(chk.config)

# Fluxo Adesão a Ata
rdve_router = criar_chat_router(rdve.config)
jva_router = criar_chat_router(jva.config)

# Fluxo Dispensa por Valor Baixo
trs_router = criar_chat_router(trs.config)
ade_router = criar_chat_router(ade.config)
jpef_router = criar_chat_router(jpef.config)

# Combine all into a single router (will be included in ia_native)
combined_router = APIRouter()
combined_router.include_router(dfd_router, prefix="/dfd", tags=["🧠 DFD Chat"])
combined_router.include_router(etp_router, prefix="/etp", tags=["🧠 ETP Chat"])
combined_router.include_router(pgr_router, prefix="/pgr", tags=["🧠 PGR Chat"])
combined_router.include_router(tr_router, prefix="/tr", tags=["🧠 TR Chat"])
combined_router.include_router(edital_router, prefix="/edital", tags=["🧠 Edital Chat"])
combined_router.include_router(je_router, prefix="/justificativa_excepcionalidade", tags=["🧠 JE Chat"])
combined_router.include_router(pesquisa_precos_router, prefix="/pesquisa_precos", tags=["🧠 PP Chat"])
combined_router.include_router(chk_router, prefix="/checklist_conformidade", tags=["🧠 CHK Chat"])

# Fluxos alternativos
combined_router.include_router(rdve_router, prefix="/rdve", tags=["🤝 RDVE Chat"])
combined_router.include_router(jva_router, prefix="/jva", tags=["🤝 JVA Chat"])
combined_router.include_router(trs_router, prefix="/trs", tags=["⚡ TRS Chat"])
combined_router.include_router(ade_router, prefix="/ade", tags=["⚡ ADE Chat"])
combined_router.include_router(jpef_router, prefix="/jpef", tags=["⚡ JPEF Chat"])
combined_router.include_router(etp_router, prefix="/etp", tags=["🧠 ETP Chat"])
combined_router.include_router(pgr_router, prefix="/pgr", tags=["🧠 PGR Chat"])
combined_router.include_router(tr_router, prefix="/tr", tags=["🧠 TR Chat"])
combined_router.include_router(edital_router, prefix="/edital", tags=["🧠 Edital Chat"])
combined_router.include_router(je_router, prefix="/justificativa_excepcionalidade", tags=["🧠 JE Chat"])
combined_router.include_router(pesquisa_precos_router, prefix="/pesquisa_precos", tags=["🧠 PP Chat"])

__all__ = ["combined_router", "dfd_router", "etp_router", "pgr_router", "tr_router", "edital_router", "je_router"]
