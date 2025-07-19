from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import boto3
import os
from dotenv import load_dotenv
import bcrypt  # ✅ NEW

# Load env variables
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Connect to DynamoDB
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Get table name from env
table_name = os.getenv("DYNAMODB_TABLE_NAME")
table = dynamodb.Table(table_name)


# ▶ Home Page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# ▶ Show Register Page
@app.get("/register", response_class=HTMLResponse)
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# ▶ Handle Register Form
@app.post("/register", response_class=HTMLResponse)
async def register_user(
    request: Request,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    # ✅ Hash password before saving
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    full_name = f"{first_name} {last_name}"

    # ✅ Save to DynamoDB
    table.put_item(Item={
        "email": email,
        "name": full_name,
        "password": hashed_password
    })

    return templates.TemplateResponse("register.html", {
        "request": request,
        "message": "✅ Registration successful! Password is secured."
    })
