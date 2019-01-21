import base64

import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField

from graphql import GraphQLError

from sqlalchemy.orm import scoped_session

from storeify.models import Product as ProductModel, Cart as CartModel, CartItem as CartItemModel
from storeify.db import get_db_session
from storeify.currency import Currency as CurrencyClass
from storeify.currency import convert as convert_currency


db_session = get_db_session()
Currency = graphene.Enum.from_enum(CurrencyClass)


def decode_id(id):
    (table_name, primary_key) = base64.b64decode(
        id.encode()).decode().split(':')
    return primary_key


def encode_id(table_name, primary_key):
    ret = base64.b64encode(
        bytes(
            table_name +
            ':' +
            primary_key,
            'utf-8')).decode("utf-8")
    return ret


def validate_cart_item(cartItem, cartItemID):
    if cartItem is None:
        raise GraphQLError('CartItem "' + cartItemID + '" does not exist.')
    if not cartItem.product.can_purchase:
        raise GraphQLError(
            'CartItem "' +
            cartItemID +
            '" cannot be purchased.')
    if cartItem.product.inventory_count == 0:
        raise GraphQLError('CartItem "' + cartItemID + '" is out of stock.')
    elif cartItem.product.inventory_count < cartItem.quantity:
        raise GraphQLError('CartItem "' +
                           cartItemID +
                           '" has only ' +
                           str(cartItem.product.inventory_count) +
                           ' units left.')


class Cart(SQLAlchemyObjectType):
    class Meta:
        model = CartModel
        interfaces = (relay.Node, )

    cartItems = graphene.List(lambda: CartItem)
    total = graphene.Int()
    currency = graphene.String()

    def resolve_cartItems(self, info):
        query = CartItem.get_query(info)
        return query.filter_by(cart_id=self.id)

    def resolve_total(self, info):
        # Convert the price of each cart item into the cart currency
        total = 0
        for cartItem in self.cart_items:
            curpair = str(CurrencyClass(int(self.currency))
                          )[-3:] + '/' + cartItem.product.currency
            total += (convert_currency(curpair,
                                       cartItem.product.price) * cartItem.quantity)
        return total

    def resolve_currency(self, info):
        return str(CurrencyClass(int(self.currency)))[-3:]


class CartItem(SQLAlchemyObjectType):
    class Meta:
        model = CartItemModel
        interfaces = (relay.Node, )


class Product(SQLAlchemyObjectType):
    class Meta:
        model = ProductModel
        interfaces = (relay.Node, )


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    products = graphene.List(
        Product,
        id=graphene.ID(),
        title=graphene.String(),
        inventory_minimum=graphene.Int(),
        can_purchase=graphene.Boolean())

    product = graphene.Field(Product, id=graphene.ID(required=True))
    carts = graphene.Field(lambda: graphene.List(Cart), userid=graphene.Int())
    cart = graphene.Field(Cart, id=graphene.ID(required=True))
    cartItem = graphene.Field(CartItem, id=graphene.ID(required=True))

    def resolve_products(self, info, **kwargs):
        query = Product.get_query(info)
        if 'id' in kwargs:
            query = query.filter_by(id=decode_id(kwargs.get('id')))
        if 'title' in kwargs:
            query = query.filter_by(title=kwargs.get('title'))
        if 'inventory_minimum' in kwargs:
            query = query.filter(
                ProductModel.inventory_count >= kwargs.get('inventory_minimum'))
        if 'can_purchase' in kwargs:
            query = query.filter_by(can_purchase=kwargs.get('can_purchase'))
        return query.all()

    def resolve_product(self, info, id):
        query = Product.get_query(info)
        return query.get(decode_id(id))

    def resolve_carts(self, info, userid):
        query = Cart.get_query(info)
        return query.filter_by(userid=userid).all()

    def resolve_cart(self, info, id):
        query = Cart.get_query(info)
        return query.get(decode_id(id))

    def resolve_cartItem(self, info, id):
        query = CartItem.get_query(info)
        return query.get(decode_id(id))


