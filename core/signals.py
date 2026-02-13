from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import PerfilUsuario, Setor, Empresa, TipoPerfil
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Criar perfil de usuário automaticamente quando um usuário for criado"""
    if created and not hasattr(instance, 'perfil'):
        # Tentar encontrar um setor padrão ou criar um
        try:
            setor_default = Setor.objects.first()
            if not setor_default:
                setor_default = Setor.objects.create(
                    nome='Setor Padrão',
                    descricao='Setor criado automaticamente'
                )

            # Determinar perfil baseado no username ou se é staff
            perfil_codigo = 'TRANSPORTES' if 'transport' in instance.username.lower() or instance.is_staff else 'DEMANDANTE'

            # Buscar TipoPerfil correspondente
            tipo_perfil = TipoPerfil.objects.get(codigo=perfil_codigo)

            PerfilUsuario.objects.create(
                user=instance,
                setor=setor_default,
                tipo_perfil=tipo_perfil
            )
        except Exception as e:
            print(f"Erro ao criar perfil para usuário {instance.username}: {e}")


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Salvar perfil de usuário quando o usuário for salvo"""
    if hasattr(instance, 'perfil'):
        instance.perfil.save()


# ===== SIGNALS REMOVIDOS - USANDO APENAS EMPRESA =====
# A sincronização Empresa ↔ Fornecedor foi removida para simplificar o sistema
# Agora usamos apenas o modelo Empresa (core) como fonte única
