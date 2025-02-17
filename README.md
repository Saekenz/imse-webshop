# Webshop Application

## Overview
This university project is a webshop application designed to compare SQL (MySQL) and NoSQL (MongoDB) database models. The application was built using Python and the Flask web framework and is containerized using Docker Desktop for deployment and debugging.

## Technologies Used
- **Relational Database (SQL)**: MySQL
- **NoSQL Database**: MongoDB
- **Backend**: Python with Flask
- **Containerization**: Docker Desktop

## Database Design
### Relational Database Model (MySQL)
- The database schema follows the ER-model from the first milestone.
- Entities were mapped to SQL tables.
- Many-to-many relationships were handled with additional join tables.
- Entities `User` and `Order` were renamed to `User_` and `Order_` to avoid SQL keyword conflicts.
- Primary tables:
  - `User_`, `Order_`, `Invoice`, `Product`
  - Join tables for many-to-many relationships

### NoSQL Database Model (MongoDB)
- Converted from the SQL model with three main collections: `users`, `orders`, and `products`.
- Embedded related data to optimize query performance:
  - `shopping_basket` embedded in `users` collection
  - `invoice` and `order_has_product` embedded in `orders` collection

## Performance Optimizations
- Used **embedding** to reduce joins and improve query speed.
- Created indexes for frequently queried fields:
  - `users`: `email`, `shopping_basket.product_id`
  - `orders`: `date_placed`, `user_id`

## Use Cases
### Place Order (SQL vs. NoSQL)
**SQL Implementation:**
1. Fetch shopping basket data (JOIN `user_has_product` and `product` tables).
2. Check product availability.
3. Create a new order.
4. Insert order details into `Order_has_Product`.
5. Update product quantities.
6. Generate an invoice and clear the shopping basket.

**NoSQL Implementation:**
1. Fetch and increment order ID.
2. Check product availability.
3. Insert a new order document.
4. Empty the user's shopping basket.
5. Update product quantities.

## Reports
### SQL Report: Users with Unpaid Invoices
- Uses two JOINs to retrieve users with unpaid invoices from the past year.
- Filters results and sorts by the number of unpaid invoices.

### NoSQL Report: Users with Unpaid Invoices
- Uses **$lookup**, **$unwind**, and **$group** operators to replace JOINs.
- Filters `orders` collection for unpaid invoices from the past year.
- Groups results by user and sorts by invoice count.
