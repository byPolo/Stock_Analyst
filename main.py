from fastapi import FastAPI, HTTPException

app = FastAPI()

# Test database for users todo integrate actual database later
db_users = {
    "admin_user": {
        "username": "admin_Polo",
        "email": "admin@stockanalyst.com",
        "full_name": "Polo admin",
        "is_admin": True,
        "balance": 1000000.0,
    },
    "test_trader": {
        "username": "trader_joe",
        "email": "joe@example.com",
        "full_name": "Joe Trader",
        "is_admin": False,
        "balance": 10000.0,
    }
}

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/admin/users")
async def get_all_users():
    # In a real app, you'd check if the requester 'is_admin' here
    return db_users

@app.get("/users/{username}")
async def get_user(username: str):
    if username not in db_users:
        raise HTTPException(status_code=404, detail="User not found")
    return db_users[username]
@app.get("/")
async def root():
    return {"message": "Hello World"}

