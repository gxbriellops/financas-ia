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
    'neutral': '#708090',  # Cinza para elementos neutros
    'gradient_verde': ['#90EE90', '#228B22', '#006400'],  # Gradiente verde
    'gradient_vermelho': ['#FFA07A', '#DC143C', "#070404"]  # Gradiente vermelho
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

def criar_metricas_e_termometro(df):
    """Cria métricas principais e termômetro financeiro"""
    if df.empty:
        st.warning("📊 Nenhum dado encontrado. Adicione algumas transações no chat primeiro!")
        return
    
    # Calcular médias mensais
    meses_com_dados = df['MesAno'].nunique()
    media_receitas = df[df['Tipo'] == 'Ativo']['Valor'].sum() / max(meses_com_dados, 1)
    media_gastos = df[df['Tipo'] == 'Passivo']['Valor'].sum() / max(meses_com_dados, 1)
    
    # Saldo atual total
    receitas_total = df[df['Tipo'] == 'Ativo']['Valor'].sum()
    gastos_total = df[df['Tipo'] == 'Passivo']['Valor'].sum()
    saldo_atual = receitas_total - gastos_total
    
    # Meses de cobertura
    meses_cobertura = saldo_atual / media_gastos if media_gastos > 0 else float('inf')
    
    # Layout principal
    col1, col3 = st.columns([1, 2])
    
    with col1:
        st.metric(
            "💰 Média Mensal de Receitas", 
            f"R$ {media_receitas:,.2f}",
            delta=f"Baseado em {meses_com_dados} meses"
        )

        st.subheader(' ')
        st.subheader(' ')

        st.metric(
            "💸 Média Mensal de Gastos", 
            f"R$ {media_gastos:,.2f}",
            delta=f"Saldo atual: R$ {saldo_atual:,.2f}"
        )
    
    # with col2:
    
    with col3:
        # Termômetro financeiro
        st.markdown("### 🌡️ Termômetro Financeiro")
        
        if meses_cobertura == float('inf'):
            st.success("✨ Sem gastos registrados!")
        else:
            # Criar gauge/termômetro
            fig = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = min(meses_cobertura, 12),  # Limitar visualização a 12 meses
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Meses de Cobertura", 'font': {'size': 14}},
                delta = {'reference': 3, 'increasing': {'color': "green"}},
                gauge = {
                    'axis': {'range': [None, 12], 'tickwidth': 1, 'tickcolor': "darkblue"},
                    'bar': {'color': CORES['saldo_positivo'] if meses_cobertura >= 3 else CORES['saldo_negativo']},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "gray",
                    'steps': [
                        {'range': [0, 3], 'color': '#ffcccb'},
                        {'range': [3, 6], 'color': '#ffffcc'},
                        {'range': [6, 12], 'color': '#90EE90'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 3
                    }
                }
            ))
            
            fig.update_layout(
                height=200,
                margin=dict(l=20, r=20, t=40, b=0),
                font={'size': 12}
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Interpretação
            if meses_cobertura < 3:
                st.warning(f"⚠️ Atenção: Saldo cobre apenas {meses_cobertura:.1f} meses")
            elif meses_cobertura < 6:
                st.info(f"📊 Saldo cobre {meses_cobertura:.1f} meses de gastos")
            else:
                st.success(f"✅ Excelente! Saldo cobre {meses_cobertura:.1f} meses")

def criar_grafico_pizza(df):
    """Gráfico de pizza - Distribuição de gastos por categoria"""
    st.subheader("🎯 Distribuição de Gastos por Categoria")
    
    if df.empty:
        st.info("Nenhum dado disponível.")
        return

    # Filtrar apenas os gastos e agrupar por categoria
    gastos_df = df[df['Tipo'] == 'Passivo'].groupby('Categorias')['Valor'].sum().reset_index()
    gastos_df = gastos_df.sort_values('Valor', ascending=False)

    if not gastos_df.empty:
        fig = px.pie(
            gastos_df, 
            values='Valor', 
            names='Categorias',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label',
            hovertemplate='<b>%{label}</b><br>R$ %{value:,.2f}<br>%{percent}<extra></extra>'
        )
        
        fig.update_layout(
            height=400,
            font=dict(size=14),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum gasto registrado ainda.")

def criar_grafico_evolucao(df):
    """Gráfico combinado - Evolução e saldo mensal"""
    st.subheader("📈 Evolução Financeira Mensal")
    
    if df.empty:
        return
    
    # Preparar dados mensais
    df_mensal = df.groupby(['MesAno', 'Tipo'])['Valor'].sum().reset_index()
    df_pivot = df_mensal.pivot(index='MesAno', columns='Tipo', values='Valor').fillna(0)
    df_pivot['Saldo'] = df_pivot.get('Ativo', 0) - df_pivot.get('Passivo', 0)
    df_pivot = df_pivot.reset_index()
    
    if not df_pivot.empty:
        # Criar subplot com 2 gráficos
        fig = make_subplots(
            rows=2, cols=1,
            row_heights=[0.7, 0.3],
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=("Receitas vs Gastos", "Saldo Mensal")
        )
        
        # Gráfico 1: Linhas de receitas e gastos
        if 'Ativo' in df_pivot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_pivot['MesAno'],
                    y=df_pivot['Ativo'],
                    mode='lines+markers',
                    name='Receitas',
                    line=dict(color=CORES['receita'], width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>Receitas</b><br>%{x}<br>R$ %{y:,.2f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        if 'Passivo' in df_pivot.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_pivot['MesAno'],
                    y=df_pivot['Passivo'],
                    mode='lines+markers',
                    name='Gastos',
                    line=dict(color=CORES['gasto'], width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>Gastos</b><br>%{x}<br>R$ %{y:,.2f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Gráfico 2: Barras de saldo
        cores_saldo = [CORES['saldo_positivo'] if x >= 0 else CORES['saldo_negativo'] for x in df_pivot['Saldo']]
        
        fig.add_trace(
            go.Bar(
                x=df_pivot['MesAno'],
                y=df_pivot['Saldo'],
                marker_color=cores_saldo,
                name='Saldo',
                text=[f'R$ {x:,.0f}' for x in df_pivot['Saldo']],
                textposition='outside',
                hovertemplate='<b>Saldo</b><br>%{x}<br>R$ %{y:,.2f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        # Adicionar linha zero no gráfico de saldo
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5, row=2, col=1)
        
        # Atualizar layout
        fig.update_xaxes(title_text="Período", row=2, col=1)
        fig.update_yaxes(title_text="Valor (R$)", row=1, col=1)
        fig.update_yaxes(title_text="Saldo (R$)", row=2, col=1)
        
        fig.update_layout(
            height=600,
            showlegend=True,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Dados insuficientes para mostrar evolução temporal.")

def criar_tabela_transacoes(df):
    """Exibe tabela de transações recentes de forma mais elegante"""
    st.subheader("📋 Transações Recentes")
    
    if df.empty:
        st.info("Nenhuma transação registrada.")
        return
    
    # Preparar dados
    df_display = df.copy()
    df_display['Data'] = pd.to_datetime(df_display['Data'], format='mixed').dt.strftime('%d/%m/%Y')
    df_display['Valor_Formatado'] = df_display.apply(
        lambda x: f"+ R$ {x['Valor']:,.2f}" if x['Tipo'] == 'Ativo' else f"- R$ {x['Valor']:,.2f}",
        axis=1
    )
    
    # Selecionar e renomear colunas
    df_display = df_display[['Data', 'Descrição', 'Categorias', 'Valor_Formatado']]
    df_display.columns = ['Data', 'Descrição', 'Categoria', 'Valor']
    
    # Mostrar apenas as 10 últimas transações
    st.dataframe(
        df_display.head(10),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data": st.column_config.TextColumn("📅 Data"),
            "Descrição": st.column_config.TextColumn("📝 Descrição"),
            "Categoria": st.column_config.TextColumn("🏷️ Categoria"),
            "Valor": st.column_config.TextColumn("💵 Valor"),
        }
    )

# Interface principal do dashboard
def main():
    """Função principal do dashboard"""
    
    # Header
    st.title("📊 Dashboard Financeiro")
    st.markdown("**Visualize e entenda sua saúde financeira**")
    
    # Carregar dados
    df = carregar_dados()
    
    # Métricas e termômetro
    criar_metricas_e_termometro(df)
    
    st.markdown("---")
    
    # Gráficos principais
    col1, col2 = st.columns([1, 1.6])
    
    with col1:
        criar_grafico_pizza(df)
    
    with col2:
        criar_grafico_evolucao(df)
    
    st.markdown("---")
    
    # Tabela de transações
    criar_tabela_transacoes(df)
    
    # Botão de atualização
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🔄 Atualizar Dashboard", key="refresh_dashboard", use_container_width=True):
            st.rerun()

if __name__ == "__main__":
    main()