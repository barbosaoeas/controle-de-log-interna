from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from .models import PerfilUsuario


class ForcePasswordChangeMiddleware:
    """
    Middleware que força usuários com senha padrão a alterarem a senha
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que não precisam de verificação de senha
        self.exempt_urls = [
            reverse('alterar_senha'),
            reverse('logout'),
            '/admin/',
        ]
    
    def __call__(self, request):
        # Verificar se o usuário está logado
        if request.user.is_authenticated:
            try:
                perfil = request.user.perfil
                
                # Verificar se precisa alterar senha
                if perfil.precisa_alterar_senha:
                    # Verificar se não está em uma URL isenta
                    current_path = request.path
                    is_exempt = any(current_path.startswith(url) for url in self.exempt_urls)
                    
                    if not is_exempt:
                        messages.warning(
                            request, 
                            'Por segurança, você deve alterar sua senha antes de continuar.'
                        )
                        return redirect('alterar_senha')
                        
            except PerfilUsuario.DoesNotExist:
                # Usuário sem perfil, deixar passar
                pass
        
        response = self.get_response(request)
        return response