class ProductCreate(graphene.Mutation):
    class Arguments:
        title = graphene.NonNull(graphene.String)
        price = graphene.NonNull(graphene.Int)
        currency = graphene.NonNull(Currency)
        inventory_count = graphene.NonNull(graphene.Int)
        can_purchase = graphene.NonNull(graphene.Boolean)

    ok = graphene.Boolean()
    product = graphene.Field(lambda: Product)

    def mutate(self, info, title, price,
               currency, inventory_count, can_purchase):
        new_product = ProductModel(title=title,
                                   price=price,
                                   currency=currency,
                                   inventory_count=inventory_count,
                                   can_purchase=can_purchase)
        db_session.add(new_product)
        db_session.commit()

        ok = True
        return ProductCreate(product=new_product, ok=ok)


class ProductDelete(graphene.Mutation):
    class Arguments:
        id = graphene.NonNull(graphene.ID)

    ok = graphene.Boolean()
    product = graphene.Field(lambda: Product)

    def mutate(self, info, id):
        to_delete = db_session.query(ProductModel).get(decode_id(id))
        db_session.delete(to_delete)
        db_session.commit()

        ok = True
        return ProductDelete(ok=ok, product=to_delete)


class ProductUpdate(graphene.Mutation):
    class Arguments:
        id = graphene.NonNull(graphene.ID)
        title = graphene.String()
        price = graphene.Int()
        currency = graphene.Argument(Currency)
        inventory_count = graphene.Int()
        can_purchase = graphene.Boolean()

    ok = graphene.Boolean()
    product = graphene.Field(lambda: Product)

    def mutate(self, info, **kwargs):
        to_edit = db_session.query(ProductModel).get(decode_id(kwargs['id']))
        if 'title' in kwargs:
            to_edit.title = kwargs['title']
        if 'price' in kwargs:
            to_edit.price = kwargs['price']
        if 'currency' in kwargs:
            to_edit.currency = kwargs['currency']
        if 'inventory_count' in kwargs:
            to_edit.inventory_count = kwargs['inventory_count']
        if 'can_purchase' in kwargs:
            to_edit.can_purchase = kwargs['can_purchase']
        db_session.commit()

        ok = True
        return ProductUpdate(product=to_edit, ok=ok)


class CartItemCreate(graphene.Mutation):
    class Arguments:
        productID = graphene.NonNull(graphene.ID)
        quantity = graphene.NonNull(graphene.Int)

    ok = graphene.Boolean()
    cartItem = graphene.Field(lambda: CartItem)

    def mutate(self, info, productID, quantity):
        if quantity <= 0:
            raise GraphQLError('Product quantity must be greater than zero.')
        product = db_session.query(ProductModel).get(decode_id(productID))
        if product is None:
            raise GraphQLError('Product ID is invalid.')
        new_cart_item = CartItemModel(product=product, quantity=quantity)
        db_session.add(new_cart_item)
        db_session.commit()

        ok = True
        return CartItemCreate(ok=ok, cartItem=new_cart_item)


class CartItemUpdate(graphene.Mutation):
    class Arguments:
        id = graphene.NonNull(graphene.ID)
        productID = graphene.ID()
        quantity = graphene.Int()

    ok = graphene.Boolean()
    cartItem = graphene.Field(lambda: CartItem)

    def mutate(self, info, id, **kwargs):
        to_edit = db_session.query(CartItemModel).get(decode_id(id))
        if 'productID' in kwargs:
            product = db_session.query(ProductModel).get(
                decode_id(kwargs['productID']))
            to_edit.product = product
        if 'quantity' in kwargs:
            to_edit.quantity = kwargs['quantity']
        db_session.commit()

        ok = True
        return CartItemUpdate(ok=ok, cartItem=to_edit)


