import os
import tempfile

from collections import OrderedDict

import pytest

from graphene.test import Client

from storeify import util
from storeify import db
from storeify import schema
from storeify.app import create_app
from storeify.config import Config

@pytest.fixture
def app_client():
    # db_path = tempfile.mkstemp()[1]
    db_path = "testdb.sqlite3"
    Config.DATABASE_URI = "sqlite:///"+db_path
    app = create_app()
    db.reset_db()
    db.create_db()
    db.init_db_engine()
    util.load_test_data('test/products.csv')
    yield app_client

def create_cart(client, currency="USD"):
    query = '''
        mutation{
            cartCreate(userid:1, currency:%s, cartItems:[]){
                ok
                cart{
                    id
                    userid
                    currency
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' % currency
    executed = client.execute(query)
    cartID = executed['data']['cartCreate']['cart']['id']
    return cartID, executed

def create_cart_item(client, productID, quantity=5):
    query = '''
        mutation{
            cartItemCreate(productID:"%s", quantity:%d){
                ok
                cartItem{
                    id
                }
            }
        }
        ''' % (productID, quantity)

    executed = client.execute(query)
    print(executed)
    cartItemID = executed['data']['cartItemCreate']['cartItem']['id']
    return cartItemID, executed

def add_item_to_cart(client, cartID, cartItemID):
    query = '''
        mutation{
            cartAddItems(cartID:"%s", cartItems:["%s"]){
                ok
                cart{
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' % (cartID, cartItemID)
    executed = client.execute(query)
    return cartID, executed

def test_retreive_all_products_all_data(app_client):
    client = Client(schema.schema)
    query = '''
        query{
            products {
                title
                price
                currency
                canPurchase
                inventoryCount
            }
        }
        '''
    executed = client.execute(query)
    assert executed == {'data': 
        OrderedDict([
            ('products',[
                OrderedDict([('title', 'Cat Food'), ('price', 500), ('currency', 'USD'), ('canPurchase', True), ('inventoryCount', 250)]), 
                OrderedDict([('title', 'Potatoes'), ('price', 10), ('currency', 'CAD'), ('canPurchase', False), ('inventoryCount', 10)]), 
                OrderedDict([('title', 'Whiteboard'), ('price', 10000), ('currency', 'EUR'), ('canPurchase', True), ('inventoryCount', 10)]), 
                OrderedDict([('title', 'Lightbulb'), ('price', 1000), ('currency', 'USD'), ('canPurchase', True), ('inventoryCount', 0)]), 
                OrderedDict([('title', 'Glasses'), ('price', 80000), ('currency', 'USD'), ('canPurchase', True), ('inventoryCount', 1)])])
        ])
    } 

def test_retreive_product_by_id(app_client):
    # Get first product from list of all products, then get it again
    # by ID, checking if they are equal
    client = Client(schema.schema)
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    id = executed['data']['products'][0]['id']
    title = executed['data']['products'][0]['title']

    query = '''
        query{
            product(id:"%s"){
                title
            }
        }
        ''' % id

    executed = client.execute(query)
    assert executed['data']['product']['title'] == title

def test_create_new_product_valid(app_client):
    client = Client(schema.schema)

    # Test the creation method
    query = '''
        mutation {
            productCreate(title:"Energy Drink",
                          price:700,
                          currency:CAD,
                          inventoryCount:500,
                          canPurchase:true){
                product {
                    title
                    price
                    currency
                    inventoryCount
                    canPurchase
                }
            }
        }
        '''
    executed = client.execute(query)
    assert executed == {
        "data": {
            "productCreate": {
                "product": {
                    "title": "Energy Drink",
                    "price": 700,
                    "currency": "1",
                    "inventoryCount": 500,
                    "canPurchase": True
                }
            }
        }
    }

    # Verify the product is in the DB
    query = '''
        query{
            products(title:"Energy Drink"){
                title
                price
                currency
                inventoryCount
                canPurchase
            }
        }
        '''
    executed = client.execute(query)
    assert executed =={
        "data": {
            "products": [
            {
                "title": "Energy Drink",
                "price": 700,
                "currency": "1",
                "inventoryCount": 500,
                "canPurchase": True
            }
            ]
        }
    }

def test_create_new_product_invalid(app_client):    
    client = Client(schema.schema)
    query = '''
        mutation {
            productCreate(title: "Coffee", 
                          price: potato, 
                          currency: USD, 
                          inventoryCount: 500, 
                          canPurchase: true) {
                product {
                    id
                }
            }
        }
        '''
    executed = client.execute(query)
    assert executed == {
        "errors": [
            {
            "locations": [
                {
                "column": 34,
                "line": 4
                }
            ],
            "message": "Argument \"price\" has invalid value potato.\nExpected type \"Int\", found potato."
            }
        ]
    }

def test_update_product(app_client):
    client = Client(schema.schema)

    # Pull the first product, update the title, then check that it has been
    # updated successfully
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    id = executed['data']['products'][0]['id']

    query = '''
        mutation{
            productUpdate(id:"%s", title:"%s"){
                product{
                    title
                }
            }
        }
        ''' % (id, "Water Bottle")

    executed = client.execute(query)
    print(executed)
    assert executed['data']['productUpdate']['product']['title'] == "Water Bottle"

def test_delete_product(app_client):
    client = Client(schema.schema)
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    print(executed)
    id = executed['data']['products'][0]['id']
    title = executed['data']['products'][0]['title']
    print(id, title)

    # Check if returned product from delete is correct
    query = '''
        mutation{
            productDelete(id:"%s"){
                ok
                product{
                    title
                }
            }
        }
        ''' % id

    executed = client.execute(query)
    print(executed)
    assert executed['data']['productDelete']['product']['title'] == title
    assert executed['data']['productDelete']['ok'] == True

    # Check if product has been removed
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    print(executed)
    for product in executed['data']['products']:
        assert product['id'] != id

def test_create_cart_item(app_client):
    # Get cart item
    client = Client(schema.schema)
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    productID = executed['data']['products'][0]['id']
    productTitle = executed['data']['products'][0]['title']

    print(productID)

    query = '''
        mutation{
            cartItemCreate(productID:"%s", quantity:5){
                ok
                cartItem{
                    id
                    product{
                        id
                        title
                    }
                    quantity
                }
            }
        }
        ''' % productID

    executed = client.execute(query)
    print(executed)
    assert executed['data']['cartItemCreate']['ok'] == True
    assert executed['data']['cartItemCreate']['cartItem']['product']['id'] == productID
    assert executed['data']['cartItemCreate']['cartItem']['product']['title'] == productTitle
    assert executed['data']['cartItemCreate']['cartItem']['quantity'] == 5

def test_update_cart_item(app_client):
    client = Client(schema.schema)
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    productID = executed['data']['products'][0]['id']
    productTitle = executed['data']['products'][0]['title']

    print(productID)

    query = '''
        mutation{
            cartItemCreate(productID:"%s", quantity:5){
                ok
                cartItem{
                    id
                }
            }
        }
        ''' % productID

    executed = client.execute(query)
    cartItemID = executed['data']['cartItemCreate']['cartItem']['id']

    query = '''
        mutation{
            cartItemUpdate(id:"%s", quantity:6){
                ok
                cartItem{
                    id
                    quantity
                }
            }
        }
        ''' % cartItemID 

    executed = client.execute(query)
    print(executed)
    assert executed['data']['cartItemUpdate']['cartItem']['quantity'] == 6

def test_create_new_cart_valid(app_client):
    client = Client(schema.schema)
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    productID = executed['data']['products'][0]['id']

    query = '''
        mutation{
            cartItemCreate(productID:"%s", quantity:5){
                ok
                cartItem{
                    id
                }
            }
        }
        ''' % productID

    executed = client.execute(query)
    cartItemID = executed['data']['cartItemCreate']['cartItem']['id']

    query = '''
        mutation{
            cartCreate(userid:1, currency:USD, cartItems:["%s"]){
                ok
                cart{
                    id
                    userid
                    currency
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' % cartItemID

    executed = client.execute(query)
    print(executed)
    assert executed['data']['cartCreate']['ok'] == True
    assert executed['data']['cartCreate']['cart']['userid'] == 1
    assert executed['data']['cartCreate']['cart']['currency'] == 'USD'

def test_delete_cart(app_client):
    client = Client(schema.schema)
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    productID = executed['data']['products'][0]['id']

    query = '''
        mutation{
            cartItemCreate(productID:"%s", quantity:5){
                ok
                cartItem{
                    id
                }
            }
        }
        ''' % productID

    executed = client.execute(query)
    cartItemID = executed['data']['cartItemCreate']['cartItem']['id']

    query = '''
        mutation{
            cartCreate(userid:1, currency:USD, cartItems:"[%s]"){
                ok
                cart{
                    id
                    userid
                    currency
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' % cartItemID

    executed = client.execute(query)
    cartID = executed['data']['cartCreate']['cart']['id']

    query = '''
        mutation{
            cartDelete(id:"%s"){
                ok
                cart{
                    id
                }
            }
        }
        ''' % cartID

    executed = client.execute(query)
    assert executed['data']['cartDelete']['ok'] == True
    assert executed['data']['cartDelete']['cart']['id'] == cartID

def test_retreive_all_user_carts(app_client):
    client = Client(schema.schema)
    query = '''
        mutation{
            cartCreate(userid:1, currency:USD, cartItems:[]){
                ok
                cart{
                    id
                    userid
                    currency
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' 
    ids = []
    for i in range(0,3):
        executed = client.execute(query)
        print(executed)
        ids.append(executed['data']['cartCreate']['cart']['id'])

    query = '''
        query{
            carts(userid:1){
                id
            }
        }
        ''' 
    
    executed = client.execute(query)
    print(executed)
    for i in range(0,3):
        assert executed['data']['carts'][i]['id'] in ids

def test_retreive_cart(app_client):
    client = Client(schema.schema)
    query = '''
        mutation{
            cartCreate(userid:1, currency:USD, cartItems:[]){
                ok
                cart{
                    id
                    userid
                    currency
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' 
    
    executed = client.execute(query)
    id = executed['data']['cartCreate']['cart']['id']

    query = '''
        query{
            cart(id:"%s"){
                id
                userid
            }
        }
        ''' % id

    executed = client.execute(query)
    assert executed['data']['cart']['id'] == id

def test_add_item_to_cart_valid(app_client):
    client = Client(schema.schema)
    query = '''
        query{
            products {
                id
                title
            }
        }
        '''
    executed = client.execute(query)
    productID0 = executed['data']['products'][0]['id']
    productID1 = executed['data']['products'][2]['id']

    query = '''
        mutation{
            cartItemCreate(productID:"%s", quantity:5){
                ok
                cartItem{
                    id
                }
            }
        }
        ''' % productID0

    cartItemList = []
    executed = client.execute(query)
    cartItemList.append(executed['data']['cartItemCreate']['cartItem']['id'])

    query = '''
        mutation{
            cartItemCreate(productID:"%s", quantity:5){
                ok
                cartItem{
                    id
                }
            }
        }
        ''' % productID1

    executed = client.execute(query)
    cartItemList.append(executed['data']['cartItemCreate']['cartItem']['id'])

    query = '''
        mutation{
            cartCreate(userid:1, currency:USD, cartItems:[]){
                ok
                cart{
                    id
                    userid
                    currency
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' 

    executed = client.execute(query)
    print(executed)
    cartID = executed['data']['cartCreate']['cart']['id']

    query = '''
        mutation{
            cartAddItems(cartID:"%s", cartItems:["%s", "%s"]){
                ok
                cart{
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' % (cartID, cartItemList[0], cartItemList[1])

    print(client.execute(query))

    query = '''
        query{
            cart(id:"%s"){
                cartItems{
                    id
                }
            }
        }
        ''' % cartID

    executed = client.execute(query)
    print(executed)
    assert len(executed['data']['cart']['cartItems']) == 2
    for cartItem in executed['data']['cart']['cartItems']:
        assert cartItem['id'] in cartItemList

def test_add_item_to_cart_invalid(app_client):
    # Test if item is out of stock
    client = Client(schema.schema)
    query = '''
        query{
            products(title:"Lightbulb") {
                id
            }
        }
        '''
    executed = client.execute(query)
    outOfStockID = executed['data']['products'][0]['id']

    outOfStockCartItemID = create_cart_item(client, outOfStockID)[0]
    cartID = create_cart(client)[0]
    executed = add_item_to_cart(client, cartID, outOfStockCartItemID)[1]

    print(executed)
    assert executed['errors'][0]['message'] == 'CartItem "%s" is out of stock.' % outOfStockCartItemID

    # Test if requested amount is greater than stock
    query = '''
        query{
            products(title:"Glasses") {
                id
            }
        }
        '''
    executed = client.execute(query)
    underStockItemID = executed['data']['products'][0]['id']

    underStockCartItemID = create_cart_item(client, underStockItemID, 100)[0]
    executed = add_item_to_cart(client, cartID, underStockCartItemID)[1]

    print(executed)
    assert executed['errors'][0]['message'] == 'CartItem "%s" has only 1 units left.' %underStockCartItemID

    # Test if item purchase is disabled
    query = '''
        query{
            products(title:"Potatoes") {
                id
            }
        }
        '''
    executed = client.execute(query)
    disabledItemID = executed['data']['products'][0]['id']

    disabledCartItemID = create_cart_item(client, disabledItemID, 100)[0]
    executed = add_item_to_cart(client, cartID, disabledCartItemID)[1]

    print(executed)
    assert executed['errors'][0]['message'] == 'CartItem "%s" cannot be purchased.' %disabledCartItemID

    # Test if item code is invalid
    executed = add_item_to_cart(client, cartID, "L2FydDol")[1]
    assert executed['errors'][0]['message'] == 'CartItem "L2FydDol" does not exist.'

def test_remove_item_from_cart(app_client):
    client = Client(schema.schema)
    cartID = create_cart(client)[0]
    query = '''
        query{
            products(title:"Glasses") {
                id
            }
        }
        '''
    executed = client.execute(query)
    itemID = executed['data']['products'][0]['id']

    cartItemID = create_cart_item(client, itemID, 1)[0]
    executed = add_item_to_cart(client, cartID, cartItemID)[1]
    assert executed['data']['cartAddItems']['ok'] == True

    query = '''
        mutation{
            cartRemoveItems(cartID:"%s", cartItems:["%s"]){
                cart{
                    cartItems{
                        id
                    }
                }
            }
        }
        ''' % (cartID, cartItemID)

    executed = client.execute(query)
    print(executed)
    assert len(executed['data']['cartRemoveItems']['cart']['cartItems']) == 0

def test_get_cart_price(app_client):
    client = Client(schema.schema)
    cartID = create_cart(client, "CAD")[0]
    query = '''
        query{
            products(title:"Whiteboard") {
                id
            }
        }
        '''
    executed = client.execute(query)
    itemID = executed['data']['products'][0]['id']
    cartItemID = create_cart_item(client, itemID, 5)[0]
    executed = add_item_to_cart(client, cartID, cartItemID)[1]
    assert executed['data']['cartAddItems']['ok'] == True

    query = '''
        query{
            products(title:"Glasses") {
                id
            }
        }
        '''
    executed = client.execute(query)
    itemID = executed['data']['products'][0]['id']
    cartItemID = create_cart_item(client, itemID, 1)[0]
    executed = add_item_to_cart(client, cartID, cartItemID)[1]
    assert executed['data']['cartAddItems']['ok'] == True

    query = '''
        query{
            cart(id:"%s"){
                id
                total
            }
        }
        ''' % cartID
    executed = client.execute(query)
    print(executed)
    assert executed['data']['cart']['total'] == 93000

def test_purchase_cart_with_items(app_client):
    client = Client(schema.schema)
    cartID = create_cart(client, "CAD")[0]
    query = '''
        query{
            products(title:"Whiteboard") {
                id
            }
        }
        '''
    executed = client.execute(query)
    itemID = executed['data']['products'][0]['id']
    cartItemID = create_cart_item(client, itemID, 5)[0]
    executed = add_item_to_cart(client, cartID, cartItemID)[1]
    assert executed['data']['cartAddItems']['ok'] == True

    query = '''
        query{
            products(title:"Glasses") {
                id
            }
        }
        '''
    executed = client.execute(query)
    itemID = executed['data']['products'][0]['id']
    cartItemID = create_cart_item(client, itemID, 1)[0]
    executed = add_item_to_cart(client, cartID, cartItemID)[1]
    assert executed['data']['cartAddItems']['ok'] == True

    query = '''
        mutation{
            cartPurchase(cartID:"%s"){
                ok
                cart{
                    id
                }
            }
        }
        ''' % cartID
    executed = client.execute(query)
    print(executed)
    assert executed['data']['cartPurchase']['ok'] == True

    query = '''
        query{
            products(title:"Whiteboard") {
                inventoryCount
            }
        }
        '''
    executed = client.execute(query)
    print(executed)
    assert executed['data']['products'][0]['inventoryCount'] == 5

    query = '''
        query{
            products(title:"Glasses") {
                inventoryCount
            }
        }
        '''
    executed = client.execute(query)
    assert executed['data']['products'][0]['inventoryCount'] == 0

def test_purchase_empty_cart(app_client):
    client = Client(schema.schema)
    cartID = create_cart(client)[0]
    query = '''
        mutation{
            cartPurchase(cartID:"%s"){
                ok
                cart{
                    id
                }
            }
        }
        ''' % cartID
    executed = client.execute(query)
    print(executed)
    assert executed['errors'][0]['message'] == 'Cart cannot be purchased. It is empty.'