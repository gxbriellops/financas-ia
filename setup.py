#!/usr/bin/env python3
"""
Script de inicialização do economiza.ai
Prepara o ambiente para primeiro uso
"""

import os
import sys
import shutil
from pathlib import Path

def criar_estrutura_pastas():
    """Cria estrutura de pastas necessária"""
    pastas = [
        '.streamlit',
        'data',
        'backups'
    ]
    
    for pasta in pastas:
        Path(pasta).mkdir(exist_ok=True)
        print(f"✅ Pasta '{pasta}' criada/verificada")

def criar_secrets_template():
    """Cria template do secrets.toml se não existir"""
    secrets_path = Path('.streamlit/secrets.toml')
    
    if not secrets_path.exists():
        template = '''# CONFIGURE SUAS CREDENCIAIS AQUI
# NUNCA COMMITE ESTE ARQUIVO!

[auth]
username = "admin"
password = "MUDE_ESTA_SENHA"
demo_username = "demo"
demo_password = "demo"

[api_keys]
GEMINI_API_KEY = "COLE_SUA_CHAVE_GEMINI_AQUI"
GROQ_API_KEY = "COLE_SUA_CHAVE_GROQ_AQUI"

[database]
SQLITE_PATH = "./data/gastos_receita.db"
'''
        
        with open(secrets_path, 'w', encoding='utf-8') as f:
            f.write(template)
        
        print("⚠️  IMPORTANTE: Edite .streamlit/secrets.toml com suas credenciais!")
        print("📝 Arquivo template criado em: .streamlit/secrets.toml")
    else:
        print("✅ Arquivo secrets.toml já existe")

def verificar_gitignore():
    """Verifica se secrets.toml está no .gitignore"""
    gitignore_path = Path('.gitignore')
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'secrets.toml' not in content:
            print("⚠️  AVISO: secrets.toml não está no .gitignore!")
            print("   Adicione manualmente para evitar vazar credenciais")
    else:
        print("⚠️  AVISO: Arquivo .gitignore não encontrado!")

def criar_env_example():
    """Cria arquivo .env.example"""
    env_example = '''# Exemplo de variáveis de ambiente para desenvolvimento local
# Copie para .env e preencha com suas chaves

GEMINI_API_KEY=sua_chave_aqui
GROQ_API_KEY=sua_chave_aqui
'''
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example)
    
    print("✅ Arquivo .env.example criado")

def verificar_dependencias():
    """Verifica se requirements.txt existe"""
    if Path('requirements.txt').exists():
        print("✅ requirements.txt encontrado")
        print("   Execute: pip install -r requirements.txt")
    else:
        print("❌ requirements.txt não encontrado!")

def main():
    """Função principal"""
    print("🚀 Configurando economiza.ai...")
    print("-" * 50)
    
    # Executar setup
    criar_estrutura_pastas()
    criar_secrets_template()
    verificar_gitignore()
    criar_env_example()
    verificar_dependencias()
    
    print("-" * 50)
    print("✅ Setup concluído!")
    print("\n📋 Próximos passos:")
    print("1. Edite .streamlit/secrets.toml com suas credenciais")
    print("2. Instale dependências: pip install -r requirements.txt")
    print("3. Execute: streamlit run app.py")
    print("\n🔒 Lembre-se: NUNCA commite o arquivo secrets.toml!")

if __name__ == "__main__":
    main()