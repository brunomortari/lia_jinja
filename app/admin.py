from sqladmin import Admin, ModelView
from app.models.user import User
from app.models.projeto import Projeto
from app.models.artefatos import DFD, ETP, TR, Riscos, Edital, PesquisaPrecos
from app.models.pac import PAC

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email, User.nome, User.grupo, User.perfil, User.is_superuser, User.is_active]
    icon = "fa-solid fa-user"

class ProjetoAdmin(ModelView, model=Projeto):
    column_list = [Projeto.id, Projeto.titulo, Projeto.status, Projeto.data_criacao]
    icon = "fa-solid fa-folder"

class DFDAdmin(ModelView, model=DFD):
    column_list = [DFD.id, DFD.projeto_id, DFD.status, DFD.versao]
    icon = "fa-solid fa-file-lines"

class ETPAdmin(ModelView, model=ETP):
    column_list = [ETP.id, ETP.projeto_id, ETP.status, ETP.versao]
    icon = "fa-solid fa-file-contract"

class TRAdmin(ModelView, model=TR):
    column_list = [TR.id, TR.projeto_id, TR.status, TR.versao]
    icon = "fa-solid fa-file-signature"

class RiscosAdmin(ModelView, model=Riscos):
    column_list = [Riscos.id, Riscos.projeto_id, Riscos.status, Riscos.versao]
    icon = "fa-solid fa-triangle-exclamation"

class EditalAdmin(ModelView, model=Edital):
    column_list = [Edital.id, Edital.projeto_id, Edital.status, Edital.versao]
    icon = "fa-solid fa-scroll"

class PACAdmin(ModelView, model=PAC):
    column_list = [PAC.id, PAC.descricao, PAC.valor_previsto]
    icon = "fa-solid fa-box"

def setup_admin(app, engine):
    admin = Admin(app, engine, title="LIA Admin")
    
    admin.add_view(UserAdmin)
    admin.add_view(ProjetoAdmin)
    admin.add_view(DFDAdmin)
    admin.add_view(ETPAdmin)
    admin.add_view(TRAdmin)
    admin.add_view(RiscosAdmin)
    admin.add_view(EditalAdmin)
    admin.add_view(PACAdmin)
