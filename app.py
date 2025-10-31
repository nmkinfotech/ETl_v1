from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os
import requests
import uuid
import pandas as pd

from sources.monday_client import get_board_items
from transformers.transformer_monday import board_to_dataframe
from destinations.sqlserver_loader_monday import load_to_sql_monday_api

from sources.hubspot_client import get_hubspot_data
from destinations.sqlserver_loader_hubspot import load_to_sql_hubspot_api
from transformers.transformer_hubspot import hubspot_response_to_dataframe

## Global Dataframe
server_store = {}

# Load environment variables from .env file
load_dotenv()

# Get secret key securely
SESSION_SECRET_KEY = os.getenv("SECRET_KEY")


app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key = SESSION_SECRET_KEY)

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def select_source(request: Request):
    return templates.TemplateResponse("source_select.html", {"request":request})



'''Monday Helpers'''

@app.get("/config/monday", response_class=HTMLResponse)
async def config_monday(request: Request):
    return templates.TemplateResponse("source_config_monday.html", {"request": request})

@app.post("/config/monday")
async def submit_monday(request:Request ,api_key: str = Form(...), board_id: int = Form(...)):
    request.session["api_name"] ="monday"

    board_data, columns = get_board_items(api_key, int(board_id))
    df = board_to_dataframe(board_data,columns)
    table_html = df.to_html(classes="table table-striped", index=False)

    session_ref = str(uuid.uuid4())
    server_store[session_ref] = df
    request.session["session_ref"] = session_ref

    return RedirectResponse(url="/select_destination", status_code=303)

    # return templates.TemplateResponse("preview.html", {
    #     "request":request,
    #     "dataframe" : table_html
    # })

@app.get("/select_destination", response_class=HTMLResponse)
async def select_destination(request: Request):
    return templates.TemplateResponse("destination_select.html",{
        "request":request
    })


@app.get("/config/sqlserver", response_class=HTMLResponse)
async def config_sqlserver(request: Request):
    return templates.TemplateResponse("destination_config_sqlserver.html",{
        "request":request
    })   

@app.post("/config/sqlserver")
async def submit_sqlserver(request:Request):

    form = await request.form()
    Driver = form.get("driver_number")
    Server = form.get("server")
    Database = form.get("database")
    Username = form.get("username")
    Password = form.get("password")
    table_name_from_user = form.get("table_name")
    LOAD_MODE = form.get("load_mode")
    session_ref = request.session.get("session_ref")

    print(LOAD_MODE)
    connection_string=''

    driver_string=f"{{ODBC Driver {Driver} for Sql Server}}"
    if Username:
        connection_string=f"DRIVER={driver_string};SERVER={Server};DATABASE={Database};UID={username};PWD={password};"
    else:
        connection_string=f"DRIVER={driver_string};SERVER={Server};DATABASE={Database};Trusted_Connection=yes;"

    api_response = server_store[session_ref]
    rows_written=0
    table_count = 0
    api_name = request.session.get("api_name")

    if  api_name == "monday":
        table_count+=1
        df = pd.DataFrame(api_response)
        rows_written = load_to_sql_monday_api(df, table_name_from_user, connection_string, LOAD_MODE)

    elif api_name == "hubspot":
        for endpoint , response in api_response.items():
            if not response:
                continue
            table_name =  table_name_from_user + "_" + endpoint.rsplit("/", 1)[-1]
            table_count+=1
            normalize_json = pd.json_normalize(response)
            df = pd.DataFrame(normalize_json)
            rows_written+=load_to_sql_hubspot_api(df, table_name, connection_string, LOAD_MODE)
    if table_count==1:
        formatted_table_name = f"{table_count} table"
    elif table_count>1:
        formatted_table_name = f"{table_count} tables"
    return templates.TemplateResponse("success.html", {
        "request": {}, "rows_loaded":rows_written, "table_name": formatted_table_name, "load_mode":LOAD_MODE
    })


'''HubSpot Helpers'''

@app.get("/config/hubspot",response_class=HTMLResponse)
async def config_hubspot(request:Request):
    return templates.TemplateResponse(
        "source_config_hubspot.html", {"request":request}
    )

@app.post("/config/hubspot", response_class=HTMLResponse)
async def submit_hubspot(request:Request ,api_key: str = Form(...)):

    # request.session["api_key"] = api_key
    request.session["api_name"] = "hubspot"
    request.session["api_key"] = api_key

    headers = {"Authorization": f"Bearer {api_key}"}
    test_url = "https://api.hubapi.com/crm/v3/objects/tickets?limit=1"

    response = requests.get(test_url, headers=headers)

    if response.status_code == 200:

        return templates.TemplateResponse(
            "endpoints_hubspot.html", {"request":{}}
        )
    else:
        # ❌ Invalid key — return error page
        return templates.TemplateResponse(
            "source_config_hubspot.html",
            {"request":{} ,"error": "Invalid HubSpot API key. Please try again."},
        )

@app.post("/endpoints")
async def extract_endpoints(request:Request):
    form_data = await request.form()
    api_key = request.session.get("api_key")
    endpoints = form_data.getlist("endpoints")

    api_response = get_hubspot_data(api_key,endpoints)
    session_ref = str(uuid.uuid4()) 
    server_store[session_ref] = api_response
    request.session["session_ref"] = session_ref    

    return templates.TemplateResponse("destination_select.html",{
        "request":request,
    })