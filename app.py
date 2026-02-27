import streamlit as st
import pandas as pd
import json
import plotly.express as px

# 1. Configuração da página (Deve ser o primeiro comando)
st.set_page_config(page_title="Inteligência de Remuneração e ILP", layout="wide", page_icon="📊")

# 2. Função para carregar e estruturar os dados
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
                'Links': docs # Mantemos como lista para criar botões depois
            })
            
    return pd.DataFrame(linhas)

# Carregar os dados do JSON
df = carregar_dados('resumo_fatos_e_topicos_v4_por_data (5).json')

# ==========================================
# BARRA LATERAL (FILTROS GLOBAIS)
# ==========================================
st.sidebar.title("🔍 Filtros Globais")
st.sidebar.markdown("Use estes filtros para refinar toda a análise no dashboard.")

setores = st.sidebar.multiselect("Setor", options=sorted(df['Setor'].unique()), default=df['Setor'].unique())
tipos_plano = st.sidebar.multiselect("Tipo de Plano", options=sorted(df['Tipo de Plano'].unique()), default=df['Tipo de Plano'].unique())
controles = st.sidebar.multiselect("Controle Acionário", options=sorted(df['Controle Acionário'].unique()), default=df['Controle Acionário'].unique())

# Aplicar filtros ao dataframe
df_filtrado = df[
    (df['Setor'].isin(setores)) & 
    (df['Tipo de Plano'].isin(tipos_plano)) &
    (df['Controle Acionário'].isin(controles))
]

st.sidebar.divider()
st.sidebar.info(f"A apresentar dados de **{df_filtrado['Empresa'].nunique()}** empresas de acordo com os filtros selecionados.")

# ==========================================
# CABEÇALHO E NAVEGAÇÃO (TABS)
# ==========================================
st.title("📊 Painel de Inteligência: Planos de Remuneração e Incentivos")

# Criamos 4 abas de navegação que funcionam como páginas
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 1. Visão Executiva", 
    "⚖️ 2. Benchmarking Setorial", 
    "🛡️ 3. Radar de Governança", 
    "🏢 4. Explorador de Empresas"
])

# ------------------------------------------
# TAB 1: VISÃO EXECUTIVA
# ------------------------------------------
with tab1:
    st.subheader("Resumo Macro do Mercado")
    
    # KPIs Rápidos
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Empresas Analisadas", df_filtrado['Empresa'].nunique())
    col2.metric("Total de Planos Ativos", len(df_filtrado))
    
    media_diluicao = df_filtrado['Diluição Máxima (%)'].mean()
    col3.metric("Diluição Máxima (Média)", f"{media_diluicao:.2f}%" if pd.notna(media_diluicao) else "N/A")
    
    # Cálculo de adoção de Clawback
    qtd_clawback = len(df_filtrado[df_filtrado['Possui Malus/Clawback'] == 'Sim'])
    taxa_clawback = (qtd_clawback / len(df_filtrado)) * 100 if len(df_filtrado) > 0 else 0
    col4.metric("Adoção de Malus/Clawback", f"{taxa_clawback:.1f}%")

    st.divider()
    
    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.markdown("**Top 10 Setores com Mais Planos**")
        setor_counts = df_filtrado['Setor'].value_counts().reset_index().head(10)
        setor_counts.columns = ['Setor', 'Quantidade']
        fig_setores = px.bar(setor_counts, x='Quantidade', y='Setor', orientation='h', color='Quantidade', color_continuous_scale='Blues')
        fig_setores.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
        st.plotly_chart(fig_setores, use_container_width=True)

    with col_graf2:
        st.markdown("**Distribuição por Tipo de Plano (Market Share)**")
        fig_planos = px.pie(df_filtrado, names='Tipo de Plano', hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_planos, use_container_width=True)

