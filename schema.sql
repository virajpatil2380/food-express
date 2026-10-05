-- Food Express Database Schema Specification
CREATE DATABASE IF NOT EXISTS food_delivery_db;
USE food_delivery_db;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    role ENUM('Customer', 'Kitchen', 'Admin') DEFAULT 'Customer',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Categories Table
CREATE TABLE IF NOT EXISTS categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

-- 3. Menu Items Table (Includes image_url for food showcase)
CREATE TABLE IF NOT EXISTS menu_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    category_id INT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    image_url TEXT,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL
);

-- 4. Orders Table
CREATE TABLE IF NOT EXISTS orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT 1,
    total_amount DECIMAL(10,2) NOT NULL,
    delivery_address TEXT NOT NULL,
    status ENUM('Pending', 'Preparing', 'Out for Delivery', 'Delivered', 'Cancelled') DEFAULT 'Pending',
    payment_method ENUM('UPI', 'COD', 'Card') DEFAULT 'COD',
    payment_status ENUM('Pending', 'Completed', 'Failed') DEFAULT 'Pending',
    transaction_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 5. Order Items Table
CREATE TABLE IF NOT EXISTS order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    item_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES menu_items(item_id)
);

-- 6. Payments Table
CREATE TABLE IF NOT EXISTS payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    upi_id VARCHAR(100),
    transaction_id VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);
