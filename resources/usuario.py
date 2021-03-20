from flask_restful import Resource, reqparse
from models.usuario import UserModel
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt
from werkzeug.security import safe_str_cmp
from blacklist import BLACKLIST


class User(Resource):
    # /usuarios/{user_id}
    def get(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            return user.json()
        return {'message': 'Usuário não encontrado!'}, 404 # not found.

    @jwt_required
    def delete(self, user_id):
        user = UserModel.find_user(user_id)
        if user:
            try:
                user.delete_user()
            except:
                return {'message': 'Ocorreu um erro ao tentar excluir o usuário!'}, 500 # Http Status Code 500 Erro Interno de Servidor.
            return {'message': 'Usuário excluído com Sucesso!'}, 200 # Https Status Code 200 Operação Realizada com Sucesso.
        return {'message': 'Usuário não existe!'}, 400 # Http Status Code 400 Not Found


class UserRegister(Resource):
    # /cadastro
    def post(self):
        parametros = reqparse.RequestParser()
        parametros.add_argument('login', type=str, required=True, help="O campo 'Login' é obrigratório!")
        parametros.add_argument('senha', type=str, required=True, help="O campo 'Senha' é obrigratório!")

        dados = parametros.parse_args()

        if UserModel.find_by_login(dados['login']):
            return {'message': "O Login '{}' já existe!".format(dados['login'])}

        user = UserModel(**dados)
        user.save_user()
        return {'message': 'Usuário criado com sucesso!'}, 201 # Http Status Code 201 Created.


class UserLogin(Resource):

    @classmethod
    def post(cls):
        parametros = reqparse.RequestParser()
        parametros.add_argument('login', type=str, required=True, help="O campo 'Login' é obrigratório!")
        parametros.add_argument('senha', type=str, required=True, help="O campo 'Senha' é obrigratório!")

        dados = parametros.parse_args()

        user = UserModel.find_by_login(dados['login'])

        if(user and safe_str_cmp(user.senha, dados['senha'])):
            # Documentacao Flask JWT Extended: https://flask-jwt-extended.readthedocs.io/en/stable/tokens_from_complex_object/
            token_de_acesso = create_access_token(identity=user.user_id)
            return {'access_token': token_de_acesso}, 200 # Http Status Code 200 Sucesso.
            return {'access_token': 'acesso_fake_ok'}, 200 # Http Status Code 200 Sucesso.
        return {'message': 'Usuário ou Senha incorretos!'}, 401 #Http Status Code 401 Unauthorized.


class UserLogout(Resource):

     @jwt_required
     def post(self):
         jwt_id = get_raw_jwt()['jti'] #JWT Token Identifier
         BLACKLIST.add(jwt_id)
         return {'message': 'Logout executado com sucesso!'}
