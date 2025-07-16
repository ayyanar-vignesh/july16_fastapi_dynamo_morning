from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Setup Jinja2 templates directory
templates = Jinja2Templates(directory="templates")

# DynamoDB setup
dynamodb = boto3.resource(
    'dynamodb',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

# Get table name from .env
table_name = os.getenv("DYNAMODB_TABLE_NAME")
table = dynamodb.Table(table_name)

# Show form page
@app.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Handle form submission
@app.post("/submit/", response_class=HTMLResponse)
async def submit_form(request: Request, name: str = Form(...), email: str = Form(...)):
    # Insert into DynamoDB
    response = table.put_item(Item={"name": name, "email": email})
    print(name,email)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": "✅ Data submitted successfully!"
    })

