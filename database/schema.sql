CREATE DATABASE IF NOT EXISTS `inventory management system`;
USE `inventory management system`;

CREATE TABLE IF NOT EXISTS Category (
 Category_ID INT PRIMARY KEY,
 Category_Name VARCHAR(100) NOT NULL,
 Description VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS Supplier (
 Supplier_ID INT PRIMARY KEY,
 Company_Name VARCHAR(100) NOT NULL,
 Contact_Person VARCHAR(100),
 Phone VARCHAR(15),
 Email VARCHAR(100) UNIQUE,
 Address VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS Customer (
 Customer_ID INT PRIMARY KEY,
 Customer_Name VARCHAR(100) NOT NULL,
 Phone VARCHAR(15),
 Email VARCHAR(100) UNIQUE,
 Address VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS Product (
 Product_ID INT PRIMARY KEY,
 Product_Name VARCHAR(100) NOT NULL,
 Description VARCHAR(255),
 Unit_Price DECIMAL(10,2) NOT NULL,
 Stock_Quantity INT DEFAULT 0,
 Reorder_Level INT,
 Category_ID INT,
 FOREIGN KEY (Category_ID) REFERENCES Category(Category_ID)
);
CREATE TABLE IF NOT EXISTS Purchase_Order (
 Purchase_ID INT PRIMARY KEY,
 Purchase_Date DATE NOT NULL,
 Total_Cost DECIMAL(10,2),
 Payment_Status VARCHAR(30),
 Supplier_ID INT,
 FOREIGN KEY (Supplier_ID) REFERENCES Supplier(Supplier_ID)
);
CREATE TABLE IF NOT EXISTS Purchase_Order_Item (
 Purchase_ID INT,
 Product_ID INT,
 Quantity INT NOT NULL,
 Unit_Cost DECIMAL(10,2),
 Discount DECIMAL(10,2),
 Amount DECIMAL(10,2),
 PRIMARY KEY (Purchase_ID, Product_ID),
 FOREIGN KEY (Purchase_ID) REFERENCES Purchase_Order(Purchase_ID),
 FOREIGN KEY (Product_ID) REFERENCES Product(Product_ID)
);
CREATE TABLE IF NOT EXISTS Sales_Invoice (
 Sale_ID INT PRIMARY KEY,
 Sale_Date DATE NOT NULL,
 Total_Amount DECIMAL(10,2),
 Payment_Status VARCHAR(30),
 Customer_ID INT,
 FOREIGN KEY (Customer_ID) REFERENCES Customer(Customer_ID)
);
CREATE TABLE IF NOT EXISTS Sales_Invoice_Item (
 Sale_ID INT,
 Product_ID INT,
 Quantity INT NOT NULL,
 Unit_Selling_Price DECIMAL(10,2),
 Discount DECIMAL(10,2),
 Amount DECIMAL(10,2),
 PRIMARY KEY (Sale_ID, Product_ID),
 FOREIGN KEY (Sale_ID) REFERENCES Sales_Invoice(Sale_ID),
 FOREIGN KEY (Product_ID) REFERENCES Product(Product_ID)
);

-- Login accounts. Public registration is restricted to the 'user' role.
CREATE TABLE IF NOT EXISTS App_User (
 User_ID INT AUTO_INCREMENT PRIMARY KEY,
 Username VARCHAR(80) NOT NULL UNIQUE,
 Password_Hash VARCHAR(255) NOT NULL,
 Role ENUM('admin','user') NOT NULL DEFAULT 'user',
 Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
