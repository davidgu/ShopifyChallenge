# Storeify by David Gu: Shopify 2019 Developer Intern Challenge

## **Extra Credit & Extra Extra Credit**
* Ergonomic Shopping Cart Flow :heavy_check_mark:
* Clear Documentation :heavy_check_mark:
* Extensive Unit Tests :heavy_check_mark:
* Idiomatic GraphQL API :heavy_check_mark:

## **Other Features**
* Multiple currency support! Create products priced in USD, CAD or EUR and have them automatically converted into a target currency when added to a shopping cart.
* Product canPurchase flag! Allow merchants to enable and disable products for purchase, independent of inventory count.
* Informative error messages! Identifies the offending object causing queries to fail.


## **Installation and Setup**
```bash
# Install the python dependencies. Python3 is required!
$ pip3 install -r requirements.txt

# Export the required environment variables
$ export LC_ALL=C.UTF-8
$ export LANG=C.UTF-8

# Run the tests
$ pytest

# Enter the project directory, and start the flask shell
$ cd storeify/
$ flask shell

# Initialize the database for first use, and load some test data
>>> from storeify.db import create_db
>>> from storeify.util import load_test_data
>>> create_db()
>>> load_test_data('../test/products.csv')
>>> exit()

# Start the local development server
$ flask run
```
Now open `localhost:5000/graphql` in your browser to enter GraphiQL where you can interact with the API


## **Getting Started**
This is a demonstration of a basic order flow, creating a cart, adding products, then purchasing the cart.
```graphql
# Get a list of all products
query{
  products{
    id
    title
    currency
    price
    inventoryCount
    canPurchase
  }
}
```
```javascript
{
  "data": {
    "products": [
      {
        "id": "UHJvZHVjdDox",
        "title": "Cat Food",
        "currency": "USD",
        "price": 500,
        "inventoryCount": 250,
        "canPurchase": true
      },
      {
        "id": "UHJvZHVjdDoy",
        "title": "Potatoes",
        "currency": "CAD",
        "price": 10,
        "inventoryCount": 10,
        "canPurchase": false
      },
      ...
      {
        "id": "UHJvZHVjdDo1",
        "title": "Glasses",
        "currency": "USD",
        "price": 80000,
        "inventoryCount": 1,
        "canPurchase": true
      }
    ]
  }
}
```
```graphql
# Alternatively, to only get products with available inventory
query{
  products(inventoryMinimum:1){
    id
    title
    currency
    price
    inventoryCount
    canPurchase
  }
}
```
```javascript
{
  "data": {
    "products": [
      {
        "id": "UHJvZHVjdDox",
        "title": "Cat Food",
        "currency": "USD",
        "price": 500,
        "inventoryCount": 250,
        "canPurchase": true
      },
      {
        "id": "UHJvZHVjdDoy",
        "title": "Potatoes",
        "currency": "CAD",
        "price": 10,
        "inventoryCount": 10,
        "canPurchase": false
      },
      {
        "id": "UHJvZHVjdDoz",
        "title": "Whiteboard",
        "currency": "EUR",
        "price": 10000,
        "inventoryCount": 10,
        "canPurchase": true
      },
      {
        "id": "UHJvZHVjdDo1",
        "title": "Glasses",
        "currency": "USD",
        "price": 80000,
        "inventoryCount": 1,
        "canPurchase": true
      }
    ]
  }
}
```
```graphql
# Create cartItems, which specify the product and quantity
mutation{
  cartItemCreate(productID:"UHJvZHVjdDox", quantity:1){
    cartItem{
      id
    }
  }
}

mutation{
  cartItemCreate(productID:"UHJvZHVjdDol", quantity:1){
    cartItem{
      id
    }
  }
}

# These cartItems can later be edited, with a different product or quantity with the cartItemUpdate mutation
```
```javascript
{
  "data": {
    "cartItemCreate": {
      "cartItem": {
        "id": "Q2FydEl0ZW06NQ=="
      }
    }
  }
}

{
  "data": {
    "cartItemCreate": {
      "cartItem": {
        "id": "Q2FydEl0ZW06Ng=="
      }
    }
  }
}
```
```graphql
# Create a cart, with cartItems in it
# The cart could also be created empty, if cartItems:[]
mutation{
  cartCreate(userid:1, currency:CAD, cartItems:["Q2FydEl0ZW06NQ==", "Q2FydEl0ZW06Ng=="]){
    cart{
      id
    }
  }
}
# More cartItems could be later added with the cartAddItems mutation
# cartItems could be removed with the cartRemoveItems mutation
```
```javascript
{
  "data": {
    "cartCreate": {
      "cart": {
        "id": "Q2FydDoy"
      }
    }
  }
}
```
```graphql
# Now, we can take a look at our cart
query{
  cart(id:"Q2FydDoy"){
    id
    total
    currency
    cartItems {
      product{
        title
      }
    }
  }
}
# Notice how our total, in Canadian cents, has been automatically calculated from products priced in USD and EUR cents.
```
```javascript
{
  "data": {
    "cart": {
      "id": "Q2FydDoy",
      "total": 120000,
      "currency": "CAD",
      "cartItems": [
        {
          "product": {
            "title": "Glasses"
          }
        },
        {
          "product": {
            "title": "Glasses"
          }
        }
      ]
    }
  }
}
```
```graphql
# Now we can purchase our cart!
# Note: each of our mutations provides a boolean "ok", representing the success of the operation

mutation{
  cartPurchase(cartID:"Q2FydDoy"){
    ok
    cart{
      id
      total
    }
  }
}

# In this case, our purchase is successful. If any of the items in the cart had less inventory available than we had in our cart, or were disabled for purchasing, the purchase would fail with an error message informing the user of the failing cartItem.
```
```javascript
// Our successful purchase
{
  "data": {
    "cartPurchase": {
      "ok": true,
      "cart": {
        "id": "Q2FydDoy",
        "total": 120000
      }
    }
  }
}

// An error message from a failing purchase
{
  "errors": [
    {
      "message": "CartItem \"Q2FydEl0ZW06Nw==\" cannot be purchased.",
      "locations": [
        {
          "line": 61,
          "column": 3
        }
      ],
      "path": [
        "cartPurchase"
      ]
    }
  ],
  "data": {
    "cartPurchase": null
  }
}
```


