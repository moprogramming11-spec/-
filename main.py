import os
import asyncio
import sqlite3

import cloudinary
import cloudinary.uploader

from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
import jwt


cloudinary.config(
    cloud_name="ywq1nmza",
    api_key="184542494378983",
    api_secret="AVtz_MXl8sThEkbO7qV1wo4OvVc", 
)

#------------------connecting-with-db----------------------
app = FastAPI()
conn = sqlite3.connect("database.db", check_same_thread=False)

#------------------creating-tables----------------------
#-----------------------users---------------------------
conn.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)''')
#--------------------products--------------------------
conn.execute('''CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    image_url TEXT
)''')
#--------------------orders--------------------------
conn.execute('''CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    user_address TEXT NOT NULL,
    order_status TEXT DEFAULT 'pending',
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    total_price REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
)''')


#------------Create a Pydantic model for user registration----------------
class Users(BaseModel):
    username: str
    email: str
    phone: str
    password: str = Field(..., min_length=6) 
    
class Products(BaseModel):
    name: str
    description: str
    price: float
    image_url: str = None
    
class Orders(BaseModel):
    user_id: int
    username: str
    user_address: str
    product_id: int
    quantity: int
    total_price: float
    

#------------------creat-tokens----------------------- 

SECRET_KEY = "sokar.w.laban_secret_key"
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token      
  
  
#----------------------img-url-maker----------------------

@app.post("/upload-image")
def upload_image(image: UploadFile = File(...)):

    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file."
        )

    try:
        result = cloudinary.uploader.upload(
            image.file,
            folder="b-laban"
        )
 
        return {
            "message": "Image uploaded successfully",
            "img_url": result["secure_url"]
        }

    except Exception as error:
        print("Cloudinary upload error:", repr(error))

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:
        image.file.close()


#------------------Authentication-----------------------
#write a function to hash the password
def hash_password(password: str) -> str:
    ph = PasswordHash()
    hashed_password = ph.hash(password)
    return hashed_password

@app.post("/register")
def register_user(user: Users):
    # Hash the password before storing it in the database
    hashed_password = hash_password(user.password)

    try:
        conn.execute(
            "INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)",
            (user.username, user.email, user.phone, hashed_password)
        )
        conn.commit()
        return {"message": "User registered successfully"}
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail="Username, email, or phone already exists")
    
@app.post("/login")
def login_user(username: str, password: str):
    cursor = conn.execute(
        "SELECT id, password FROM users WHERE username = ?",
        (username,)
    )
    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    user_id, hashed_password = user

    ph = PasswordHash()
    if not ph.verify(password, hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # Create a JWT token for the authenticated user
    access_token = create_access_token({"user_id": user_id, "username": username})

    return {"access_token": access_token, "token_type": "bearer"}    

#------------------authroization-----------------------
def requirs_admin(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if username != "admin":
            raise HTTPException(status_code=403, detail="Admin privileges required")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    
#------------------products-end-points----------------------    
#------------------add-product-----------------------
@app.post("/products")
def add_product(product: Products, token: str):
    requirs_admin(token)
    conn.execute(
        "INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)",
        (product.name, product.description, product.price, product.image_url)
    )
    conn.commit()
    return {"message": "Product added successfully"}

#------------------get-all-products-----------------------
@app.get("/products")
def get_all_products():
    cursor = conn.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return {"products": products}

#------------------delete-product-----------------------
@app.delete("/products/{product_id}")
def delete_product(product_id: int, token: str):
    requirs_admin(token)
    cursor = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    return {"message": "Product deleted successfully"}

#------------------edit-product-----------------------
@app.put("/products/{product_id}")
def edit_product(product_id: int, product: Products, token: str):
    requirs_admin(token)
    cursor = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    existing_product = cursor.fetchone()
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")

    conn.execute(
        "UPDATE products SET name = ?, description = ?, price = ?, image_url = ? WHERE id = ?",
        (product.name, product.description, product.price, product.image_url, product_id)
    )
    conn.commit()
    return {"message": "Product updated successfully"}

#------------------orders-end-points----------------------
#------------------add-order-----------------------
@app.post("/orders")
def add_order(order: Orders, token: str):
    # Verify the token and get the user ID from it
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Check if the user ID in the token matches the user ID in the order
    if user_id != order.user_id or username != order.username:
        raise HTTPException(status_code=403, detail="You are not authorized to place this order")

    conn.execute(
        "INSERT INTO orders (user_id, username, user_address, product_id, quantity, total_price) VALUES (?, ?, ?, ?, ?, ?)",
        (order.user_id, order.username, order.user_address, order.product_id, order.quantity, order.total_price)
    )
    conn.commit()
    return {"message": "Order placed successfully"}

#------------------get-all-orders-----------------------
@app.get("/orders")
def get_all_orders(token: str):
    requirs_admin(token)
    cursor = conn.execute("SELECT * FROM orders")
    orders = cursor.fetchall()
    return {"orders": orders}

#---------------------edit-order-status----------------------
@app.put("/orders/{order_id}")
def edit_order_status(order_id: int, status: str, token: str):
    requirs_admin(token)

    cursor = conn.execute(
        "SELECT id FROM orders WHERE id = ?",
        (order_id,)
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Order not found")

    conn.execute(
        "UPDATE orders SET order_status = ? WHERE id = ?",
        (status, order_id)
    )
    conn.commit()

    return {"message": "Order status updated successfully"}