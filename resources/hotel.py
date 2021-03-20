from flask_restful import Resource, reqparse
from models.hotel import HotelModel
from flask_jwt_extended import jwt_required
import sqlite3

def normalizar_parametros_path(cidade=None,
                                estrelas_min = 0,
                                estrelas_max = 5,
                                diaria_min = 0,
                                diaria_max = 10000,
                                limit = 50,
                                offset = 0, **dados):
    if cidade:
        return {
            'estrelas_min': estrelas_min,
            'estrelas_max': estrelas_max,
            'diaria_min': diaria_min,
            'diaria_max': diaria_max,
            'cidade': cidade,
            'limit': limit,
            'offset': offset
        }
    return {
        'estrelas_min': estrelas_min,
        'estrelas_max': estrelas_max,
        'diaria_min': diaria_min,
        'diaria_max': diaria_max,
        'limit': limit,
        'offset': offset
    }

# path /hoteis?cidade=Rio de Janeiro&estrelas_min=4&diaria_max=400
path_params = reqparse.RequestParser()
path_params.add_argument('cidade', type=str)
path_params.add_argument('estrelas_min', type=float)
path_params.add_argument('estrelas_max', type=float)
path_params.add_argument('diaria_min', type=float)
path_params.add_argument('diaria_max', type=float)
path_params.add_argument('limit', type=float)
path_params.add_argument('offset', type=float)

class Hoteis(Resource):
    def get(self):
        conexao = sqlite3.connect('banco_hoteis.db')
        cursor = conexao.cursor()

        dados = path_params.parse_args()
        dados_validos = {chave:dados[chave] for chave in dados if dados[chave] is not None}
        parametros = normalizar_parametros_path(**dados_validos)

        if not parametros.get('cidade'):
            consulta = "SELECT * FROM hotel_model \
            WHERE (estrelas >= ? and estrelas <= ?) \
            AND (diaria >= ? and diaria <= ?) \
            LIMIT ? OFFSET ?"

            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta, tupla)
        else:
            consulta = "SELECT * FROM hotel_model \
            WHERE (estrelas >= ? and estrelas <= ?) \
            AND (diaria >= ? and diaria <= ?) \
            AND cidade = ? LIMIT ? OFFSET ?"

            tupla = tuple([parametros[chave] for chave in parametros])
            resultado = cursor.execute(consulta, tupla)

        hoteis_lista = []
        for linha in resultado:
            hoteis_lista.append({
                'hotel_id': linha[0],
                'nome': linha[1],
                'estrelas': linha[2],
                'diaria': linha[3],
                'cidade': linha[4]
            })

        #return {'hoteis': [ hotel.json() for hotel in HotelModel.query.all()]}, 200 # Http Status Code 200 Sucesso.
        return {'hoteis': hoteis_lista}, 200 # Http Status Code 200 Sucesso.


class Hotel(Resource):
    argumentos = reqparse.RequestParser()
    argumentos.add_argument('nome', type=str, required=True, help="O campo 'nome' é obrigatório!")
    argumentos.add_argument('estrelas', type=float, required=True, help="O campo 'estrelas' é obrigatório!")
    argumentos.add_argument('diaria', type=float, required=True, help="O campo 'diaria' é obrigatório!")
    argumentos.add_argument('cidade', type=str, required=True, help="O campo 'cidade' é obrigatório!")


    def get(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            return hotel.json()
        return {'message': 'Hotel not found.'}, 404 # not found.

    @jwt_required
    def post(self, hotel_id):
        if HotelModel.find_hotel(hotel_id):
            return {"message": "Hotel id '{}' já existe!".format(hotel_id)}, 400 #Http Status Code 400 Bad Request.

        dados = Hotel.argumentos.parse_args()
        #novo_hotel = { 'hotel_id': hotel_id, **dados }
        hotel = HotelModel(hotel_id, **dados)
        # novo_hotel = hotel.json() # transformando em JSON.
        # hoteis.append(novo_hotel) # adicionando na lista em memória.
        #return novo_hotel, 200  # HTTP Status Code 200: Sucesso!
        try:
            hotel.save_hotel() # salvando no banco de dados.
        except:
            return {'message': 'Ocorreu um erro ao tentar salvar o hotel'}, 500 # Http Status Code 500 Erro Interno de Servidor.
        return hotel.json(), 200  # HTTP Status Code 200: Sucesso!

    @jwt_required
    def put(self, hotel_id):

        dados = Hotel.argumentos.parse_args()
        hotel_encontrado = HotelModel.find_hotel(hotel_id)
        if hotel_encontrado:
            hotel_encontrado.update_hotel(**dados)
            return hotel_encontrado.json(), 200 # Http Status 200, ok encotrado com Sucesso.
        hotel_novo = HotelModel(hotel_id, **dados)
        try:
            hotel.save_hotel() # salvando no banco de dados.
        except:
            return {'message': 'Ocorreu um erro ao tentar salvar o hotel'}, 500 # Http Status Code 500 Erro Interno de Servidor.
        return hotel_novo.json(), 201 # Http Status 201, ok Criado com Sucesso.

    @jwt_required
    def delete(self, hotel_id):
        hotel = HotelModel.find_hotel(hotel_id)
        if hotel:
            try:
                hotel.delete_hotel()
            except:
                return {'message': 'Ocorreu um erro ao tentar excluir o hotel'}, 500 # Http Status Code 500 Erro Interno de Servidor.
            return {'message': 'Hotel excluído com Sucesso.'}, 200 # Https Status Code 200 Operação Realizada com Sucesso.
        return {'message': 'Hotel não existe!'}, 400 # Http Status Code 400 Not Found
