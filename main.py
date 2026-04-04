from database import engine,Base, SessionLocal
import uvicorn
import models
from models import User, Portfolio
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import yfinance as yf
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

app = FastAPI()

templates = Jinja2Templates(directory="templates")

print("Connecting to database...")
Base.metadata.create_all(bind=engine)
print("Database tables created successfully!")
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

    # Get stats for the index
    current = round(df['Close'].iloc[-1], 2)
    prev = round(df['Close'].iloc[-2], 2)
    stats = {"price": current, "change": round(current - prev, 2)}

    return pio.to_json(fig), stats


def get_index_stats(ticker_symbol, period="2d"):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)

    if hist.empty or len(hist) < 2:
        return None

    current_price = hist['Close'].iloc[-1]
    start_price = hist['Close'].iloc[0]  # Price at the start of the 1D, 5D, etc.

    change = current_price - start_price
    percent = (change / start_price) * 100

    return {
        "price": round(current_price, 2),
        "change": round(change, 2),
        "percent": round(percent, 2),
        "color": "green" if change >= 0 else "red",
        "ticker": ticker_symbol
    }

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

#Dashboard functions
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

#Index Page Layout
@app.get("/indexes", response_class=HTMLResponse)
async def indexes_page(request: Request, username: str = "Guest"):
    if username == "Guest":
        return RedirectResponse(url="/login")

    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    db.close()

    # Define indexes and fetch live data for them
    index_list = [{"name": "S&P 500", "ticker": "^GSPC","safe_id":"GSPC", "desc": "Top 500 US Companies"},]

    # Add live data to each index dictionary
    for idx in index_list:
        market_info = get_index_stats(idx["ticker"])
        idx.update(market_info) # Merges the price/change into the dict

    return templates.TemplateResponse(request=request,name="indexes.html", context={
        "request": request,
        "username": username,
        "balance": user.balance,
        "indexes": index_list
    })
#Function for the partial HTMX template
@app.get("/api/index-stats/{ticker}")
async def update_index_stats(request: Request, ticker: str, period: str = "2d"):
    stats = get_index_stats(ticker, period)
    # Strip the ^ for the template context
    safe_id = ticker.replace("^", "")
    return templates.TemplateResponse(
        request=request,
        name="partials/index_price_display.html",
        context={
            "request": request,
            "stats": stats,
            "safe_id": safe_id
        }
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)