## **Schema**
```graphql
enum Currency {
  USD
  CAD
  EUR
}

type Cart {
  id: ID!
  userid: Int!
  cartItems: [CartItem!]!
  currency: Currency!
  total: Int!
}

type CartItem{
  id: ID!
  product: Product!
  quantity: Int!
}

type Product {
  id: ID!
  title: String!
  price: Int!
  currency: Currency!
  inventory_count: Int!
  can_purchase: Bool!
}

type Query {
  products(id: ID!, title: String, inventoryMinimum: Int, canPurchase: Boolean): [Product]
  product(id: ID!): Product

  carts(userid: Int!): [Cart]
  cart(id: ID!): Cart

  cartItem(id: ID!): CartItem
}

type Mutation {
  productCreate(title: String!, price: Int!, currency: Currency!, inventoryCount: Int!, canPurchase: Boolean!): Product
  productDelete(id: ID!): Product
  productUpdate(id: ID!, title: String, price: Int, currency: Currency, inventoryCount: Int, canPurchase: Boolean): Product

  cartItemCreate(productID: ID!, quantity: Int!): CartItem
  cartItemUpdate(id: ID!, productID: ID, quantity: Int): CartItem

  cartCreate(userid: Int!, currency: Currency!, cartItems: [ID!]!): Cart
  cartDelete(id: ID!): Cart
  cartAddItems(cartID: ID!, cartItems: [ID!]!): Cart
  cartRemoveItems(cartID: ID!, cartItems: [ID!]!): Cart
  cartPurchase(cartID: ID!): Cart

}
```
