import pandas as pd
import datetime as dt
import sqlparse
import sys

def read_sql_file(file_path):
    """ Read sql file and return statements contained in it. """
    with open(file_path, 'r') as file:
        sql_content = file.read()
    return sql_content

def split_sql_statements(sql_content):
    # Use sqlparse to split SQL statements
    statements = sqlparse.split(sql_content)
    # Filter out empty statements
    statements = [statement.strip() for statement in statements if statement.strip()]
    return statements

def has_data_been_migrated(db):
    """ Checks if data has already been migrated from MySQL to Mongo database. """
    return len(pd.read_sql_query(sql='SHOW Tables', con=db))

def find_user_by_email(db, mongo_db, email):
    """ Find user by email address in MySQL/Mongo database. """
    if has_data_been_migrated(db):
        sql = f"SELECT * FROM User_ WHERE LOWER(email) = '{email.lower()}'"
        res = pd.read_sql_query(sql=sql, con=db).to_dict(orient='records')
        return res[0] if res else None
    else:
        return mongo_db['users'].find_one({'email': email}, {'shopping_basket': 0})

def update_user_by_email(db, mongo_db, email, form):
    """ Takes user input from form and updates user info in MySQL/Mongo database. """
    if has_data_been_migrated(db):
        sql = f"""
                UPDATE User_
                SET first_name = {"'%s'" % form.first_name.data if form.first_name.data != 'None' else 'NULL'},
                    last_name = {"'%s'" % form.last_name.data if form.last_name.data != 'None' else 'NULL'}
                WHERE email = '{email}'
                """
        cursor = db.cursor()
        cursor.execute(sql)
        db.commit()
        cursor.close()
    else:
        query = {'email': email}
        update_data = {
            "$set": {
                "first_name": form.first_name.data, 
                "last_name": form.last_name.data
            }   
        }
        mongo_db['users'].update_one(query, update_data)

def report_unpaid_invoices(db, mongo_db):
    """ Fetches users that have unpaid invoices and sorts by number of unpaid invoices. """
    if has_data_been_migrated(db):
        sql_statement = read_sql_file('app/sql/invoice_report.sql')
        return pd.read_sql_query(sql_statement, con=db, index_col='user_id')
    else:
        # Define the timeframe as the last year
        cutoff_date = dt.datetime.now() - dt.timedelta(days=365)
        pipeline = [
            {
                "$match": {
                    "date_placed": {"$gte": cutoff_date},
                    "invoice.payment_status": {"$ne": "paid"}
                }
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user_info"
                }
            },
            {
                "$unwind": {
                    "path": "$user_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$group": {
                    "_id": "$user_id",
                    "first_name": {"$first": "$user_info.first_name"},
                    "last_name": {"$first": "$user_info.last_name"},
                    "unpaid_invoice_count": {"$sum": 1}
                }
            },
            {
                "$sort": {"unpaid_invoice_count": -1}
            }
        ]

        result = list(mongo_db.orders.aggregate(pipeline))
        df = pd.DataFrame(result)

        # Rename columns to correspond with columns of MySQL query
        df.rename(columns={"_id": "user_id", "first_name": "First Name", "last_name": "Last Name", 
                           "unpaid_invoice_count": "Unpaid Invoices"}, inplace=True)
        return df

def find_cart_by_user_id_mysql(db, user_id):
    """ Fetches shopping cart data for the logged in user from MySQL database. """
    sql_statement = read_sql_file('app/sql/shopping_cart_query.sql')
    df = pd.read_sql_query(sql_statement, con=db, params=(user_id,))
    df['total'] = df['price'] * df['quantity'] # Add total price field for each product
    return df

def find_cart_by_user_id_nosql(mongo_db, user_id):
    """ Fetches shopping cart data for the logged in user from MongoDB. """
    pipeline = [
        {"$match": {"_id": user_id}},
        {"$unwind": "$shopping_basket"},
        {
            "$lookup": {
                "from": "products",
                "localField": "shopping_basket.product_id",
                "foreignField": "_id",
                "as": "product_info"
            }
        },
        {"$unwind": "$product_info"},
        {
            "$project": {
                "product_id": "$shopping_basket.product_id",
                "quantity_in_cart": "$shopping_basket.quantity_in_cart",
                "product_name": "$product_info.product_name",
                "product_desc": "$product_info.product_desc",
                "price": "$product_info.price",
                "total": {"$multiply": ["$shopping_basket.quantity_in_cart", "$product_info.price"]}
            }
        },
        {
            "$group": {
                "_id": "$_id",
                "shopping_basket": {
                    "$push": {
                        "product_id": "$product_id",
                        "product_name": "$product_name",
                        "product_desc": "$product_desc",
                        "quantity_in_cart": "$quantity_in_cart",
                        "price": "$price",
                        "total": "$total"
                    }
                }
            }
        }
    ]

    # Execute the aggregation pipeline
    result = list(mongo_db.users.aggregate(pipeline))

    # Check if the user has any products in their shopping basket
    if result and result[0].get('shopping_basket'):
        df = pd.DataFrame(result)
        df = df.explode('shopping_basket')

        # Create columns corresponding to columns of MySQL query
        df['name'] = df['shopping_basket'].apply(lambda x: x['product_name'])
        df['info'] = df['shopping_basket'].apply(lambda x: x['product_desc'])
        df['quantity'] = df['shopping_basket'].apply(lambda x: x['quantity_in_cart'])
        df['price'] = df['shopping_basket'].apply(lambda x: x['price'])
        df['product_id'] = df['shopping_basket'].apply(lambda x: x['product_id'])
        df['total'] = df['shopping_basket'].apply(lambda x: x['total'])

        # Drop not needed columns from DataFrame
        df = df.drop(["_id", "shopping_basket"], axis=1)
        return df
    else:
        return pd.DataFrame()  # Return an empty DataFrame if the user has no items in their cart

