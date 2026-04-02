from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from database import Base

class User(Base):
    __tablename__ = "users" # This is the actual name inside the SQL file

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String)
    balance = Column(Float, default=10000.0)
    is_admin = Column(Boolean, default=False)

class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticker = Column(String)
    shares = Column(Float)
    avg_price = Column(Float)



