from flask_restful import Api
from flask import Flask, render_template, jsonify
#--> from posts import posts
from flask_cors import CORS, cross_origin
from resources.chatbot import Chatbot


app = Flask(__name__)

api = Api(app)

cors = CORS(app)

#--> @app.route('/')
#--> def home():
#--> 	return render_template('home.html', posts=posts)


api.add_resource(Chatbot, '/chatbot/question')


if __name__ == '__main__':
	app.run(debug=True)
