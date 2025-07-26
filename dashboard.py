import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from datetime import datetime, timedelta
import calendar

# Configuração
DB_PATH = 'sqlite:///./gastos_receita.db'
engine = create_engine(DB_PATH)

# Cores do tema (storytelling visual)
CORES = {
    'receita': '#2E8B57',  # Verde escuro para receitas
    'gasto': '#DC143C',    # Vermelho para gastos
    'saldo_positivo': '#228B22',  # Verde para saldo positivo
    'saldo_negativo': '#B22222',  # Vermelho escuro para saldo negativo
    'neutral': '#708090'   # Cinza para elementos neutros
}

def carregar_dados():
    """Carrega dados do banco SQLite"""
    try:
        query = """
        SELECT Data, Descrição, Valor, Categorias, Tipo, 
               strftime('%Y-%m', Data) as MesAno,
               strftime('%Y', Data) as Ano,
               strftime('%m', Data) as Mes
        FROM receita_gastos 
        ORDER BY Data DESC
        """
        df = pd.read_sql(query, engine)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

def criar_metricas(df):
    """Cria métricas principais"""
    if df.empty:
        st.warning("📊 Nenhum dado encontrado. Adicione algumas transações no chat primeiro!")
        return
    
    # Calcular totais
    receitas = df[df['Tipo'] == 'Ativo']['Valor'].sum()
    gastos = df[df['Tipo'] == 'Passivo']['Valor'].sum()
    saldo = receitas - gastos
    
    # Métricas do mês atual
    mes_atual = datetime.now().strftime('%Y-%m')
    df_mes = df[df['MesAno'] == mes_atual]
    receitas_mes = df_mes[df_mes['Tipo'] == 'Ativo']['Valor'].sum()
    gastos_mes = df_mes[df_mes['Tipo'] == 'Passivo']['Valor'].sum()
    saldo_mes = receitas_mes - gastos_mes
    
    # Exibir métricas
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "💰 Receitas Totais", 
            f"R$ {receitas:,.2f}",
            f"R$ {receitas_mes:,.2f} este mês"
        )
    
    with col2:
        st.metric(
            "💸 Gastos Totais", 
            f"R$ {gastos:,.2f}",
            f"R$ {gastos_mes:,.2f} este mês"
        )
    
    with col3:
        cor_saldo = CORES['saldo_positivo'] if saldo >= 0 else CORES['saldo_negativo']
        st.metric(
            "📊 Saldo", 
            f"R$ {saldo:,.2f}",
            f"R$ {saldo_mes:,.2f} este mês"
        )

