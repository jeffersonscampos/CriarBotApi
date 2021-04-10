from flask import Flask, render_template, jsonify
from flask_cors import CORS, cross_origin
from flask_restful import Resource, reqparse
#from flask_jwt_extended import jwt_required
import pymongo
import dns # required for connecting to MongoDB with SRV
import os # necessario para verificacao de variavel de ambiente.
import logging
import json
import re
import unicodedata


import string
import nltk
from nltk import tokenize
nltk.download('punkt')
nltk.download('stopwords')
stopwords = nltk.corpus.stopwords.words('portuguese')
from nltk.cluster.util import cosine_distance

nltk.download('wordnet')
from nltk.stem import WordNetLemmatizer

# path /chatbot/question?code_user=xxxx&code_before=xxxxxx&input=xxxxxx
path_params = reqparse.RequestParser()
path_params.add_argument('code_user', type=int)
path_params.add_argument('code_relation', type=int)
path_params.add_argument('code_before', type=int)
path_params.add_argument('input', type=str)


class Chatbot(Resource):

    def get(self):

        #recupera os parametros da requisicao.
    	dados = path_params.parse_args()

    	MONGODB_URL = str(os.environ.get("MONGODB_URL", 'localhost'))

    	#conexão local padrão
    	#cliente = pymongo.MongoClient('mongodb+srv://localhost:27017/')
    	#cliente = pymongo.MongoClient('localhost', 27017)

    	if (MONGODB_URL == 'localhost'):
    		cliente = pymongo.MongoClient('localhost', 27017)
    	else:
    		cliente = pymongo.MongoClient(MONGODB_URL)

    	#banco chatbotsdb
    	db = cliente.chatbotsdb
    	#coleção chatbot
    	botQuestions = db.chatbot

    	#rgxFiltroInput = re.compile('.*' + dados['input'] + '.*', re.IGNORECASE)  # compile the regex

    	#busca a pergunta/resposata com base no input do usuário.
    	if(dados['code_relation']):
    		questionData = botQuestions.find({"code_user": dados['code_user'], "code_relation": dados['code_relation']})
    		logging.warning('code_relation: ' + json.dumps(dados['code_relation']))
    		if(questionData is None):
    			questionData = botQuestions.find({"code_user": dados['code_user'], "code_relation": 0})
    			logging.warning('Entrou aqui!')
    		else:
    			logging.warning('questionData is not None!')
    	else:
    		questionData = botQuestions.find({"code_user": dados['code_user'], "code_relation": 0})
    		logging.warning('Nao veio code_relation!')

    	#Filtrando através da question do usuário, aqui deve ser utilizado o SpaCy NLP:
    	#questionData = [item for item in questionData if dados['input'] in item['input']]

    	# modelo JSON: registro--> {campo1:'valor'; campo2:'valor'}.
    	lista = [{campo: registro[campo] for campo in registro if campo != '_id'} for registro in questionData]

    	lista = [{campo: str(registro[campo]) for campo in registro if campo != '_id'} for registro in lista]

    	#entrada = nlp(json.loads(json.dumps(removerAcentosECaracteresEspeciais(dados['input']))))
    	entrada = str(json.loads(json.dumps(preprocessamento(dados['input']))))

        #Filtrando pela similaridade
    	lista = filtrar_similaridade_cosseno_nltk(entrada, lista, 0.7)

    	#entrada_original = json.loads(json.dumps(preprocessamento(dados['input'])))
    	#entrada_tokenizada = tokenize.word_tokenize(entrada_original, language='portuguese')

    	for item in lista:
    		#item_comparar = nlp(json.loads(json.dumps(removerAcentosECaracteresEspeciais(item['input']))))
    		item_comparar = str(json.loads(json.dumps(preprocessamento(item['input']))))
    		#logging.warning("entrada: {} item: {} similaridade: {} %.".format(entrada, item_comparar, item_comparar.similarity(entrada)))
    		logging.warning("entrada: {} item: {} similaridade: {} %.".format(entrada, item_comparar, calcula_similaridade_cosseno_nltk(entrada, item_comparar)))

    	logging.warning('code_user: ' + json.dumps(dados['code_user']))
    	logging.warning('input: ' + json.loads(json.dumps(preprocessamento(dados['input']))))

    	# return bson.json_util.dumps(questionData)

    	#lista = [{item: data[item]} for item in lista if item.input.constains(dados['input'])  for data in lista]
    	#lista = [{item: data[item]} for item in lista if(dados['input'] in item.input)]

    	logging.warning('Retorno:')
    	logging.warning(json.loads(json.dumps(lista)))

    	if(questionData):
    		return json.loads(json.dumps(lista)), 200
    		# return json.dumps(questionData, default=json_util.default), 200 # Http Status Code 200 Sucesso.
    	else:
    		return None, 404 # Http Status Code 404 Não Encontrado.


