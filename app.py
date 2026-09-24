"""Página inicial Streamlit e verificação segura da conexão."""

import streamlit as st

from src.database import (
    DatabaseConfigurationError,
    DatabaseConnectionError,
    test_connection,
)


st.set_page_config(page_title="Dashboard de Concessionárias", layout="wide")
st.title("Dashboard de Concessionárias")

try:
    test_connection()
except (DatabaseConfigurationError, DatabaseConnectionError) as error:
    st.error(str(error))
else:
    st.success("Conexão somente leitura estabelecida com sucesso.")
