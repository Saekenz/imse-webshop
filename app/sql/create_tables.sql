-- -----------------------------------------------------
-- Table `User`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `User_` ;

CREATE TABLE IF NOT EXISTS `User_` (
  `user_id` INT NOT NULL AUTO_INCREMENT,
  `first_name` VARCHAR(50),
  `last_name` VARCHAR(50),
  `email` VARCHAR(100) NOT NULL,
  `password` VARCHAR(100) NOT NULL,
  `date_registered` DATE,
  PRIMARY KEY (`user_id`)
 );


-- -----------------------------------------------------
-- Table `Order_`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Order_` ;

CREATE TABLE IF NOT EXISTS `Order_` (
  `order_id` INT NOT NULL AUTO_INCREMENT,
  `date_placed` DATE,
  `order_status` VARCHAR(45),
  `user_id` INT NOT NULL,
  PRIMARY KEY (`order_id`),
  CONSTRAINT `fk_Order_User`FOREIGN KEY (`user_id`) REFERENCES `User_` (`user_id`) ON DELETE CASCADE
);


-- -----------------------------------------------------
-- Table `Invoice`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Invoice` ;

CREATE TABLE IF NOT EXISTS `Invoice` (
  `invoice_id` INT NOT NULL AUTO_INCREMENT,
  `order_id` INT NOT NULL,
  `total_cost` DECIMAL(10,2),
  `date_issued` DATE,
  `payment_status` VARCHAR(45),
  PRIMARY KEY (`invoice_id`, `order_id`),
  CONSTRAINT `fk_Invoice_Order_` FOREIGN KEY (`order_id`) REFERENCES `Order_` (`order_id`) ON DELETE CASCADE
);


-- -----------------------------------------------------
-- Table `Product`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Product` ;

CREATE TABLE IF NOT EXISTS `Product` (
  `product_id` INT NOT NULL AUTO_INCREMENT,
  `product_name` VARCHAR(50),
  `price` DECIMAL(8,2),
  `quantity` INT,
  `product_desc` VARCHAR(100),
  UNIQUE (`product_name`),
  PRIMARY KEY (`product_id`)
);


-- -----------------------------------------------------
-- Table 'Product Is Accessory For Product'
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Product_is_Accessory_for_Product` ;

CREATE TABLE IF NOT EXISTS `Product_is_Accessory_for_Product` (
    `main_product_id` INT NOT NULL,
    `accessory_product_id` INT NOT NULL,
    PRIMARY KEY (`main_product_id`, `accessory_product_id`),
    CONSTRAINT `fk_Product_is_Accessory_for_Product_Main`    FOREIGN KEY (`main_product_id`) REFERENCES `Product` (`product_id`),
    CONSTRAINT `fk_Product_is_Accessory_for_Product_Accessory` FOREIGN KEY (`accessory_product_id`) REFERENCES `Product` (`product_id`)
    );


-- -----------------------------------------------------
-- Table 'Category'
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Category` ;

CREATE TABLE IF NOT EXISTS `Category` (
    `category_id` INT NOT NULL AUTO_INCREMENT,
    `category_name` VARCHAR(50),
    `category_desc` VARCHAR(50),
    PRIMARY KEY (`category_id`)
    );

-- -----------------------------------------------------
-- Table 'Order_has_Product'
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Order_has_Product` ;

CREATE TABLE IF NOT EXISTS `Order_has_Product` (
  `order_id` INT NOT NULL,
  `product_id` INT NOT NULL,
  `quantity_in_order` INT,
  PRIMARY KEY (`order_id`, `product_id`),
  CONSTRAINT `fk_Order_has_Product_Order`    FOREIGN KEY (`order_id`) REFERENCES `Order_` (`order_id`),
  CONSTRAINT `fk_Order_has_Product_Product` FOREIGN KEY (`product_id`) REFERENCES `Product` (`product_id`)
);

-- -----------------------------------------------------
-- Table 'Product has Category'
-- -----------------------------------------------------
DROP TABLE IF EXISTS `Product_has_Category` ;

CREATE TABLE IF NOT EXISTS `Product_has_Category` (
    `product_id` INT NOT NULL,
    `category_id` INT NOT NULL,
    PRIMARY KEY (`product_id`, `category_id`),
    CONSTRAINT `fk_Product_has_Category_Product`    FOREIGN KEY (`product_id`) REFERENCES `Product` (`product_id`),
    CONSTRAINT `fk_Product_has_Category_Category` FOREIGN KEY (`category_id`) REFERENCES `Category` (`category_id`)
    );

-- -----------------------------------------------------
-- Table `User_has_Product`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `User_has_Product` ;

CREATE TABLE IF NOT EXISTS `User_has_Product` (
  `user_id` INT NOT NULL,
  `product_id` INT NOT NULL,
  `quantity_in_cart` INT,
  PRIMARY KEY (`user_id`, `product_id`),
  CONSTRAINT `fk_User_has_Product_User`    FOREIGN KEY (`user_id`) REFERENCES `User_` (`user_id`),
  CONSTRAINT `fk_User_has_Product_Product` FOREIGN KEY (`product_id`) REFERENCES `Product` (`product_id`)
);
