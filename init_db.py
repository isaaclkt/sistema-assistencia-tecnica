import sqlite3
import os

os.makedirs("database", exist_ok=True)

conexao = sqlite3.connect("database/sistema.db")
conexao.execute("PRAGMA foreign_keys = ON")

with open("database/schema.sql", "r", encoding="utf-8") as arquivo:
    conexao.executescript(arquivo.read())

conexao.commit()
conexao.close()

print("Banco criado com sucesso!")