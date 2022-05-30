"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, send_from_directory
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from api.utils import APIException, generate_sitemap
from api.models import db, User
from api.routes import api
from api.admin import setup_admin
from api.commands import setup_commands

#JWT +++++++++++++++++++++++++++++++++++
import datetime #ayuda a trabajar con fecha/hora MODULO NATIVO DE PYTHON
from flask_jwt_extended import JWTManager, create_access_token,jwt_required,get_jwt_identity
#+++++++++++++++++++++++++++++++++++++++
#from models import Person

ENV = os.getenv("FLASK_ENV")
static_file_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../public/')
app = Flask(__name__)
app.url_map.strict_slashes = False

# database condiguration
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db, compare_type = True)
db.init_app(app)

# Allow CORS requests to this API
CORS(app)

# add the admin
setup_admin(app)

# add the admin
setup_commands(app)

#importar JWT +++++++++++++++++++
jwt = JWTManager(app)
#++++++++++++++++++++++++++++++++

# Add all endpoints form the API with a "api" prefix
app.register_blueprint(api, url_prefix='/api')

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    if ENV == "development":
        return generate_sitemap(app)
    return send_from_directory(static_file_dir, 'index.html')

#jwt +++++++++++++++++++++++++++++++++++
@app.route('/login', methods =['POST'])
def iniciar_sesion():
    request_body = request.get_json()
    print(request_body)
    #De la tabla user seleccionamos los que coincidan con el email facilitado
    user = User.query.filter_by(email = request_body['email']).first()
    if user:
        if user.password == request_body['password']:
            #Una vez comprobado que usuario existe y la password coinbcide empezamos con JWT
            #en tiempo almacenamos el tiempo valido del token
            tiempo = datetime.timedelta(seconds = 660)
            #CREAMOS EL TOKEN DE ACCESO
            #El primer argumento es quien soy (identidad y por cuanto tiempo con permisos)
            acceso = create_access_token(identity = request_body['email'], expires_delta = tiempo)
            #DEVOLVEMOS LOS DATOS PARA TESTEAR
            return jsonify({
                "mensaje": "INICIO DE SESION CORRECTO",
                "duracion" : tiempo.total_seconds(),
                "token": acceso
            })


        return "todo ok", 200
    else:
        return "usuario no existe", 400
#++++++++++++++++++++++++++++++++++++++


@app.route('/signup', methods=['GET'])
def signup():
    request_body = request.get_json()
    user = User.query.filter_by(email = request_body['email'])
    password = User.query.filter_by(password = request_body['password'])
    





# SOLO ACCEDERAN LOS USUARIOS IDENBTIFICADOS
#TIPO DE TOKEN BEARER TOKEN
@app.route('/privada', methods =['GET'])
@jwt_required()
def privada(): 
    #Averiguamos de quien es el token con el metodo get_jwt_identity
    identidad = get_jwt_identity()
    return jsonify({"acceso": "concedido, Bienvenida ," + identidad})

#***************************************************************


# any other endpoint will try to serve it like a static file
@app.route('/<path:path>', methods=['GET'])
def serve_any_other_file(path):
    if not os.path.isfile(os.path.join(static_file_dir, path)):
        path = 'index.html'
    response = send_from_directory(static_file_dir, path)
    response.cache_control.max_age = 0 # avoid cache memory
    return response


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3001))
    app.run(host='0.0.0.0', port=PORT, debug=True)
