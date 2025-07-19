from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import boto3
import os
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Set up Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

# Connect to DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Get the table
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


# ▶ Register Submission with duplicate check
@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    # Check if user already exists
    existing_user = table.get_item(Key={"email": email}).get("Item")
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "❌ Email already exists. Please login or use another email."
        })

    # Hash the password
    full_name = f"{first_name} {last_name}"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Save to DynamoDB
    table.put_item(Item={
        "email": email,
        "name": full_name,
        "password": hashed_password
    })

    return templates.TemplateResponse("register.html", {
        "request": request,
        "message": "✅ Registration successful!"
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
    # Fetch user from DynamoDB
    response = table.get_item(Key={"email": email})
    user = response.get("Item")

    if user:
        hashed_pw = user.get("password")
        if bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            full_name = user.get("name", "User")
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "name": full_name,
                "email": email
            })

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": "❌ Invalid email or password"
    })
