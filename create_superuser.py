import os
import django

# Configura o ambiente do Django para que o script possa usar os modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'siram_pato.settings')
django.setup()

# Importa o modelo de usuário customizado APÓS a configuração
from laudos.models import UsuarioCustomizado

# --- DADOS DO SUPERUSUÁRIO ---
USERNAME = 'user'
PASSWORD = '1234'
EMAIL = 'adm@user.com'
# -----------------------------

# Verifica se o usuário já existe antes de tentar criar
if UsuarioCustomizado.objects.filter(username=USERNAME).exists():
    print(f"O superusuário '{USERNAME}' já existe no banco de dados.")
else:
    # Cria o superusuário com o role de Administrador
    UsuarioCustomizado.objects.create_superuser(
        username=USERNAME,
        email=EMAIL,
        password=PASSWORD,
        role='ADMIN'  # Define o papel como Administrador
    )
    print(f"Superusuário '{USERNAME}' criado com sucesso!")