def calcula_similaridade_cosseno_nltk(sentenca1, sentenca2):
	palavras1 = [palavra for palavra in nltk.word_tokenize(sentenca1)]
	palavras2 = [palavra for palavra in nltk.word_tokenize(sentenca2)]
	#print(palavras1)
	#print(palavras2)

	todas_palavras = list(set(palavras1 + palavras2))
	#print(todas_palavras)

	vetor1 = [0] * len(todas_palavras)
	vetor2 = [0] * len(todas_palavras)
	#print(vetor1)
	#print(vetor2)

	for palavra in palavras1:
		vetor1[todas_palavras.index(palavra)] += 1
	for palavra in palavras2:
		vetor2[todas_palavras.index(palavra)] += 1

	#print(vetor1)
	#print(vetor2)

	return 1 - cosine_distance(vetor1, vetor2)


def filtrar_similaridade_cosseno_nltk(entrada, lista, fatorSimilaridade):
    lista = [item for item in lista if calcula_similaridade_cosseno_nltk(str(json.loads(json.dumps(preprocessamento(item['input'])))), entrada) > fatorSimilaridade]
    return lista


def removerEspacosEmBranco(texto):
	texto_formatado = re.sub(r'\s+', ' ', texto)
	return texto_formatado


def removerAcentosECaracteresEspeciais(texto):
    # Tipos de Normalização NFD e NFKD
    # --> https://qastack.com.br/programming/7931204/what-is-normalized-utf-8-all-about
    # --> https://www.otaviomiranda.com.br/2020/normalizacao-unicode-em-python/
    # Unicode normalize transforma um caracter em seu equivalente em latin.
    # nfkd = unicodedata.normalize('NFKD', texto)
    texto = normalizarTexto(texto)

    textoSemAcento = u"".join([caracter for caracter in texto if not unicodedata.combining(caracter)])

    # remove punctuation tokens that are in the word string like 'bye!' -> 'bye'
    #REPLACE_PUNCT = re.compile("(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\()|(\))|(\[)|(\])")

    # Usa expressão regular para retornar a palavra apenas com números, letras e espaço
    #return re.sub('[^a-zA-Z0-9 \\\]', '', palavraSemAcento)
    textoSemAcento = re.sub("(\.)|(\;)|(\:)|(\!)|(\')|(\?)|(\,)|(\")|(\()|(\))|(\[)|(\])", '', textoSemAcento)

    textoSemAcento = removerStopWords(textoSemAcento)

    return textoSemAcento


def normalizarTexto(texto):
    # Tipos de Normalização NFD e NFKD
    # --> https://qastack.com.br/programming/7931204/what-is-normalized-utf-8-all-about
    # --> https://www.otaviomiranda.com.br/2020/normalizacao-unicode-em-python/
    # Unicode normalize transforma um caracter em seu equivalente em latin.
    # nfkd = unicodedata.normalize('NFKD', texto)

    texto = unicodedata.normalize('NFD', texto)

    texto = texto .lower()

    return texto


def lematizarTexto(texto):
    wordnet_lemmatizer = WordNetLemmatizer()
    pontuacao="?:!.,;"
    texto_palavras = nltk.word_tokenize(texto)
    for palavra in texto_palavras:
        if palavra in pontuacao:
            texto_palavras.remove(palavra)

    texto = u" ".join([str(wordnet_lemmatizer.lemmatize(palavra)) for palavra in texto_palavras])
    return texto


def removerStopWords(texto):
    texto = normalizarTexto(texto)
    palavras = [i for i in texto.split() if not i in stopwords]
    return (" ".join(palavras))


def preprocessamento(texto):
    texto_formatado	= texto.lower()

    texto_formatado = removerEspacosEmBranco(texto_formatado)

    texto_formatado = removerAcentosECaracteresEspeciais(texto_formatado)

    texto_formatado = normalizarTexto(texto_formatado)

    texto_formatado = lematizarTexto(texto_formatado)

    #TOKENIZACAO COM O NLTK:
    tokens = []
    for token in nltk.word_tokenize(texto_formatado):
      tokens.append(token)

    tokens = [palavra for palavra in tokens if palavra not in stopwords]

    tokens = [palavra for palavra in tokens if palavra not in string.punctuation]

    texto_formatado = ' '.join([str(elemento) for elemento in tokens if elemento is not elemento.isdigit()])

    return texto_formatado
