import pymongo
import pandas as pd

def drop_all_collections(mongo_db):
    """ Function to remove all MongoDB collections. """
    # Fetch name for each collection
    collections = mongo_db.list_collection_names()
    for collection in collections:
        # Drop each collection
        mongo_db[collection].drop()

def migrate_data(db, mongo_db):
    """ Fetches all data contained in MySQL database and imports it into MongoDB. """
    # retrieve all stored data from MySQL database
    df_user = pd.read_sql_query("SELECT * FROM User_", db)
    df_order = pd.read_sql_query("SELECT * FROM Order_", db)
    df_invoice = pd.read_sql_query("SELECT * FROM Invoice", db)
    df_product = pd.read_sql_query("SELECT * FROM Product", db)
    df_order_products = pd.read_sql_query("SELECT * FROM Order_has_Product", db)
    df_cart = pd.read_sql_query("SELECT * FROM User_has_Product", db)

    # Adjust primary key field names and date formats for MongoDB
    df_user.rename(columns={'user_id': '_id'}, inplace=True)
    df_user['date_registered'] = pd.to_datetime(df_user['date_registered'])
    df_order.rename(columns={'order_id': '_id'}, inplace=True)
    df_order['date_placed'] = pd.to_datetime(df_order['date_placed'])
    df_product.rename(columns={'product_id': '_id'}, inplace=True)
    df_invoice['date_issued'] = pd.to_datetime(df_invoice['date_issued'])

    # Create users collection
    col = mongo_db['users']
    col.create_index([('email', pymongo.ASCENDING)], unique=True)
    col.create_index([('shopping_basket.product_id', pymongo.ASCENDING)])
    users = [row.dropna().to_dict() for _, row in df_user.iterrows()]
    # Group shopping cart data by user_id
    carts = {user_id: group[['product_id', 'quantity_in_cart']].to_dict(orient='records')
             for user_id, group in df_cart.groupby('user_id')}
    
    # Add products that are currently stored in user's shopping basket
    for user in users:
        user.update({'shopping_basket': carts.get(user['_id'])}) 
    try:
        col.insert_many(users)
    except pymongo.errors.BulkWriteError as e:
        print(e.details['writeErrors'])

    # Create products collection
    col = mongo_db['products']
    products = [row.dropna().to_dict() for _, row in df_product.iterrows()]
    col.insert_many(products)

    # Create orders collection
    col = mongo_db['orders']
    col.create_index([('date_placed', pymongo.ASCENDING)])
    col.create_index([('user_id', pymongo.ASCENDING)])
    orders = [row.dropna().to_dict() for _, row in df_order.iterrows()]
    products_in_order = {order_id: group[['product_id', 'quantity_in_order']].to_dict(orient='records')
             for order_id, group in df_order_products.groupby('order_id')}
    invoices = [row.dropna().to_dict() for _, row in df_invoice.iterrows()]
    
    # Add products associated with each order
    for order in orders:
        order.update({'products': products_in_order.get(order['_id'])})
        filtered_invoices = [invoice for invoice in invoices if invoice.get('order_id') == order['_id']]
        
        # Omitting 'order_id' and 'invoice_id' when adding invoice to order
        order.update({'invoice': {k: v for k, v in filtered_invoices[0].items() if k not in ['order_id', 'invoice_id']}})
    try:
        col.insert_many(orders)
    except pymongo.errors.BulkWriteError as e:
        print(e.details['writeErrors'])
    
    