# ------------------------------------------
# TAB 2: BENCHMARKING SETORIAL
# ------------------------------------------
with tab2:
    st.subheader("Análise Comparativa (Outliers e Padrões)")
    st.markdown("Identifique empresas com alto nível de diluição vs. prazos curtos de vesting.")
    
    col_graf3, col_graf4 = st.columns([2, 1])
    
    with col_graf3:
        st.markdown("**Matriz: Período de Vesting vs. Diluição Máxima**")
        fig_scatter = px.scatter(
            df_filtrado, x='Vesting Médio (Anos)', y='Diluição Máxima (%)', 
            color='Setor', hover_name='Empresa', hover_data=['Tipo de Plano', 'Controle Acionário'],
            size_max=15, opacity=0.8
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with col_graf4:
        st.markdown("**Distribuição de Vesting por Controle Acionário**")
        fig_box = px.box(df_filtrado, x='Controle Acionário', y='Vesting Médio (Anos)', color='Controle Acionário')
        fig_box.update_layout(showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

# ------------------------------------------
# TAB 3: RADAR DE GOVERNANÇA E RISCO
# ------------------------------------------
with tab3:
    st.subheader("Cláusulas de Proteção ao Acionista")
    
    col_gov1, col_gov2 = st.columns(2)
    with col_gov1:
        st.markdown("**Proporção de Planos com Malus / Clawback**")
        fig_clawback = px.pie(df_filtrado, names='Possui Malus/Clawback', color='Possui Malus/Clawback', color_discrete_map={'Sim': '#198754', 'Não': '#dc3545'}, hole=0.4)
        st.plotly_chart(fig_clawback, use_container_width=True)
        
    with col_gov2:
        st.markdown("**Adoção de Clawback por Setor (Top 10)**")
        top_setores = df_filtrado['Setor'].value_counts().head(10).index
        df_top_setores = df_filtrado[df_filtrado['Setor'].isin(top_setores)]
        fig_bar_stacked = px.histogram(df_top_setores, y="Setor", color="Possui Malus/Clawback", orientation='h', barmode='group', color_discrete_map={'Sim': '#198754', 'Não': '#dc3545'})
        fig_bar_stacked.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar_stacked, use_container_width=True)

# ------------------------------------------
# TAB 4: EXPLORADOR DE EMPRESAS (DEEP DIVE)
# ------------------------------------------
with tab4:
    st.subheader("Dossiê por Empresa")
    st.markdown("Selecione uma empresa específica para aceder aos detalhes e aos links oficias da CVM.")
    
    # Campo de busca interativo
    empresa_selecionada = st.selectbox("Pesquise pelo nome da empresa:", options=[""] + sorted(df_filtrado['Empresa'].unique()))
    
    if empresa_selecionada:
        dados_empresa = df_filtrado[df_filtrado['Empresa'] == empresa_selecionada]
        info_geral = dados_empresa.iloc[0]
        
        # Perfil da Empresa
        st.markdown(f"### 🏢 {empresa_selecionada}")
        st.markdown(f"**Setor de Atuação:** {info_geral['Setor']} | **Modelo de Controle:** {info_geral['Controle Acionário']}")
        st.divider()
        
        st.markdown("#### Planos Identificados e Documentos")
        
        # Cria um card (expander) para cada plano que a empresa tem
        for index, row in dados_empresa.iterrows():
            with st.expander(f"📌 {row['Tipo de Plano']}", expanded=True):
                c1, c2, c3 = st.columns(3)
                c1.metric("Vesting (Anos)", row['Vesting Médio (Anos)'])
                c2.metric("Diluição Máxima", f"{row['Diluição Máxima (%)']}%" if pd.notna(row['Diluição Máxima (%)']) else "N/A")
                c3.metric("Proteção (Clawback)", row['Possui Malus/Clawback'])
                
                st.markdown("**📄 Acesso Direto aos Fatos Relevantes / Editais (CVM):**")
                # Exibe os links de forma muito mais elegante e clicável
                for i, link in enumerate(row['Links'], 1):
                    st.markdown(f"- [Aceder ao Documento {i} na plataforma da CVM]({link})")
