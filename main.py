import pandas as pd
import os
from fitparse import FitFile
from datetime import datetime

# Abre o arquivo .fit
temp_fitfile = 'activities/21787457234_ACTIVITY.fit'

import pandas as pd
from fitparse import FitFile
from datetime import datetime


def parse_fit_to_dataframe(fit_input):
    """
    Processa arquivo .fit e retorna:
    - df_sets: DataFrame com dados dos sets
    - treino_info: dict com informações gerais do treino
    """

    if isinstance(fit_input, str):
        fitfile = FitFile(fit_input)
    else:
        fitfile = fit_input

    # ========================================
    # PARTE 1: Extrair info geral do treino (SESSION)
    # ========================================
    treino_info = {}
    for record in fitfile.get_messages('session'):
        data_dict = {}
        for data in record:
            data_dict[data.name] = data.value

        treino_info = {
            'data': data_dict.get('start_time').date() if data_dict.get('start_time') else None,
            'inicio': data_dict.get('start_time'),
            'fim': data_dict.get('timestamp'),
            'duracao_total': data_dict.get('total_elapsed_time', 0),
            'fc_media': data_dict.get('avg_heart_rate', 0),
            'fc_maxima': data_dict.get('max_heart_rate', 0),
            'training_effect_aerobico': data_dict.get('total_training_effect', 0),
            'training_effect_anaerobico': data_dict.get('total_anaerobic_training_effect', 0),
            'calorias': data_dict.get('total_calories', 0),
        }
        break  # só tem 1 session por treino

    # ========================================
    # PARTE 2: Extrair FC por segundo (RECORD)
    # ========================================
    records_fc = []
    for record in fitfile.get_messages('record'):
        data_dict = {}
        for data in record:
            data_dict[data.name] = data.value

        if data_dict.get('heart_rate'):
            records_fc.append({
                'timestamp': data_dict.get('timestamp'),
                'heart_rate': data_dict.get('heart_rate')
            })

    df_fc = pd.DataFrame(records_fc)

    # ========================================
    # PARTE 3: Processar SETS (igual antes)
    # ========================================
    all_sets = []
    for record in fitfile.get_messages('set'):
        data_dict = {}
        for data in record:
            data_dict[data.name] = data.value
        all_sets.append(data_dict)

    sets_data = []
    exercise_counters = {}

    for i, set_dict in enumerate(all_sets):
        if set_dict.get('set_type') != 'active':
            continue

        exercicio = set_dict.get('category')

        if exercicio in [None, 'unknown']:
            continue

        if exercicio not in exercise_counters:
            exercise_counters[exercicio] = 1
        else:
            exercise_counters[exercicio] += 1

        start_time = set_dict.get('start_time')
        timestamp = set_dict.get('timestamp')

        # ========================================
        # NOVO: Calcular FC média durante o set
        # ========================================
        fc_durante_set = None
        if len(df_fc) > 0 and start_time and timestamp:
            fc_no_set = df_fc[
                (df_fc['timestamp'] >= start_time) &
                (df_fc['timestamp'] <= timestamp)
                ]
            if len(fc_no_set) > 0:
                fc_durante_set = fc_no_set['heart_rate'].mean()

        set_info = {
            'data': start_time.date() if start_time else None,
            'dia_semana': start_time.strftime('%A') if start_time else None,  # NOVO
            'hora_inicio': start_time.time() if start_time else None,
            'exercicio': exercicio,
            'set_num': exercise_counters[exercicio],
            'reps': set_dict.get('repetitions', 0),
            'peso': set_dict.get('weight', 0.0),
            'duracao_set': set_dict.get('duration', 0.0),
            'fc_media_set': round(fc_durante_set, 1) if fc_durante_set else None,  # NOVO
        }

        # Próximo set ativo válido
        next_active_set = None
        for j in range(i + 1, len(all_sets)):
            if (all_sets[j].get('set_type') == 'active' and
                    all_sets[j].get('category') not in [None, 'unknown']):
                next_active_set = all_sets[j]
                break

        # Período de REST
        rest_duration = None
        if i + 1 < len(all_sets) and all_sets[i + 1].get('set_type') == 'rest':
            rest_duration = all_sets[i + 1].get('duration')

        if next_active_set:
            next_category = next_active_set.get('category')

            if rest_duration:
                intervalo = rest_duration
            else:
                next_start = next_active_set.get('start_time')
                intervalo = (next_start - timestamp).total_seconds()

            tipo_intervalo = 'descanso' if next_category == exercicio else 'transição'
        else:
            intervalo = None
            tipo_intervalo = None

        set_info['intervalo_apos'] = intervalo
        set_info['tipo_intervalo'] = tipo_intervalo

        sets_data.append(set_info)

    df_sets = pd.DataFrame(sets_data)

    return df_sets, treino_info


import os
import pandas as pd


def processar_semana(pasta='activities/'):
    """
    Processa todos os .fit da pasta e retorna:
    - df_todos_sets: DataFrame consolidado com TODOS os sets da semana
    - treinos_info: lista com info de cada treino
    """

    todos_sets = []
    treinos_info = []

    arquivos_fit = [f for f in os.listdir(pasta) if f.endswith('.fit')]

    print(f"📂 Encontrados {len(arquivos_fit)} arquivos .fit")

    for arquivo in sorted(arquivos_fit):
        caminho = os.path.join(pasta, arquivo)
        print(f"  Processando {arquivo}...")

        try:
            df_sets, info_treino = parse_fit_to_dataframe(caminho)

            # Adiciona identificador do arquivo
            df_sets['arquivo'] = arquivo

            todos_sets.append(df_sets)
            treinos_info.append(info_treino)

            print(f"    ✅ {len(df_sets)} sets, {info_treino['duracao_total']:.0f}s, FC média {info_treino['fc_media']}")

        except Exception as e:
            print(f"    ❌ Erro ao processar {arquivo}: {e}")

    # Concatena todos os DataFrames
    if todos_sets:
        df_completo = pd.concat(todos_sets, ignore_index=True)
        df_completo = df_completo.sort_values(['data', 'hora_inicio']).reset_index(drop=True)
    else:
        df_completo = pd.DataFrame()

    return df_completo, treinos_info


# ========================================
# USO:
# ========================================
df_semana, info_treinos = processar_semana('activities/')

print("\n" + "=" * 60)
print("📊 RESUMO DA SEMANA")
print("=" * 60)
print(f"Total de treinos: {len(info_treinos)}")
print(f"Total de sets: {len(df_semana)}")
print(f"Dias treinados: {df_semana['data'].nunique()}")

print("\n📅 Treinos por dia:")
print(df_semana.groupby(['data', 'dia_semana']).size())

print("\n💪 Sets por exercício:")
print(df_semana.groupby('exercicio')['set_num'].max().sort_values(ascending=False))