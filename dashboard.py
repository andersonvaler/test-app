import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Uso de Feature Flags",
    page_icon="🚩",
    layout="wide"
)

# Título
st.title("🚩 Dashboard de Uso de Feature Flags")
st.markdown("Análise do uso de flags por origem e nome")

# Carregar dados
@st.cache_data
def load_data():
    with open("out.json", "r") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    return df

df = load_data()

# Métricas gerais
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📊 Total de Registros", f"{len(df):,}")
with col2:
    st.metric("🏷️ Flags Únicas", f"{df['name'].nunique():,}")
with col3:
    st.metric("🔗 Origins Únicos", f"{df['origin'].nunique():,}")
with col4:
    total_sum = df['sum'].sum()
    st.metric("📈 Total de Chamadas", f"{total_sum:,.0f}")

st.divider()

# Sidebar com filtros
st.sidebar.header("🔍 Filtros")

# Filtro por origem
all_origins = sorted(df['origin'].unique())
selected_origins = st.sidebar.multiselect(
    "Selecione Origins",
    options=all_origins,
    default=None,
    placeholder="Todas as origins"
)

# Filtro por nome de flag
search_flag = st.sidebar.text_input("🔎 Buscar Flag por nome", "")

# Aplicar filtros
df_filtered = df.copy()
if selected_origins:
    df_filtered = df_filtered[df_filtered['origin'].isin(selected_origins)]
if search_flag:
    df_filtered = df_filtered[df_filtered['name'].str.contains(search_flag, case=False, na=False)]

st.sidebar.markdown(f"**Registros filtrados:** {len(df_filtered):,}")

