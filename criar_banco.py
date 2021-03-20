import sqlite3

conexao = sqlite3.connect('banco_hoteis.db')
cursor = conexao.cursor()

criar_tabela ="CREATE TABLE IF NOT EXISTS hoteis (hotel_id text PRIMARY KEY,\
 nome text, estrelas real, diaria real, cidade text)"

criar_hotel = "INSERT INTO hoteis VALUES ('hotel_teste', 'Hotel Teste', 4.3, 345.30, 'Rio de Janeiro')"

cursor.execute(criar_tabela)
cursor.execute(criar_hotel)

conexao.commit()
conexao.close()
