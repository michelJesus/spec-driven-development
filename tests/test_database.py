from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.exc import OperationalError

from src.database import (
    DatabaseConfig,
    DatabaseConnectionError,
    ReadOnlyViolation,
    create_database_engine,
    test_connection as check_connection,
    validate_read_only_query,
)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO vendas (id_vendas) VALUES (1)",
        "UPDATE vendas SET valor_pago = 0",
        "DELETE FROM vendas",
        "DROP TABLE vendas",
        "TRUNCATE vendas",
        "WITH removidas AS (DELETE FROM vendas RETURNING *) SELECT * FROM removidas",
        "SELECT id_vendas INTO vendas_copia FROM vendas",
        "SELECT id_vendas FROM vendas FOR UPDATE",
        "SELECT 1; DELETE FROM vendas",
    ],
)
def test_bloqueia_instrucoes_que_podem_escrever(sql: str) -> None:
    with pytest.raises(ReadOnlyViolation):
        validate_read_only_query(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT id_vendas FROM vendas",
        "WITH totais AS (SELECT COUNT(id_vendas) AS total FROM vendas) SELECT total FROM totais",
        "SELECT '-- DELETE FROM vendas' AS observacao",
    ],
)
def test_permite_consultas_de_leitura(sql: str) -> None:
    validate_read_only_query(sql)


@patch("src.database.create_engine")
def test_engine_configura_postgresql_como_somente_leitura(
    mocked_create_engine: MagicMock,
) -> None:
    config = DatabaseConfig(
        host="db.example.invalid",
        port=5432,
        database="concessionarias",
        user="leitor",
        password="segredo",
    )
    create_database_engine(config)

    url = mocked_create_engine.call_args.args[0]
    options = mocked_create_engine.call_args.kwargs["connect_args"]["options"]

    assert url.drivername == "postgresql+psycopg2"
    assert url.password == "segredo"
    assert "default_transaction_read_only=on" in options
    assert "segredo" not in str(url)


def test_erro_de_conexao_nao_expoe_credenciais() -> None:
    engine = MagicMock()
    engine.connect.side_effect = OperationalError(
        "connect", {}, Exception("password=segredo-super-secreto")
    )

    with pytest.raises(DatabaseConnectionError) as error:
        check_connection(engine=engine)

    assert "segredo-super-secreto" not in str(error.value)
    assert "conectar ao banco" in str(error.value)
