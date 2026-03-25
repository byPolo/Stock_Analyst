import yfinance as yf
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="templates")
# Test database for users todo integrate actual database later
db_users = {
    "admin_Polo": {
        "username": "admin_Polo",
        "password": "Polo123",
        "email": "admin@stockanalyst.com",
        "full_name": "Polo admin",
        "is_admin": True,
        "balance": 1000000.0,
    },
    "trader_joe": {
        "username": "trader_joe",
        "password": "123",
        "email": "joe@example.com",
        "full_name": "Joe Trader",
        "is_admin": False,
        "balance": 10000.0,
    }
}
#Default home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, username: str = "Guest"):
    # 1. Fetch Real Market Data for S&P 500
    sp500 = yf.Ticker("^GSPC")
    data = sp500.history(period="1d")
    price = round(data['Close'].iloc[-1], 2)

    # Get the latest closing price and the change
    current_price = round(data['Close'].iloc[-1], 2)
    prev_close = sp500.info.get('previousClose', current_price)
    change = round(current_price - prev_close, 2)
    change_percent = round((change / prev_close) * 100, 2)

    #Not sure if its smart to have the logic here for a logged in user, maybe in the future it is better to have it in its separate .get
    user_data = db_users.get(username)
    if username != "Guest":
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "username": username,
                "is_logged_in": user_data is not None,
                "balance": user_data.get("balance") if user_data else 0,
                "market_data": {
                    "name": "S&P 500",
                    "price": current_price,
                    "change": change,
                    "percent": change_percent
                }
            }
        )

    return templates.TemplateResponse(request=request, name="base_layout.html", context={
        "request": request,
        "username": "Guest",
        "market_data": {
                    "name": "S&P 500",
                    "price": current_price,
                    "change": change,
                    "percent": change_percent
                }
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = "Guest"):
    # In a real app, we'd get the user data from a session or cookie
    user = db_users.get(username, {"balance": 0})
    return templates.TemplateResponse(request=request, name="dashboard.html", context={
        "request": request,
        "username": username,
        "balance": user.get("balance")
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
    # Check if user exists and password matches
    user_data = db_users.get(username)

    if user_data and user_data["password"] == password:
        # Instead of just text, we tell HTMX to trigger a redirect
        # HX-Redirect is a special header HTMX understands
        response = HTMLResponse(content="Logging in...")
        response.headers["HX-Redirect"] = f"/dashboard?username={username}"
        return response

    return "<div style='color: red;'>Invalid username or password.</div>"


#Users in the fictional Database
@app.get("/admin/users")
async def get_all_users():
    # In a real app, you'd check if the requester 'is_admin' here
    return db_users

@app.get("/users/{username}")
async def get_user(username: str):
    if username not in db_users:
        raise HTTPException(status_code=404, detail="User not found")
    return db_users[username]


