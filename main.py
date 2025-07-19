from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import boto3
import os
from dotenv import load_dotenv
import bcrypt

# Load environment variables from .env
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

# Connect to DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Load the table
table_name = os.getenv("DYNAMODB_TABLE_NAME")
table = dynamodb.Table(table_name)


# ▶ Home Page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ▶ Register Page
@app.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# ▶ Register Form Submission
@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    # Check for existing user
    existing_user = table.get_item(Key={"email": email}).get("Item")
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "❌ Email already exists. Please use another."
        })

    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Save user to DynamoDB
    table.put_item(Item={
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "password": hashed_password
    })

    return templates.TemplateResponse("register.html", {
        "request": request,
        "message": "✅ Registration successful! Please login."
    })


# ▶ Login Page
@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


# ▶ Handle Login
@app.post("/login", response_class=HTMLResponse)
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    # Fetch user
    response = table.get_item(Key={"email": email})
    user = response.get("Item")

    if user:
        hashed_pw = user.get("password")
        if bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            first_name = user.get("first_name", "User")
            last_name = user.get("last_name", "")
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "first_name": first_name,
                "last_name": last_name,
                "email": email
            })

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "❌ Invalid email or password"
    })



# ▶ Update Profile Info
@app.post("/update-profile", response_class=HTMLResponse)
async def update_profile(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...)
):
    # Update DynamoDB item
    try:
        table.update_item(
            Key={"email": email},
            UpdateExpression="SET first_name = :f, last_name = :l",
            ExpressionAttributeValues={
                ":f": first_name,
                ":l": last_name
            }
        )
        message = "✅ Profile updated successfully!"
    except Exception as e:
        print("Error updating profile:", str(e))
        message = "❌ Failed to update profile"

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "message": message
    })
