#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response, jsonify
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"

@app.route("/restaurants" ,methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    restaurant_list = []
    for restaurant in restaurants:
        restaurant_list.append({
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
        })
    print(restaurants)
    return jsonify(restaurant_list),200

@app.route('/restaurants/<int:id>', methods=['GET'])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    return jsonify(restaurant.to_dict(rules=('id', 'name', 'address', 'restaurant_pizzas.id', 'restaurant_pizzas.price', 'restaurant_pizzas.pizza.id', 'restaurant_pizzas.pizza.name', 'restaurant_pizzas.pizza.ingredients'))), 200

@app.route("/restaurants/<int:id>" ,methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404
    db.session.query(RestaurantPizza).filter(RestaurantPizza.restaurant_id == id).delete()
    db.session.delete(restaurant)
    db.session.commit()
    return '', 204

@app.route("/pizzas" ,methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    pizza_list = []
    for pizza in pizzas:
        pizza_list.append({
            "id": pizza.id,
            "name": pizza.name,
            "ingredients": pizza.ingredients
        })
    print(pizza_list)
    return jsonify(pizza_list),200

@app.route("/restaurant_pizzas" ,methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()

    # Validate input data
    if not data or not all(key in data for key in ('price', 'pizza_id', 'restaurant_id')):
        return jsonify({"errors": ["Missing required fields"]}), 400

    try:
        price = int(data.get('price'))
    except ValueError:
        return jsonify({"errors": ["validation errors"]}), 400

    pizza_id = data.get('pizza_id')
    restaurant_id = data.get('restaurant_id')

    pizza = Pizza.query.get(pizza_id)
    restaurant = Restaurant.query.get(restaurant_id)

    if not pizza or not restaurant:
        return jsonify({"errors": ["Pizza or Restaurant not found"]}), 404

    try:
        new_restaurant_pizza = RestaurantPizza(price=price, pizza_id=pizza_id, restaurant_id=restaurant_id)
        db.session.add(new_restaurant_pizza)
        db.session.commit()
    except ValueError as e:
        db.session.rollback()
        return jsonify({"errors": ["validation errors"]}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"errors": ["Failed to create RestaurantPizza"]}), 400

    response_data = {
        "id": new_restaurant_pizza.id,
        "pizza": {
            "id": pizza.id,
            "ingredients": pizza.ingredients,
            "name": pizza.name
        },
        "pizza_id": new_restaurant_pizza.pizza_id,
        "price": new_restaurant_pizza.price,
        "restaurant": {
            "address": restaurant.address,
            "id": restaurant.id,
            "name": restaurant.name
        },
        "restaurant_id": new_restaurant_pizza.restaurant_id
    }

    return jsonify(response_data), 201

if __name__ == "__main__":
    app.run(port=5555, debug=True)
