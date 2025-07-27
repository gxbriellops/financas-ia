import os
import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd

@st.cache_resource
def get_database_engine():
    """
    Retorna engine do banco com cache.
    Cache persiste entre reruns e é compartilhado entre usuários.
    """
    # Produção: PostgreSQL (se configurado)
    if "DATABASE_URL" in st.secrets.get("database", {}):
        db_url = st.secrets["database"]["DATABASE_URL"]
        engine = create_engine(db_url, pool_pre_ping=True)
    
    # Desenvolvimento/Padrão: SQLite
    else:
        db_path = st.secrets.get("database", {}).get("SQLITE_PATH", "./data/gastos_receita.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        engine = create_engine(f"sqlite:///{db_path}")
    
    # Inicializar tabela se não existir
    init_database(engine)
    return engine

def init_database(engine):
    """Inicializa tabelas se não existirem"""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS receita_gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Data DATE NOT NULL,
        Descrição TEXT NOT NULL,
        Valor REAL NOT NULL,
        Categorias TEXT NOT NULL,
        Tipo TEXT NOT NULL CHECK (Tipo IN ('Ativo', 'Passivo'))
    );
    """
    
    try:
        with engine.connect() as conn:
            # SQLite
            if engine.dialect.name == 'sqlite':
                conn.execute(text(create_table_sql))
            # PostgreSQL
            else:
                create_table_sql_pg = create_table_sql.replace(
                    "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "SERIAL PRIMARY KEY"
                )
                conn.execute(text(create_table_sql_pg))
            conn.commit()
    except Exception as e:
        st.error(f"Erro ao inicializar banco: {e}")

@st.cache_data(ttl=300)  # Cache por 5 minutos
def carregar_dados(_engine):
    """
    Carrega dados do banco com cache.
    O underscore em _engine evita que o engine seja hasheado.
    """
    try:
        query = """
        SELECT Data, Descrição, Valor, Categorias, Tipo, 
               strftime('%Y-%m', Data) as MesAno,
               strftime('%Y', Data) as Ano,
               strftime('%m', Data) as Mes
        FROM receita_gastos 
        ORDER BY Data DESC
        """
        
        # Ajustar query para PostgreSQL
        if _engine.dialect.name == 'postgresql':
            query = """
            SELECT Data, Descrição, Valor, Categorias, Tipo,
                   TO_CHAR(Data, 'YYYY-MM') as MesAno,
                   EXTRACT(YEAR FROM Data)::TEXT as Ano,
                   EXTRACT(MONTH FROM Data)::TEXT as Mes
            FROM receita_gastos 
            ORDER BY Data DESC
            """
        
        df = pd.read_sql(query, _engine)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)  # Cache por 5 minutos
def get_summary_stats(_engine):
    """Retorna estatísticas resumidas com cache"""
    try:
        query = """
        SELECT 
            Tipo,
            COUNT(*) as total_transacoes,
            SUM(Valor) as valor_total,
            AVG(Valor) as valor_medio,
            MAX(Valor) as valor_maximo,
            MIN(Valor) as valor_minimo
        FROM receita_gastos
        GROUP BY Tipo
        """
        
        return pd.read_sql(query, _engine)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_category_summary(_engine):
    """Retorna resumo por categoria com cache"""
    try:
        query = """
        SELECT 
            Categorias,
            Tipo,
            COUNT(*) as qtd,
            SUM(Valor) as total
        FROM receita_gastos
        GROUP BY Categorias, Tipo
        ORDER BY total DESC
        """
        
        return pd.read_sql(query, _engine)
    except:
        return pd.DataFrame()

def invalidate_cache():
    """Invalida todos os caches quando há mudanças nos dados"""
    st.cache_data.clear()

# Funções para manipulação de dados (sem cache)
def insert_transaction(engine, data, descricao, valor, categoria, tipo):
    """Insere nova transação e invalida cache"""
    try:
        with engine.connect() as conn:
            query = text("""
                INSERT INTO receita_gastos (Data, Descrição, Valor, Categorias, Tipo)
                VALUES (:data, :descricao, :valor, :categoria, :tipo)
            """)
            
            conn.execute(query, {
                'data': data,
                'descricao': descricao,
                'valor': valor,
                'categoria': categoria,
                'tipo': tipo
            })
            conn.commit()
        
        # Invalidar cache após inserção
        invalidate_cache()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir transação: {e}")
        return False

def delete_transaction(engine, transaction_id):
    """Deleta transação e invalida cache"""
    try:
        with engine.connect() as conn:
            query = text("DELETE FROM receita_gastos WHERE id = :id")
            conn.execute(query, {'id': transaction_id})
            conn.commit()
        
        # Invalidar cache após deleção
        invalidate_cache()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar transação: {e}")
        return False