# 🤖 economiza.ai - Assistente Financeiro Inteligente

## O que é o economiza.ai?

O **economiza.ai** é um assistente financeiro pessoal que revoluciona a forma como você gerencia suas finanças. Imagine ter um consultor financeiro disponível 24 horas por dia, que entende linguagem natural e pode registrar seus gastos e receitas apenas conversando com ele.

Este sistema combina inteligência artificial avançada com visualizações financeiras intuitivas, permitindo que você:

- **Converse naturalmente** sobre suas finanças: "Gastei 50 reais no supermercado" 
- **Visualize sua saúde financeira** através de dashboards interativos
- **Receba insights inteligentes** sobre seus padrões de gastos

## Como Funciona a Mágica?

### 1. Inteligência Artificial Conversacional

O coração do sistema é um agente de IA que usa o modelo **Gemini 2.0** do Google. Este agente foi treinado especificamente para entender contexto financeiro e pode:

- Interpretar frases como "comprei um livro por 30 reais" e automaticamente classificar como gasto na categoria "Educação"
- Distinguir entre receitas e despesas baseado no contexto
- Executar consultas SQL automaticamente para buscar informações
- Oferecer análises e sugestões baseadas nos seus dados
  
### 2. Banco de Dados Adaptável

O sistema usa uma arquitetura inteligente de banco de dados:
- **Desenvolvimento local**: SQLite para simplicidade
- **Cache inteligente**: Otimização automática de consultas frequentes

## Arquitetura do Sistema

Vou explicar como cada componente trabalha em conjunto:

### Componentes Principais

**app.py** - O cérebro do sistema que orquestra toda a experiência do usuário. Aqui acontece a mágica da conversação com IA, processamento de áudio e renderização da interface.

**dashboard.py** - O centro de visualização que transforma seus dados em gráficos, métricas e insights visuais compreensíveis.

**auth.py** - O guardião do sistema, garantindo que apenas você tenha acesso aos seus dados financeiros sensíveis.

**database.py** - O arquiteto dos dados, gerenciando como as informações são armazenadas, recuperadas e mantidas íntegras.

**config.py** - O configurador inteligente que contém as instruções detalhadas para o agente de IA entender contexto financeiro.

**helpers.py** - A caixa de ferramentas com funções especializadas para processamento de áudio e outras utilidades.

## 🔧 Preparação do Ambiente Local

### Passo 1: Obter as Chaves de API

Antes de começar, você precisará obter credenciais para os serviços de IA:

**Chave do Google Gemini:**
1. Visite [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Faça login com sua conta Google
3. Clique em "Create API Key"
4. Copie e guarde a chave (ela começa com "AIza...")

### Passo 2: Configuração com UV (Recomendado)

O **UV** é um gerenciador de dependências Python moderno e extremamente rápido. Ele resolve o problema das "500 dependências" que apareceriam no requirements.txt tradicional:

```bash
# Instalar UV (se ainda não tiver)
curl -LsSf https://astral.sh/uv/install.sh | sh
# ou no Windows: 
# powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clonar o repositório
git clone https://github.com/seu-usuario/economiza-ai.git
cd economiza-ai

# Criar ambiente virtual e instalar dependências automaticamente
uv sync

# Ativar o ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate     # Windows
```

### Passo 3: Configuração Inicial Automatizada

O sistema inclui um script de setup inteligente que prepara tudo para você:

```bash
python setup.py
```

Este script automaticamente:
- Cria todas as pastas necessárias (`.streamlit`, `data`, `backups`)
- Gera o template de configuração `.streamlit/secrets.toml`
- Verifica se o `.gitignore` está protegendo seus secrets
- Configura exemplos de variáveis de ambiente

### Passo 4: Configurar Suas Credenciais

Edite o arquivo `.streamlit/secrets.toml` que foi criado:

```toml
[auth]
username = "admin"                    # Seu usuário para login
password = "MinhaS3nh@Segura123"     # Senha forte para proteger o sistema
demo_username = "demo"               # Usuario para demonstrações
demo_password = "demo"               # Senha para demos

[api_keys]
GEMINI_API_KEY = "AIza..."           # Sua chave do Google Gemini
GROQ_API_KEY = "gsk_..."             # Sua chave do Groq

[database]
SQLITE_PATH = "./data/gastos_receita.db"  # Caminho do banco local
```

### Passo 5: Testar Localmente

```bash
# Executar o aplicativo
streamlit run app.py

# O sistema abrirá automaticamente em http://localhost:8501
```

## 🚀 Deploy no Streamlit Community Cloud

### Passo 1: Preparar o Repositório

O Streamlit Community Cloud precisa de um repositório GitHub público ou privado:

```bash
# Adicionar tudo ao Git (o .gitignore já protege os secrets)
git add .
git commit -m "🚀 Initial commit - economiza.ai"

# Enviar para GitHub
git remote add origin https://github.com/seu-usuario/economiza-ai.git
git push -u origin main
```

### Passo 2: Deploy Automatizado

1. **Acesse [share.streamlit.io](https://share.streamlit.io)**
2. **Conecte sua conta GitHub** (autorize o acesso)
3. **Clique em "New app"**
4. **Configure o deploy:**
   - Repository: `seu-usuario/economiza-ai`
   - Branch: `main`
   - Main file path: `app.py`

5. **CRUCIAL - Advanced Settings:**
   - Clique em "Advanced settings"
   - Deixe seu repositório privado, é interessante que você mantenha suas informações sensíveis privadas.
   - Na seção "Secrets", cole **todo** o conteúdo do seu arquivo `secrets.toml`:

```toml
[auth]
username = "admin"
password = "MinhaS3nh@Segura123"
demo_username = "demo" 
demo_password = "demo"

[api_keys]
GEMINI_API_KEY = "AIza..."
GROQ_API_KEY = "gsk_..."

[database]
SQLITE_PATH = "./data/gastos_receita.db"
```

6. **Deploy:** Clique em "Deploy!" e aguarde alguns minutos

### Passo 3: Configurar Privacidade

Para manter seus dados financeiros seguros:

1. No dashboard do Streamlit Cloud, encontre seu app
2. Clique nos três pontos (⋮) ao lado do nome
3. Selecione "Settings"
4. Em "Sharing", marque "Private app"
5. Adicione emails de pessoas autorizadas se necessário

## 🔐 Segurança e Boas Práticas

### Proteção de Credenciais

O sistema implementa várias camadas de segurança:

**Autenticação Robusta:** Sistema de login com senhas hasheadas e sessões seguras.

**Secrets Management:** As credenciais nunca são expostas no código, ficando sempre em arquivos de configuração protegidos.

**Isolamento de Dados:** Cada usuário tem acesso apenas aos próprios dados financeiros.

### Senhas Recomendadas

Use senhas que combinem:
- Pelo menos 12 caracteres
- Letras maiúsculas e minúsculas  
- Números e símbolos especiais
- Evite informações pessoais óbvias

Exemplo de senha forte: `Fin@nc3ir0_S3gur0!2024`

## 💡 Como Usar o Sistema

### Interface de Chat Inteligente

O chat é onde a mágica acontece. Você pode falar naturalmente:

**Registrar Gastos:**
- "Gastei 45 reais no supermercado hoje"
- "Comprei um livro por 30 reais"
- "Paguei 120 na consulta médica"

**Registrar Receitas:**
- "Recebi meu salário de 3000 reais"
- "Ganhei 500 reais com freelance"
- "Vendi algo por 200 reais"

**Consultar Informações:**
- "Quanto gastei este mês?"
- "Qual minha categoria de maior gasto?"
- "Como está meu saldo atual?"


### Dashboard Inteligente

O dashboard oferece quatro visualizações principais:

**Métricas Principais:** Receitas médias, gastos médios e saldo atual com indicadores visuais de saúde financeira.

**Termômetro Financeiro:** Um gauge que mostra quantos meses seu saldo atual pode cobrir seus gastos médios.

**Distribuição de Gastos:** Gráfico de pizza mostrando como você distribui seus gastos entre categorias.

**Evolução Temporal:** Gráficos de linha e barras mostrando a evolução de receitas, gastos e saldo ao longo do tempo.

## 🛠️ Personalização e Extensões

### Adicionando Novas Categorias

Para adicionar categorias personalizadas, edite o arquivo `config.py`:

```python
'categorias': {
    'gastos': [
        'Alimentação', 'Transporte', 'Saúde', 'Casa',
        'Compras', 'Entretenimento', 'Educação',
        'Pets',  # Nova categoria
        'Investimentos'  # Outra nova categoria
    ],
    'receitas': ['Receita', 'Freelance', 'Investimentos']
}
```

### Configurando Banco PostgreSQL

Para usar PostgreSQL em produção, adicione ao `secrets.toml`:

```toml
[database]
DATABASE_URL = "postgresql://usuario:senha@host:porta/database"
```

Exemplos de providers populares:
- **Render:** `postgresql://user:pass@dpg-xxxxx.render.com/db`
- **Supabase:** `postgresql://postgres:pass@db.xxxxx.supabase.co:5432/postgres`
- **Neon:** `postgresql://user:pass@ep-xxxxx.neon.tech/db`

## 🐛 Solução de Problemas

### Problemas Comuns e Soluções

**Erro de API Key Inválida:**
- Verifique se as chaves foram copiadas corretamente
- Confirme se as chaves não expiraram
- Teste as chaves diretamente nos consoles das APIs

**Erro de Conexão com Banco:**
- Certifique-se de que a pasta `data` existe
- Verifique permissões de escrita no diretório
- Para PostgreSQL, teste a connection string manualmente

**App Não Carrega no Streamlit Cloud:**
- Verifique se todos os secrets foram configurados
- Confirme se o repositório está público ou você tem acesso
- Veja os logs do deploy no dashboard do Streamlit

### Logs e Debugging

Para debugar problemas localmente:

```bash
# Executar com logs detalhados
streamlit run app.py --logger.level=debug

# Ver logs do sistema
tail -f ~/.streamlit/logs/streamlit.log
```

## 🤝 Contribuindo para o Projeto

Se você quiser contribuir ou personalizar ainda mais o sistema, a arquitetura modular facilita extensões:

**Erro na função de aúdio**: Apesar de ter a função que suporta aúdio, ainda não consegui fazer ele funcionar certinho (desculpa)

**Novos Processadores de Entrada:** Adicione suporte para importação de extratos bancários, fotos de notas fiscais, etc.

**Visualizações Avançadas:** Crie novos tipos de gráficos e relatórios no `dashboard.py`.

**Integrações Externas:** Conecte com bancos, cartões de crédito ou outros sistemas financeiros.

**Melhorias de IA:** Ajuste o prompt do sistema em `config.py` para comportamentos mais específicos.

O economiza.ai representa uma nova era na gestão financeira pessoal, onde a tecnologia trabalha para simplificar sua vida ao invés de complicá-la. Ao combinar conversação natural, processamento inteligente e visualizações claras, ele transforma uma tarefa muitas vezes tediosa em uma experiência fluida e até mesmo prazerosa.

Com este guia completo, você tem todas as ferramentas necessárias para não apenas instalar e usar o sistema, mas também compreender profundamente como ele funciona e como pode ser adaptado às suas necessidades específicas.

**Pretendo melhorar esse projeto continuamente e implementar novas features futuramente.**

Desenvolvido com 💗 por Gabriel.