class CartCreate(graphene.Mutation):
    """
    Creates a cart for a user.
    Each user can have a single cart.
    """
    class Arguments:
        userid = graphene.NonNull(graphene.Int)
        currency = graphene.NonNull(Currency)
        cart_items = graphene.NonNull(
            graphene.List(
                graphene.NonNull(
                    graphene.ID)))

    ok = graphene.Boolean()
    cart = graphene.Field(lambda: Cart)

    def mutate(self, info, userid, currency, **kwargs):
        new_cart = CartModel(userid=userid, currency=currency)
        new_cart.currency = currency
        if 'cart_items' in kwargs:
            for cartItemID in kwargs['cart_items']:
                cartItem = db_session.query(
                    CartItemModel).get(decode_id(cartItemID))
                validate_cart_item(cartItem, cartItemID)
                print(decode_id(cartItemID))
                new_cart.cart_items.append(cartItem)
        db_session.add(new_cart)
        db_session.commit()

        ok = True
        return CartCreate(ok=ok, cart=new_cart)


class CartDelete(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    ok = graphene.Boolean()
    cart = graphene.Field(lambda: Cart)

    def mutate(self, info, id):
        to_delete = db_session.query(CartModel).get(decode_id(id))
        db_session.delete(to_delete)
        db_session.commit()

        ok = True
        return CartDelete(ok=ok, cart=to_delete)


class CartAddItems(graphene.Mutation):
    class Arguments:
        cartID = graphene.ID(required=True)
        cartItems = graphene.NonNull(
            graphene.List(
                graphene.NonNull(
                    graphene.ID)))

    ok = graphene.Boolean()
    cart = graphene.Field(lambda: Cart)

    def mutate(self, info, cartID, cartItems):
        cart = db_session.query(CartModel).get(decode_id(cartID))
        for cartItemID in cartItems:
            cartItem = db_session.query(
                CartItemModel).get(decode_id(cartItemID))
            validate_cart_item(cartItem, cartItemID)

            cart.cart_items.append(cartItem)
        db_session.commit()

        ok = True
        return CartAddItems(ok=ok, cart=cart)


class CartRemoveItems(graphene.Mutation):
    class Arguments:
        cartID = graphene.ID(required=True)
        cartItems = graphene.NonNull(
            graphene.List(
                graphene.NonNull(
                    graphene.ID)))

    ok = graphene.Boolean()
    cart = graphene.Field(lambda: Cart)

    def mutate(self, info, cartID, cartItems):
        cart = db_session.query(CartModel).get(decode_id(cartID))
        for cartItemID in cartItems:
            cartItem = db_session.query(
                CartItemModel).get(decode_id(cartItemID))
            cart.cart_items.remove(cartItem)
        db_session.commit()

        ok = True
        return CartAddItems(ok=ok, cart=cart)


class CartPurchase(graphene.Mutation):
    class Arguments:
        cartID = graphene.ID()

    ok = graphene.Boolean()
    cart = graphene.Field(lambda: Cart)

    def mutate(self, info, cartID):
        # Because the purchasability  of the product is checked
        # when the product is initially added to the cart, the product may
        # become out of stock or unpurchasable while the product is in cart.
        # Thus, each product in the cart should be checked for purchasability
        # before the purchase is completed.
        cart = db_session.query(CartModel).get(decode_id(cartID))
        if len(cart.cart_items) == 0:
            raise GraphQLError('Cart cannot be purchased. It is empty.')
        for cartItem in cart.cart_items:
            # Verify that the cart item is both in stock and purchasable
            cartItemID = encode_id(
                CartItemModel.__tablename__, str(
                    cartItem.id))
            validate_cart_item(cartItem, cartItemID)
        # Purchase the items
        for cartItem in cart.cart_items:
            cartItem.product.inventory_count -= cartItem.quantity
        db_session.commit()
        ok = True
        return CartPurchase(ok=ok, cart=cart)


class Mutations(graphene.ObjectType):
    product_create = ProductCreate.Field()
    product_update = ProductUpdate.Field()
    product_delete = ProductDelete.Field()

    cartItem_create = CartItemCreate.Field()
    cartItem_update = CartItemUpdate.Field()

    cart_create = CartCreate.Field()
    cart_delete = CartDelete.Field()
    cart_add_items = CartAddItems.Field()
    cart_remove_items = CartRemoveItems.Field()
    cart_purchase = CartPurchase.Field()


schema = graphene.Schema(query=Query, mutation=Mutations)
