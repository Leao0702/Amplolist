import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from pytz import timezone

# Atualização automática a cada 2 minutos
st_autorefresh(interval=120 * 1000, key="auto_refresh")

# Formata data ISO em dd/mm/yyyy
def formatar_data(data_iso):
    try:
        return datetime.fromisoformat(data_iso.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except:
        return ""

# Função para buscar dados
def carregar_dados():
    url_managers = "https://tracker-api.avalieempresas.live/api/managers"
    url_base_tx = "https://tracker-api.avalieempresas.live/api/transactions/manager/"
    registros = []

    try:
        res_managers = requests.get(url_managers)
        res_managers.raise_for_status()
        managers = res_managers.json()
    except Exception as e:
        st.error(f"Erro ao buscar gerentes: {e}")
        return pd.DataFrame()

    for manager in managers:
        manager_id = manager.get("manager_id")
        manager_name = manager.get("name")
        page = 1

        while True:
            url = f"{url_base_tx}{manager_id}?page={page}&limit=100&startDate=2000-01-01"
            try:
                res_tx = requests.get(url)
                if res_tx.status_code != 200:
                    break

                data = res_tx.json()
                txs = data.get("transactions", [])
                if not txs:
                    break

                for tx in txs:
                    registros.append({
                        "Manager Name": manager_name,
                        "UTM Source": tx.get("utm_source", ""),
                        "Created At": formatar_data(tx.get("createdAt", "")),
                    })

                page += 1
            except Exception as e:
                st.warning(f"Erro ao carregar transações de {manager_name}: {e}")
                break

    df = pd.DataFrame(registros)
    return df

# Configuração da página
st.set_page_config(page_title="Painel UTM Consolidado", layout="wide")
st.title("📋 UTM Sources por Gerente")

# Hora de atualização
br_tz = timezone("America/Sao_Paulo")
hora_atual = datetime.now(br_tz).strftime('%H:%M:%S')
st.caption(f"⏰ Última atualização: {hora_atual}")

# Carrega dados
df = carregar_dados()
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# Remove duplicações
df = df.drop_duplicates(subset=["Manager Name", "UTM Source", "Created At"])

# Sidebar: filtro por UTM Source
st.sidebar.header("🔎 Filtrar por UTM Source")
utm_opcoes = df["UTM Source"].dropna().unique().tolist()
utm_selecionada = st.sidebar.selectbox("Selecione uma UTM", options=["Todas"] + utm_opcoes)

if utm_selecionada != "Todas":
    df_filtrado = df[df["UTM Source"] == utm_selecionada]
else:
    df_filtrado = df

# Mostra a tabela final
st.dataframe(df_filtrado, use_container_width=True)

# Botão de download
st.download_button(
    label="⬇️ Baixar CSV",
    data=df_filtrado.to_csv(index=False).encode("utf-8"),
    file_name="utm_gerentes.csv",
    mime="text/csv"
)