def find_cart_by_user_id(db, mongo_db, user_id):
    """ Fetches shopping cart data for the logged in user and adds total cost of included items. """
    if len(pd.read_sql_query(sql='SHOW Tables', con=db)):
        return find_cart_by_user_id_mysql(db, user_id)
    else:
        return find_cart_by_user_id_nosql(mongo_db, user_id)

def create_and_insert_order(db, mongo_db, df, user_id):
    """ Creates a new order and inserts it into MySQL/Mongo Database. """
    # Check if shopping basket is empty
    if df.empty:
        return False
    
    current_date = dt.date.today()
    if has_data_been_migrated(db=db):
        try:
            # Create new Order
            cursor = db.cursor()
            order_query = "INSERT INTO `Order_` (date_placed, order_status, user_id) VALUES (%s, %s, %s)"
            cursor.execute(order_query, (current_date, "new", user_id))
            order_id = cursor.lastrowid

            # Add each Product from cart to Order
            order_products_query = "INSERT INTO `Order_has_Product` (order_id, product_id, quantity_in_order) VALUES (%s, %s, %s)"
            for _, row in df.iterrows():
                product_id = row['product_id']
                quantity_ordered = row['quantity']
                quantity_available = find_quantity_by_product_id(cursor, product_id)

                # Check if requested quantity of products is in stock
                if quantity_ordered > quantity_available:
                    print(f"Error: Insufficient quantity available for product {product_id}. Order not placed.", file=sys.stderr)
                    raise Exception(f"Error: Insufficient quantity available for product {product_id}. Order not placed.")
                else:
                    cursor.execute("UPDATE `Product` SET `quantity` = `quantity` - %s WHERE `product_id` = %s",
                                   (quantity_ordered, product_id))
                cursor.execute(order_products_query, (order_id, product_id, quantity_ordered))
        
            # Create new invoice for order
            invoice_query = "INSERT INTO `Invoice` (order_id, total_cost, date_issued, payment_status) VALUES (%s, %s, %s, %s)"
            total_cost = float(df['total'].sum())
            cursor.execute(invoice_query, (order_id, total_cost, current_date, 'pending'))

            # Remove all items from cart after creating the order
            empty_cart_by_user_id(db, mongo_db, user_id)
            db.commit()
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            db.rollback()  # Rollback all changes if an error occurs during transaction
            return False
        else:
            return True

    else:
        # Retrieve _id of the latest order
        latest_order = mongo_db['orders'].find_one(sort=[('_id', -1)])
        # Set new order_id to be latest order_id + 1
        new_order_id = latest_order['_id']+1

        today = pd.to_datetime(current_date)
        
        # Extract needed columns from shopping basket DataFrame
        products = df[["product_id", "quantity"]]
        
        # Check if needed products are in stock
        for _, row in products.iterrows():
            product_id = row["product_id"]
            quantity_in_basket = row["quantity"]

            product_info = mongo_db['products'].find_one({"_id": int(product_id)})
            if not product_info or product_info.get("quantity", 0) < quantity_in_basket:
                # If any of the products in the shopping cart are not available do not place the order
                return False

        # Create order document
        order_document = {
            "_id": new_order_id,
            "date_placed": today,
            "order_status": "new",
            "user_id": user_id,
            "products": [],
            "invoice": {
                "total_cost": round(df['total'].sum(), 2),
                "date_issued": today,
                "payment_status": "pending"
            }
        }

        # Convert the products Dataframe subset to a list of dictionaries
        products_list = products.to_dict(orient='records')

        # Update the products field in the order_document
        order_document["products"] = products_list

        # Insert the document into the collection
        mongo_db['orders'].insert_one(order_document)

        # Empty the users shopping basket
        empty_cart_by_user_id(db=db, mongo_db=mongo_db,user_id=user_id)

        # Update the products collection to decrement the quantity for each product
        for _, row in products.iterrows():
            product_id = row["product_id"]
            quantity_in_basket = row["quantity"]

            mongo_db['products'].update_one(
                {"_id": int(product_id)},
                {"$inc": {"quantity": -int(quantity_in_basket)}}
            )
        return True

def find_quantity_by_product_id(cursor, product_id):
    """ Fetches the available quantity for a specific product from MySQL database. """
    check_quantity_query = "SELECT quantity FROM `Product` WHERE product_id = %s"
    cursor.execute(check_quantity_query, (product_id,))
    return cursor.fetchone()[0]

def empty_cart_by_user_id(db, mongo_db, user_id):
    """ Fetches the available quantity for a specific product. """
    if has_data_been_migrated(db):
        cursor = db.cursor()
        query = "DELETE FROM `User_has_Product` WHERE `user_id` = %s"
        cursor.execute(query, (user_id,))
    else:
        user_document = mongo_db['users'].find_one({"_id": user_id})

        if user_document:
            mongo_db['users'].update_one(
                {"_id": user_id},
                {"$set": {"shopping_basket": []}}
            )
