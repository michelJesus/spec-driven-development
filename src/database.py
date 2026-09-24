"""Conexão PostgreSQL e execução estritamente somente leitura."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError


class DatabaseConfigurationError(RuntimeError):
    """Indica configuração ausente ou inválida, sem revelar seus valores."""


class DatabaseConnectionError(RuntimeError):
    """Indica falha ao conectar ao banco sem expor detalhes sensíveis."""


class DatabaseQueryError(RuntimeError):
    """Indica falha ao executar uma consulta permitida."""


class ReadOnlyViolation(ValueError):
    """Indica que uma instrução não é comprovadamente somente leitura."""


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


_ENV_KEYS = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")
_FORBIDDEN_SQL = re.compile(
    r"\b(?:insert|update|delete|merge|alter|drop|create|truncate|grant|revoke|"
    r"copy|call|do|vacuum|analyze|refresh|reindex|cluster|comment|lock)\b",
    flags=re.IGNORECASE,
)
_LOCKING_SELECT = re.compile(
    r"\bfor\s+(?:update|no\s+key\s+update|share|key\s+share)\b",
    flags=re.IGNORECASE,
)
_SELECT_INTO = re.compile(r"\bselect\b[\s\S]*?\binto\b", flags=re.IGNORECASE)


def _load_streamlit_settings() -> dict[str, str]:
    """Lê secrets no formato plano ou sob a seção ``database``."""
    try:
        secrets: Any = st.secrets
        nested = secrets.get("database", {})
        return {
            key: str(secrets.get(key) or nested.get(key) or "")
            for key in _ENV_KEYS
        }
    except Exception:
        # Fora do runtime Streamlit, st.secrets pode não estar configurado.
        return {}


def get_database_config() -> DatabaseConfig:
    """Carrega credenciais de ``st.secrets`` e completa com o ambiente/.env."""
    load_dotenv()
    secrets = _load_streamlit_settings()
    values = {key: secrets.get(key) or os.getenv(key, "") for key in _ENV_KEYS}
    missing = [key for key, value in values.items() if not value]
    if missing:
        fields = ", ".join(missing)
        raise DatabaseConfigurationError(
            f"Configuração do banco incompleta. Defina: {fields}."
        )

    try:
        port = int(values["DB_PORT"])
    except ValueError as exc:
        raise DatabaseConfigurationError("DB_PORT deve ser um número inteiro.") from exc

    if not 1 <= port <= 65535:
        raise DatabaseConfigurationError("DB_PORT deve estar entre 1 e 65535.")

    return DatabaseConfig(
        host=values["DB_HOST"],
        port=port,
        database=values["DB_NAME"],
        user=values["DB_USER"],
        password=values["DB_PASSWORD"],
    )


def create_database_engine(config: DatabaseConfig) -> Engine:
    """Cria um engine cujas conexões PostgreSQL nascem em modo somente leitura."""
    url = URL.create(
        drivername="postgresql+psycopg2",
        username=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.database,
    )
    return create_engine(
        url,
        pool_pre_ping=True,
        connect_args={
            "options": "-c default_transaction_read_only=on",
            "application_name": "dashboard_concessionarias_readonly",
        },
    )


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    """Retorna um único pool de conexões por processo da aplicação."""
    return create_database_engine(get_database_config())


def _sql_without_comments_or_literals(sql: str) -> str:
    """Remove conteúdo que não deve participar da validação lexical."""
    pattern = re.compile(
        r"--[^\r\n]*|/\*[\s\S]*?\*/|'(?:''|[^'])*'|\$([A-Za-z_]\w*)?\$[\s\S]*?\$\1\$",
        flags=re.MULTILINE,
    )
    return pattern.sub(" ", sql)


def validate_read_only_query(sql: str) -> None:
    """Rejeita SQL vazio, múltiplas instruções e comandos com escrita/lock."""
    if not isinstance(sql, str) or not sql.strip():
        raise ReadOnlyViolation("A consulta SQL não pode estar vazia.")

    normalized = _sql_without_comments_or_literals(sql).strip()
    statement = normalized[:-1].rstrip() if normalized.endswith(";") else normalized
    if ";" in statement:
        raise ReadOnlyViolation("Apenas uma instrução SQL é permitida por consulta.")
    if not re.match(r"^(?:select|with)\b", statement, flags=re.IGNORECASE):
        raise ReadOnlyViolation("Somente consultas SELECT são permitidas.")
    if _FORBIDDEN_SQL.search(statement):
        raise ReadOnlyViolation("A consulta contém uma operação não permitida.")
    if _SELECT_INTO.search(statement) or _LOCKING_SELECT.search(statement):
        raise ReadOnlyViolation("SELECT com escrita ou bloqueio não é permitido.")


def execute_query(
    sql: str,
    params: Mapping[str, Any] | None = None,
    *,
    engine: Engine | None = None,
) -> pd.DataFrame:
    """Valida e executa uma consulta parametrizada, retornando um DataFrame."""
    validate_read_only_query(sql)
    database_engine = engine or get_engine()
    try:
        with database_engine.connect() as connection:
            return pd.read_sql_query(text(sql), connection, params=dict(params or {}))
    except SQLAlchemyError as exc:
        raise DatabaseQueryError(
            "Não foi possível consultar o banco de dados. Tente novamente mais tarde."
        ) from exc


def test_connection(*, engine: Engine | None = None) -> bool:
    """Testa a conexão sem retornar URL, usuário, senha ou erro do driver."""
    database_engine = engine or get_engine()
    try:
        with database_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except (SQLAlchemyError, OSError) as exc:
        raise DatabaseConnectionError(
            "Não foi possível conectar ao banco de dados. Verifique a configuração e tente novamente."
        ) from exc
