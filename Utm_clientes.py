import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from pytz import timezone

# Atualização automática a cada 2 minutos
st_autorefresh(interval=120 * 1000, key="auto_refresh")

# Função para formatar data ISO
def formatar_data(data_iso):
    try:
        return datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
    except:
        return None

# Carregar dados da API
def carregar_dados_utm_clientes():
    url_managers = "https://tracker-api.avalieempresas.live/api/managers"
    url_base_tx = "https://tracker-api.avalieempresas.live/api/transactions/manager/"
    transacoes = []

    try:
        res_managers = requests.get(url_managers)
        res_managers.raise_for_status()
        managers = res_managers.json()
    except Exception as e:
        st.error(f"Erro ao buscar gerentes: {e}")
        return pd.DataFrame()

    for manager in managers:
        manager_id = manager.get("manager_id")
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
                    transacoes.append({
                        "UTM Source": tx.get("utm_source", ""),
                        "Client Name": tx.get("clientName", ""),
                        "Client Email": tx.get("clientEmail", ""),
                        "Client Phone": tx.get("clientPhone", ""),
                        "Client CPF": tx.get("clientCpf", ""),
                    })

                page += 1
            except Exception as e:
                st.warning(f"Erro nas transações do gerente {manager_id}: {e}")
                break

    return pd.DataFrame(transacoes)

# Página
st.set_page_config(page_title="UTM e Clientes", layout="wide")
st.title("📋 UTM Sources + Informações dos Clientes")

# Hora da atualização
br_tz = timezone("America/Sao_Paulo")
hora_atual = datetime.now(br_tz).strftime('%H:%M:%S')
st.caption(f"⏰ Última atualização: {hora_atual}")

# Carregar dados
df = carregar_dados_utm_clientes()
if df.empty:
    st.warning("Nenhum dado encontrado.")
    st.stop()

# Mostrar tabela
st.dataframe(df, use_container_width=True)

# Baixar CSV
st.download_button(
    label="⬇️ Baixar CSV",
    data=df.to_csv(index=False).encode("utf-8"),
    file_name="utm_clientes.csv",
    mime="text/csv"
)
