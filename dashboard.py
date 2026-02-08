import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from parser import processar_semana
from datetime import datetime, timedelta
import os

# Configuração da página
st.set_page_config(
    page_title="Gym Reports 🏋️",
    page_icon="💪",
    layout="wide",  # usa tela toda
    initial_sidebar_state="expanded"
)




# ========================================
# SIDEBAR (parte 1 - antes de carregar dados)
# ========================================
st.sidebar.title("⚙️ Configurações")

aluno = st.sidebar.selectbox(
    "Escolha o aluno:",
    ["Kaue", "Barbara"]
)

foto_path = f"assets/{aluno.lower()}.jpg"
if os.path.exists(foto_path):
    st.sidebar.image(foto_path, width=150, caption=aluno)
else:
    st.sidebar.warning(f"Foto não encontrada: {foto_path}")

st.sidebar.markdown("---")
pagina = st.sidebar.radio(
    "Navegação:",
    ["📊 Dashboard", "📈 Evolução"]
)

# ========================================
# CARREGAR DADOS DO ALUNO
# ========================================
pasta_aluno = f"activities/{aluno}/"
df_sets, treinos_info = processar_semana(pasta_aluno)



# ========================================
# SIDEBAR (parte 2 - DEPOIS de carregar dados)
# ========================================
st.sidebar.markdown("---")

# Pega todas as datas únicas dos treinos
datas_treino = sorted(df_sets['data'].unique())
data_min = min(datas_treino)
data_max = max(datas_treino)

# Calcula início da semana (segunda-feira)
from datetime import timedelta
semana_atual = data_max - timedelta(days=data_max.weekday())

# Seletor de data inicial da semana
semana_selecionada = st.sidebar.date_input(
    "Semana (início):",
    value=semana_atual,
    min_value=data_min - timedelta(days=7),
    max_value=data_max,
    help="Escolha a segunda-feira da semana que deseja visualizar"
)

# Calcula fim da semana (domingo)
fim_semana = semana_selecionada + timedelta(days=6)

st.sidebar.caption(f"📅 Visualizando: {semana_selecionada.strftime('%d/%m')} a {fim_semana.strftime('%d/%m/%Y')}")

st.sidebar.markdown("---")
st.sidebar.caption(f"Aluno selecionado: **{aluno}**")





