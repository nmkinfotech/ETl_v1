# Monday ETL Tool

A simple Windsor.ai–style ETL tool built with **Python + FastAPI**.
It extracts data from **Monday.com** and loads it into **SQL Server (SSMS)**.
The app is designed to be extended for more sources (HubSpot, Facebook Ads, etc.) and destinations.

---

## 🚀 Features

* Web-based interface (FastAPI + Jinja2 templates).
* Step-by-step flow:

  1. Select **Source** (e.g., Monday.com).
  2. Enter **Source details** (API Key, Board ID, etc.).
  3. Select **Destination** (e.g., SQL Server).
  4. Enter **Destination details** (connection string, credentials).
  5. Run ETL → data is loaded into SQL Server.
* Modular: easy to add new sources and destinations.

---

## 📂 Project Structure

```
monday-etl-tool/
│── app.py              # FastAPI app with routes
│── monday_client.py    # Extract from Monday.com
│── transformer.py      # Transform JSON → DataFrame
│── loader.py           # Load DataFrame → SQL Server
│── config.py           # Global configurations
│── requirements.txt    # Python dependencies
│── templates/          # HTML pages
│    ├── index.html         # Home page (select source)
│    ├── source_monday.html # Source details (Monday)
│    ├── destination.html   # Select destination
│    └── destination_sql.html # SQL Server destination details
```

---

## ⚙️ Installation

1. Clone or unzip this repo:

   ```bash
   unzip monday-etl-tool.zip
   cd monday-etl-tool
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Linux/Mac
   venv\Scripts\activate      # On Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## ▶️ Run the App

```bash
uvicorn app:app --reload
```

Visit: **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in your browser.

---

## 🛠️ Example SQL Server Connection String

```text
mssql+pyodbc://username:password@SERVER_NAME/DB_NAME?driver=ODBC+Driver+17+for+SQL+Server
```

---

## 🔮 Next Steps

* Add support for **HubSpot, Facebook Ads** as new sources.
* Add **Google BigQuery, Snowflake** as destinations.
* Support **incremental refresh** (currently full refresh).
* Add **user authentication**.

---

## 📜 License

MIT License
