SELECT p.product_name AS "name", p.product_desc AS "info", cart.quantity_in_cart AS "quantity", p.price, p.product_id 
FROM User_has_Product cart
INNER JOIN Product p 
ON cart.product_id = p.product_id
WHERE cart.user_id = %s;