from flask import Flask, jsonify
from flask_restful import Api
from resources.chatbot import Chatbot
from resources.hotel import Hotel, Hoteis
from resources.usuario import User, UserRegister, UserLogin, UserLogout
from flask_jwt_extended import JWTManager
from blacklist import BLACKLIST
from flask_cors import CORS, cross_origin

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banco_hoteis.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = '@J3fferson'
app.config['JWT_BLACKLIST_ENABLED'] = True
api = Api(app)
jwt = JWTManager(app)

cors = CORS(app)

@app.before_first_request
def criar_banco():
    banco.create_all()


@jwt.token_in_blacklist_loader
def verificar_backlist(token):
    return token['jti'] in BLACKLIST


@jwt.revoked_token_loader
def verificar_token_invalidado():
    return jsonify({'message': 'Logout do Usuário já realizado'}), 401 # Http Status Code 401 Unauthorized.


# @app.route("/chatbot/question")
# def chatbot():
#     return Chatbot.get()

@app.route("/")
def index():
    return "<h1><strong>Flask - REST Api<strong></h1><br/><br/> <h2><a href='/hoteis'>Listar Hoteis</a></h2>"

api.add_resource(Hoteis, '/hoteis')
api.add_resource(Hotel, '/hoteis/<string:hotel_id>')
api.add_resource(User, '/usuarios/<int:user_id>')
api.add_resource(UserRegister, '/cadastro')
api.add_resource(UserLogin, '/login')
api.add_resource(UserLogout, '/logout')
api.add_resource(Chatbot, '/chatbot/question')


if __name__ == "__main__":
    from sql_alchemy import banco
    banco.init_app(app)
    app.run(debug=True)
