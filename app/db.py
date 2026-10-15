"""Conexao compartilhada para o futuro algoritmo de alocacao."""
import os

import pymysql


def connect():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3308")),
        user=os.getenv("DB_USER", "alocacao"),
        password=os.environ["DB_PASSWORD"],
        database=os.getenv("DB_NAME", "alocacao"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=10,
    )
