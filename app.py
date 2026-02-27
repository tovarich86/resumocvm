import streamlit as st
import pandas as pd
import json
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Planos de Remuneração", layout="wide")

# Função para carregar e processar os dados
@st.cache_data
def carregar_dados(caminho_arquivo):
    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    linhas = []
    for empresa, info in data.items():
        setor = info.get('setor', 'Não Informado')
        controle = info.get('controle_acionario', 'Não Informado')
        
        # Fatos extraídos no nível da empresa
        fatos_gerais = info.get('fatos_extraidos', {})
        vesting = fatos_gerais.get('periodo_vesting', {}).get('valor', None)
        diluicao = fatos_gerais.get('diluicao_maxima_percentual', {}).get('valor', None)
        clawback = fatos_gerais.get('malus_clawback_presente', {}).get('presente', False)
        
        planos = info.get('planos_identificados', {})
        for nome_plano, detalhes_plano in planos.items():
            docs = detalhes_plano.get('documentos_fonte', [])
            
            linhas.append({
                'Empresa': empresa,
                'Setor': setor,
                'Controle Acionário': controle,
                'Tipo de Plano': nome_plano,
                'Vesting Médio (Anos)': vesting,
                'Diluição Máxima (%)': diluicao,
                'Possui Malus/Clawback': 'Sim' if clawback else 'Não',
                'Qtd Documentos': len(docs),
                'Links': ", ".join(docs)
            })
            
    return pd.DataFrame(linhas)

# Carregar os dados (ajuste o nome do arquivo se necessário)
df = carregar_dados('resumo_fatos_e_topicos_v4_por_data (5).json')

# ==========================================
# BARRA LATERAL (FILTROS)
# ==========================================
st.sidebar.header("Filtros")

setores = st.sidebar.multiselect("Setor", options=df['Setor'].unique(), default=df['Setor'].unique())
tipos_plano = st.sidebar.multiselect("Tipo de Plano", options=df['Tipo de Plano'].unique(), default=df['Tipo de Plano'].unique())
controles = st.sidebar.multiselect("Controle Acionário", options=df['Controle Acionário'].unique(), default=df['Controle Acionário'].unique())

# Aplicar filtros
df_filtrado = df[
    (df['Setor'].isin(setores)) & 
    (df['Tipo de Plano'].isin(tipos_plano)) &
    (df['Controle Acionário'].isin(controles))
]

# ==========================================
# CORPO PRINCIPAL
# ==========================================
st.title("📊 Inteligência de Planos de Remuneração e Incentivos")
st.markdown("Visão consolidada de métricas de planos de ILP, Opções, Matching, Ações Restritas e governança atrelada.")

# Métricas Principais (KPIs)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Empresas", df_filtrado['Empresa'].nunique())
col2.metric("Total de Planos", len(df_filtrado))
col3.metric("Média de Diluição Máxima", f"{df_filtrado['Diluição Máxima (%)'].mean():.2f}%" if not df_filtrado['Diluição Máxima (%)'].isna().all() else "N/A")
col4.metric("Empresas com Malus/Clawback", df_filtrado[df_filtrado['Possui Malus/Clawback'] == 'Sim']['Empresa'].nunique())

st.divider()

# ==========================================
# GRÁFICOS INTERATIVOS
# ==========================================
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.subheader("Distribuição por Tipo de Plano")
    fig_planos = px.pie(df_filtrado, names='Tipo de Plano', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_planos, use_container_width=True)

with col_graf2:
    st.subheader("Top 10 Setores com Mais Planos")
    setor_counts = df_filtrado['Setor'].value_counts().reset_index().head(10)
    setor_counts.columns = ['Setor', 'Quantidade']
    fig_setores = px.bar(setor_counts, x='Quantidade', y='Setor', orientation='h', color='Quantidade', color_continuous_scale='Blues')
    fig_setores.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_setores, use_container_width=True)

col_graf3, col_graf4 = st.columns(2)

with col_graf3:
    st.subheader("Período de Vesting vs. Diluição Máxima")
    fig_scatter = px.scatter(df_filtrado, x='Vesting Médio (Anos)', y='Diluição Máxima (%)', color='Tipo de Plano', hover_data=['Empresa'])
    st.plotly_chart(fig_scatter, use_container_width=True)

with col_graf4:
    st.subheader("Adoção de Malus / Clawback")
    fig_clawback = px.pie(df_filtrado, names='Possui Malus/Clawback', color='Possui Malus/Clawback', color_discrete_map={'Sim': '#2ca02c', 'Não': '#d62728'})
    st.plotly_chart(fig_clawback, use_container_width=True)

st.divider()

# ==========================================
# TABELA DE DADOS DETALHADOS
# ==========================================
st.subheader("📋 Tabela de Dados Detalhados")
st.markdown("Use a tabela abaixo para explorar os dados ou exportá-los em CSV.")
st.dataframe(df_filtrado, use_container_width=True)