if pagina == "📊 Dashboard":


    # ========================================
    # FILTRAR DADOS PELA SEMANA SELECIONADA
    # ========================================
    if semana_selecionada:
        df_semana = df_sets[
            (df_sets['data'] >= semana_selecionada) &
            (df_sets['data'] <= fim_semana)
            ]
        treinos_semana = [t for t in treinos_info if semana_selecionada <= t['data'] <= fim_semana]
    else:
        df_semana = df_sets
        treinos_semana = treinos_info

    # Mostra período no header
    if semana_selecionada:
        st.caption(f"📅 Semana de {semana_selecionada.strftime('%d/%m')} a {fim_semana.strftime('%d/%m/%Y')}")

    # ========================================
    # SEÇÃO 1: MÉTRICAS (usa df_semana agora)
    # ========================================
    st.subheader(" Resumo Semanal")

    total_treinos = len(treinos_semana)
    dias_treinados = df_semana['data'].nunique() if not df_semana.empty else 0
    tempo_total = sum([t['duracao_total'] for t in treinos_semana]) if treinos_semana else 0



    # Mostra em 3 colunas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Treinos", total_treinos, help="Número de sessões de treino registradas")

    with col2:
        st.metric("Dias Treinados", dias_treinados, help="Quantidade de dias diferentes com treino")

    with col3:
        st.metric("Tempo Total", f"{tempo_total / 60:.0f} min", help="Duração total de treino na semana")


    st.markdown("---")

    # ========================================
    # SEÇÃO 2: CALENDÁRIO DA SEMANA
    # ========================================
    st.subheader("Calendário Semanal")

    # Cria lista com todos os 7 dias da semana
    dias_semana = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']

    # Gera todas as datas da semana
    from datetime import timedelta

    datas_semana_completa = [semana_selecionada + timedelta(days=i) for i in range(7)]

    # Identifica quais dias tiveram treino
    datas_com_treino = set(df_semana['data'].unique()) if not df_semana.empty else set()

    # Cria 7 colunas (uma pra cada dia)
    cols = st.columns(7)

    for i, (dia_nome, data) in enumerate(zip(dias_semana, datas_semana_completa)):
        with cols[i]:
            treinou = data in datas_com_treino

            if treinou:
                # Pega info do treino desse dia
                treino_dia = [t for t in treinos_semana if t['data'] == data]
                if treino_dia:
                    t = treino_dia[0]  # pega o primeiro (assumindo 1 treino por dia)

                    # Card do dia COM TREINO
                    st.markdown(f"""
                        <div style="
                            background-color: #d4edda;
                            border: 2px solid #28a745;
                            border-radius: 8px;
                            padding: 10px;
                            text-align: center;
                        ">
                            <div style="font-weight: bold; color: #155724; font-size: 14px;">{dia_nome}</div>
                            <div style="font-size: 11px; color: #155724;">{data.strftime('%d/%m')}</div>
                            <div style="font-size: 20px; margin: 5px 0;">✅</div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Detalhes do treino (abaixo do card)
                    st.markdown(f"""
                        <div style="
                            background-color: #f8f9fa;
                            border: 1px solid #dee2e6;
                            border-radius: 6px;
                            padding: 8px;
                            margin-top: 5px;
                            font-size: 11px;
                        ">
                            <div>⏱️ {t['duracao_total'] / 60:.0f} min</div>
                            <div>❤️ Média: {t['fc_media']:.0f} bpm</div>
                            <div>🔥 Max: {t['fc_maxima']:.0f} bpm</div>
                            <div>🏃 Aero: {t['training_effect_aerobico']:.1f}</div>
                            <div>⚡ Anaero: {t['training_effect_anaerobico']:.1f}</div>
                        </div>
                        """, unsafe_allow_html=True)

            else:
                # Dia SEM treino (igual antes)
                st.markdown(f"""
                    <div style="
                        background-color: #f8f9fa;
                        border: 2px solid #dee2e6;
                        border-radius: 8px;
                        padding: 10px;
                        text-align: center;
                        height: 100px;
                    ">
                        <div style="font-weight: bold; color: #6c757d;">{dia_nome}</div>
                        <div style="font-size: 12px; color: #6c757d;">{data.strftime('%d/%m')}</div>
                        <div style="font-size: 15px; margin-top: 10px;">Off</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")



    # ========================================
    # SEÇÃO 3: TIMELINE DO TREINO (História do treino)
    # ========================================
    st.subheader("📋 Timeline do Treino")

    if df_semana.empty:
        st.info("Nenhum treino nesta semana!")
    else:
        # Para cada dia com treino, cria a timeline
        datas_treino_semana = sorted(df_semana['data'].unique())

        for data in datas_treino_semana:
            st.markdown(f"#### 📅 {data.strftime('%d/%m/%Y - %A')}")

            # Filtra sets desse dia
            df_dia = df_semana[df_semana['data'] == data].sort_values('hora_inicio')

            # Agrupa por exercício na ordem que foram feitos
            exercicios_ordem = df_dia.groupby('exercicio', sort=False).first().reset_index()
            exercicios_ordem = exercicios_ordem.sort_values('hora_inicio')

            timeline_data = []

            for idx, exercicio_row in exercicios_ordem.iterrows():
                exercicio = exercicio_row['exercicio']

                # Pega todos os sets desse exercício nesse dia
                sets_exercicio = df_dia[df_dia['exercicio'] == exercicio]

                # Calcula médias
                tempo_exec_medio = sets_exercicio['duracao_set'].mean()

                # Descanso intra-exercício (só os 'descanso', não 'transição')
                descansos_intra = sets_exercicio[
                    sets_exercicio['tipo_intervalo'] == 'descanso'
                    ]['intervalo_apos']
                descanso_intra_medio = descansos_intra.mean() if len(descansos_intra) > 0 else None

                # Adiciona linha do exercício
                timeline_data.append({
                    'Etapa': exercicio.upper(),
                    'Tempo Exec (média)': f"{tempo_exec_medio:.1f}s",
                    'Descanso (média)': f"{descanso_intra_medio:.1f}s" if descanso_intra_medio else "--",
                    "Razão (Descanso / Execução) " : f"{descanso_intra_medio/tempo_exec_medio:.1f}:1" if descanso_intra_medio else "--"
                })

                # Pega a transição APÓS esse exercício (se existir)
                transicoes = sets_exercicio[
                    sets_exercicio['tipo_intervalo'] == 'transição'
                    ]['intervalo_apos']

                if len(transicoes) > 0:
                    transicao_media = transicoes.mean()
                    timeline_data.append({
                        'Etapa': '  → Transição',
                        'Tempo Exec (média)': '--',
                        'Descanso (média)': f"{transicao_media:.1f}s",
                        "Razão (Descanso / Execução) ": "--"
                    })

            # Mostra a tabela
            df_timeline = pd.DataFrame(timeline_data)
            st.dataframe(df_timeline, use_container_width=True, hide_index=True)

            st.markdown("---")