# Layout principal com tabs
tab1, tab2, tab3, tab4 = st.tabs(["📊 Visão Geral", "🔗 Por Origin", "🏷️ Por Flag", "📋 Dados"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 20 Origins por Total de Chamadas")
        origin_sum = df_filtered.groupby('origin')['sum'].sum().sort_values(ascending=False).head(20)
        fig_origin = px.bar(
            x=origin_sum.values,
            y=origin_sum.index,
            orientation='h',
            labels={'x': 'Total de Chamadas', 'y': 'Origin'},
            color=origin_sum.values,
            color_continuous_scale='Blues'
        )
        fig_origin.update_layout(height=600, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_origin, use_container_width=True)
    
    with col2:
        st.subheader("🏆 Top 20 Flags Mais Utilizadas")
        flag_sum = df_filtered.groupby('name')['sum'].sum().sort_values(ascending=False).head(20)
        fig_flags = px.bar(
            x=flag_sum.values,
            y=flag_sum.index,
            orientation='h',
            labels={'x': 'Total de Chamadas', 'y': 'Flag'},
            color=flag_sum.values,
            color_continuous_scale='Greens'
        )
        fig_flags.update_layout(height=600, showlegend=False, yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_flags, use_container_width=True)

    # Distribuição de chamadas por origin (treemap interativo)
    st.subheader("🗺️ Mapa de Distribuição de Chamadas (clique para expandir)")
    st.caption("💡 Clique em uma origin para ver as flags. Clique no centro para voltar.")
    
    fig_treemap = px.treemap(
        df_filtered,
        path=['origin', 'name'],
        values='sum',
        color='sum',
        color_continuous_scale='RdYlGn',
        hover_data={'sum': ':,.0f'}
    )
    fig_treemap.update_layout(height=600)
    fig_treemap.update_traces(
        textinfo="label+value",
        texttemplate="%{label}<br>%{value:,.0f}",
        hovertemplate="<b>%{label}</b><br>Chamadas: %{value:,.0f}<extra></extra>"
    )
    st.plotly_chart(fig_treemap, use_container_width=True)
    
    # Treemap só por flags (top 50)
    st.subheader("🏷️ Mapa de Distribuição por Flag (Top 50)")
    top_flags = df_filtered.groupby('name')['sum'].sum().sort_values(ascending=False).head(50).reset_index()
    
    fig_treemap_flags = px.treemap(
        top_flags,
        path=['name'],
        values='sum',
        color='sum',
        color_continuous_scale='Viridis',
    )
    fig_treemap_flags.update_layout(height=500)
    fig_treemap_flags.update_traces(
        textinfo="label+value",
        texttemplate="%{label}<br>%{value:,.0f}",
        hovertemplate="<b>%{label}</b><br>Chamadas: %{value:,.0f}<extra></extra>"
    )
    st.plotly_chart(fig_treemap_flags, use_container_width=True)

with tab2:
    st.subheader("📊 Análise Detalhada por Origin")
    
    # Seletor de origin
    selected_origin = st.selectbox(
        "Selecione uma Origin para análise detalhada",
        options=sorted(df_filtered['origin'].unique())
    )
    
    if selected_origin:
        df_origin = df_filtered[df_filtered['origin'] == selected_origin]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Flags", len(df_origin))
        with col2:
            st.metric("Total de Chamadas", f"{df_origin['sum'].sum():,.0f}")
        with col3:
            st.metric("Média por Flag", f"{df_origin['sum'].mean():,.0f}")
        
        # Top flags dessa origin
        st.subheader(f"🏷️ Flags de '{selected_origin}'")
        fig_origin_flags = px.bar(
            df_origin.sort_values('sum', ascending=True).tail(30),
            x='sum',
            y='name',
            orientation='h',
            labels={'sum': 'Total de Chamadas', 'name': 'Flag'},
            color='sum',
            color_continuous_scale='Viridis'
        )
        fig_origin_flags.update_layout(height=max(400, len(df_origin.head(30)) * 25))
        st.plotly_chart(fig_origin_flags, use_container_width=True)

with tab3:
    st.subheader("🔎 Análise Detalhada por Flag")
    
    # Busca de flag específica
    flag_search = st.text_input("Digite o nome da flag (parcial ou completo)", key="flag_detail_search")
    
    if flag_search:
        df_flag = df_filtered[df_filtered['name'].str.contains(flag_search, case=False, na=False)]
        
        if not df_flag.empty:
            st.info(f"Encontradas {len(df_flag)} flags correspondentes")
            
            # Agrupar por nome de flag
            flag_usage = df_flag.groupby('name').agg({
                'sum': 'sum',
                'origin': lambda x: list(x)
            }).reset_index()
            flag_usage.columns = ['name', 'total_calls', 'origins']
            flag_usage['num_origins'] = flag_usage['origins'].apply(len)
            flag_usage = flag_usage.sort_values('total_calls', ascending=False)
            
            # Gráfico de uso por flag
            fig_flag_usage = px.bar(
                flag_usage.head(20),
                x='name',
                y='total_calls',
                color='num_origins',
                labels={'name': 'Flag', 'total_calls': 'Total de Chamadas', 'num_origins': 'Nº Origins'},
                title="Uso das Flags Encontradas"
            )
            fig_flag_usage.update_xaxes(tickangle=45)
            st.plotly_chart(fig_flag_usage, use_container_width=True)
            
            # Detalhes por flag selecionada
            selected_flag = st.selectbox(
                "Selecione uma flag para ver detalhes",
                options=flag_usage['name'].tolist()
            )
            
            if selected_flag:
                df_selected = df_flag[df_flag['name'] == selected_flag]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Flag:** `{selected_flag}`")
                    st.markdown(f"**Total de Origins:** {len(df_selected)}")
                    st.markdown(f"**Total de Chamadas:** {df_selected['sum'].sum():,.0f}")
                
                with col2:
                    # Pie chart de distribuição por origin
                    fig_pie = px.pie(
                        df_selected,
                        values='sum',
                        names='origin',
                        title=f"Distribuição por Origin"
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Nenhuma flag encontrada com esse termo")
    else:
        # Mostrar flags mais compartilhadas (usadas por mais origins)
        st.subheader("🔀 Flags Mais Compartilhadas (usadas por múltiplos origins)")
        
        shared_flags = df_filtered.groupby('name').agg({
            'origin': 'nunique',
            'sum': 'sum'
        }).reset_index()
        shared_flags.columns = ['name', 'num_origins', 'total_calls']
        shared_flags = shared_flags[shared_flags['num_origins'] > 1].sort_values('num_origins', ascending=False).head(30)
        
        fig_shared = px.scatter(
            shared_flags,
            x='num_origins',
            y='total_calls',
            size='total_calls',
            hover_name='name',
            labels={'num_origins': 'Número de Origins', 'total_calls': 'Total de Chamadas'},
            title="Flags por Número de Origins vs Total de Chamadas"
        )
        st.plotly_chart(fig_shared, use_container_width=True)
        
        # Tabela das flags mais compartilhadas
        st.dataframe(
            shared_flags[['name', 'num_origins', 'total_calls']].head(20),
            use_container_width=True,
            hide_index=True
        )

with tab4:
    st.subheader("📋 Dados Brutos")
    
    # Opções de ordenação
    col1, col2 = st.columns(2)
    with col1:
        sort_by = st.selectbox("Ordenar por", ['sum', 'name', 'origin'])
    with col2:
        sort_order = st.selectbox("Ordem", ['Decrescente', 'Crescente'])
    
    ascending = sort_order == 'Crescente'
    df_display = df_filtered.sort_values(sort_by, ascending=ascending)
    
    # Formatação do sum para melhor visualização
    df_display_formatted = df_display.copy()
    df_display_formatted['sum_formatted'] = df_display_formatted['sum'].apply(lambda x: f"{x:,.0f}")
    
    st.dataframe(
        df_display_formatted[['origin', 'name', 'sum_formatted', 'sum']],
        use_container_width=True,
        hide_index=True,
        column_config={
            "origin": "Origin",
            "name": "Flag Name",
            "sum_formatted": "Chamadas (formatado)",
            "sum": st.column_config.NumberColumn("Chamadas", format="%d")
        }
    )
    
    # Download
    csv = df_filtered.to_csv(index=False)
    st.download_button(
        label="📥 Baixar dados filtrados (CSV)",
        data=csv,
        file_name="flags_usage_filtered.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.caption("Dashboard de análise de uso de Feature Flags")
