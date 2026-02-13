"""
Backend de autenticação customizado para aceitar login case-insensitive
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q


class CaseInsensitiveModelBackend(ModelBackend):
    """
    Backend de autenticação que permite login case-insensitive (não diferencia maiúsculas/minúsculas).
    
    Isso permite que o usuário faça login com:
    - joao.lokar
    - Joao.lokar
    - JOAO.LOKAR
    
    Todos serão aceitos se o username no banco for 'joao.lokar'
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica o usuário ignorando maiúsculas/minúsculas no username
        """
        if username is None or password is None:
            return None
        
        try:
            # Buscar usuário ignorando case (case-insensitive)
            user = User.objects.get(username__iexact=username)
            
            # Verificar senha
            if user.check_password(password):
                return user
            
        except User.DoesNotExist:
            # Executar hasher de senha padrão para evitar timing attacks
            User().set_password(password)
            return None
        
        except User.MultipleObjectsReturned:
            # Se houver múltiplos usuários com o mesmo username (case-insensitive),
            # tentar encontrar o exato
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                pass
            
            return None
        
        return None

