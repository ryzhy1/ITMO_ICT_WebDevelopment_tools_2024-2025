from sqlmodel import SQLModel
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(SQLModel):
    username: str
    email: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

class UserChangePassword(SQLModel):
    old_password: str
    new_password: str

class Token(SQLModel):
    access_token: str
    token_type: str

class CategoryBase(SQLModel):
    name: str

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: int
    users: List[UserRead] = []

class UserCategoryCreate(SQLModel):
    user_id: int
    category_id: int
    is_default: bool = False

class TransactionBase(SQLModel):
    amount: float
    type: str
    description: Optional[str] = None
    date: datetime

class TransactionCreate(TransactionBase):
    user_id: int
    category_id: int

class TransactionRead(TransactionBase):
    id: int
    user: Optional[UserRead] = None
    category: Optional[CategoryRead] = None

class BudgetBase(SQLModel):
    amount: float
    period_start: datetime
    period_end: datetime

class BudgetCreate(BudgetBase):
    user_id: int
    category_id: int

class BudgetRead(BudgetBase):
    id: int
    user: Optional[UserRead] = None
    category: Optional[CategoryRead] = None

class ExpenseAnalysisOut(SQLModel):
    category: str
    total_expense: float

class DashboardSummary(SQLModel):
    total_income: float
    total_expense: float
    net_savings: float

class SpendingTrend(SQLModel):
    month: str
    total_expense: float

class ParseRequest(BaseModel):
    urls: List[str]