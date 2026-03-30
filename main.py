import yfinance as yf
from database import engine,Base, SessionLocal
import models
from models import User
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import json
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

Base.metadata.create_all(bind=engine)
app = FastAPI()

templates = Jinja2Templates(directory="templates")

# --- HELPERS ---
#database session for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#S&P 500 graph plotter
def create_sp500_chart():
    df = yf.Ticker("^GSPC").history(period="2y").reset_index()
    fig = go.Figure(go.Scatter(x=list(df.Date), y=list(df.Close), name="S&P 500"))

    fig.update_layout(
        title_text="S&P 500 Performance Analysis",
        template="plotly_white",
        xaxis=dict(
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(step="all")
                ]
            ),
            rangeslider=dict(visible=True),
            type="date"
        )
    )

    # Get stats for the navbar
    current = round(df['Close'].iloc[-1], 2)
    prev = round(df['Close'].iloc[-2], 2)
    stats = {"price": current, "change": round(current - prev, 2)}

    return pio.to_json(fig), stats

#--- Routes ---
#Default home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = "Guest"):
    # If a user is already "logged in", send them straight to the dashboard
    if username and username != "Guest":
        return RedirectResponse(url=f"/dashboard?username={username}")

    graph_json, stats = create_sp500_chart()

    return templates.TemplateResponse(request=request,name="base_layout.html", context={
        "request": request,
        "username": "Guest",
        "graph_json": graph_json,
        "market_data": {"name": "S&P 500", **stats}
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = "Guest"):
    db = SessionLocal()

    user = db.query(User).filter(User.username == username).first()
    db.close()

    if not user:
        return RedirectResponse(url="/login")

    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "request": request,
        "username": username,
        "balance": user.balance
    })

#Login Page Layout
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login_page.html",
        context={"request": request}
    )
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    # Look for the user in the database file
    user = db.query(User).filter(User.username == username).first()
    db.close()

    if user and user.password == password:
        # Instead of just text, we tell HTMX to trigger a redirect
        # HX-Redirect is a special header HTMX understands
        response = HTMLResponse(content="Logging in...")
        response.headers["HX-Redirect"] = f"/dashboard?username={user.username}"
        return response

    return "<div style='color: red;'>Invalid username or password.</div>"

#Logout logic for now, it works fine without this for some reason. Guessing html somehow already takes care of it
@app.get("/logout")
async def logout():
    # In the future, this is where you would delete the Session Cookie
    # For now, we just redirect to the main landing page
    return RedirectResponse(url="/")