def criar_grafico_barra(df):
    """Gráfico de barra - Distribuição de gastos por categoria"""
    st.subheader("📊 Onde Você Gasta Mais?")
    
    if df.empty:
        st.info("Nenhum dado disponível.")
        return

    # Filtrar apenas os gastos e agrupar por categoria
    gastos_df = df[df['Tipo'] == 'Passivo'].groupby('Categorias')['Valor'].sum().reset_index()
    gastos_df = gastos_df.sort_values('Valor', ascending=False)

    if not gastos_df.empty:
        fig = px.bar(
            data_frame=gastos_df,
            x='Categorias',
            y='Valor',
            text='Valor',
            labels={'Valor': 'Total Gasto (R$)', 'Categorias': 'Categoria'}
        )

        fig.update_traces(
            texttemplate='R$ %{y:,.2f}',
            textposition='outside'
        )

        fig.update_layout(
            height=400,
            font=dict(size=12),
            xaxis_tickangle=-45,
            yaxis_title=None,
            xaxis_title=None,
            margin=dict(t=20, b=40),
            showlegend=False  # Remove a legenda para ficar mais limpo
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum gasto registrado ainda.")


def criar_grafico_linhas(df):
    """Gráfico de linhas - Evolução temporal"""
    st.subheader("📅 Como Seus Gastos e Receitas Evoluem?")
    
    if df.empty:
        return
    
    # Agrupar por mês e tipo
    df_mensal = df.groupby(['MesAno', 'Tipo'])['Valor'].sum().reset_index()
    
    if not df_mensal.empty:
        # Pivotar para ter receitas e gastos como colunas
        df_pivot = df_mensal.pivot(index='MesAno', columns='Tipo', values='Valor').fillna(0)
        df_pivot = df_pivot.reset_index()
        
        fig = go.Figure()
        
        # Adicionar receitas
        if 'Ativo' in df_pivot.columns:
            fig.add_trace(go.Scatter(
                x=df_pivot['MesAno'],
                y=df_pivot['Ativo'],
                mode='lines+markers',
                name='Receitas',
                line=dict(color=CORES['receita'], width=3),
                marker=dict(size=8)
            ))
        
        # Adicionar gastos
        if 'Passivo' in df_pivot.columns:
            fig.add_trace(go.Scatter(
                x=df_pivot['MesAno'],
                y=df_pivot['Passivo'],
                mode='lines+markers',
                name='Gastos',
                line=dict(color=CORES['gasto'], width=3),
                marker=dict(size=8)
            ))
        
        fig.update_layout(
            title="Evolução Mensal de Receitas e Gastos",
            xaxis_title="Período",
            yaxis_title="Valor (R$)",
            hovermode='x unified',
            height=400,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dados insuficientes para mostrar evolução temporal.")

def criar_grafico_barras(df):
    """Gráfico de barras - Comparação mensal"""
    st.subheader("📊 Saldo Mensal: Você Está no Azul ou no Vermelho?")
    
    if df.empty:
        return
    
    # Calcular saldo mensal
    df_mensal = df.groupby(['MesAno', 'Tipo'])['Valor'].sum().reset_index()
    df_pivot = df_mensal.pivot(index='MesAno', columns='Tipo', values='Valor').fillna(0)
    df_pivot['Saldo'] = df_pivot.get('Ativo', 0) - df_pivot.get('Passivo', 0)
    df_pivot = df_pivot.reset_index()
    
    if not df_pivot.empty:
        # Definir cores baseadas no saldo
        cores = [CORES['saldo_positivo'] if x >= 0 else CORES['saldo_negativo'] for x in df_pivot['Saldo']]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_pivot['MesAno'],
            y=df_pivot['Saldo'],
            marker_color=cores,
            name='Saldo Mensal',
            text=[f'R$ {x:,.0f}' for x in df_pivot['Saldo']],
            textposition='outside'
        ))
        
        # Adicionar linha zero
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        fig.update_layout(
            title="Saldo Mensal (Receitas - Gastos)",
            xaxis_title="Período",
            yaxis_title="Saldo (R$)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dados insuficientes para calcular saldo mensal.")

def criar_insights(df):
    """Seção de insights e alertas"""
    if df.empty:
        return
    

    st.subheader("💡 Insights Financeiros")
    
    # Calcular alguns insights
    categoria_mais_gasta = df[df['Tipo'] == 'Passivo'].groupby('Categorias')['Valor'].sum().idxmax()
    valor_mais_gasto = df[df['Tipo'] == 'Passivo'].groupby('Categorias')['Valor'].sum().max()
    
    mes_atual = datetime.now().strftime('%Y-%m')
    gastos_mes_atual = df[(df['MesAno'] == mes_atual) & (df['Tipo'] == 'Passivo')]['Valor'].sum()
    
    # Calcular média mensal de gastos
    gastos_por_mes = df[df['Tipo'] == 'Passivo'].groupby('MesAno')['Valor'].sum()
    media_mensal = gastos_por_mes.mean() if not gastos_por_mes.empty else 0
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"🎯 **Categoria que mais consome seu dinheiro:** {categoria_mais_gasta} (R$ {valor_mais_gasto:,.2f})")
    
    with col2:
        if gastos_mes_atual > media_mensal * 1.2:
            st.warning(f"⚠️ **Atenção:** Gastos deste mês estão 20% acima da média!")
        else:
            st.success(f"✅ **Parabéns:** Gastos controlados este mês!")

# Interface principal do dashboard
def main():
    """Função principal do dashboard"""
    st.title("📊 Dashboard Financeiro")
    st.markdown("**Visualize sua saúde financeira de forma clara e objetiva**")
    
    # Carregar dados
    df = carregar_dados()
    
    # Métricas principais
    criar_metricas(df)
    
    st.markdown("---")
    
    # Layout de duas colunas para gráficos
    col1, col2 = st.columns(2)
    
    with col1:
        criar_grafico_barra(df)
    
    with col2:
        criar_grafico_linhas(df)
    
    # Gráfico de barras em largura total
    criar_grafico_barras(df)
    
    # Insights
    criar_insights(df)
    
    # Botão de atualização
    if st.button("🔄 Atualizar Dashboard", key="refresh_dashboard"):
        st.rerun()

    df_date = df.sort_values(by='Data', ascending=False)

    df_date = df_date.drop(columns=['MesAno', 'Ano', 'Mes'])

    df_date['Data'] = df_date['Data'].astype(str).str.replace(r'\s00:00:00$', '', regex=True)

    st.dataframe(df_date)

if __name__ == "__main__":
    main()