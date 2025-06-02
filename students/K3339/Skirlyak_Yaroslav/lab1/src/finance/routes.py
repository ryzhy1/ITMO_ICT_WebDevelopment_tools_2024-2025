from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, func
from typing import List
from ..core.database import get_session
from ..auth.routes import get_current_user
from ..finance.models import User, Category, Transaction, Budget, UserCategory
from ..finance.schemas import (
    CategoryCreate, CategoryRead,
    TransactionCreate, TransactionRead,
    BudgetCreate, BudgetRead,
    ExpenseAnalysisOut, DashboardSummary, SpendingTrend
)
import logging
from datetime import date

router = APIRouter(tags=["finance"])

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Аналитика расходов
@router.get("/analysis/expenses", response_model=List[ExpenseAnalysisOut])
def expense_analysis(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    analysis = (
        db.exec(
            select(Category.name, func.sum(Transaction.amount).label("total_expense"))
            .join(UserCategory, UserCategory.category_id == Category.id)
            .join(Transaction, Transaction.category_id == Category.id)
            .where(UserCategory.user_id == current_user.id, Transaction.type == "expense")
            .group_by(Category.name)
        ).all()
    )
    return [{"category": row[0], "total_expense": row[1]} for row in analysis]

# Обзор дашборда
@router.get("/dashboard", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    total_income = db.exec(
        select(func.sum(Transaction.amount))
        .where(Transaction.user_id == current_user.id, Transaction.type == "income")
    ).first() or 0.0
    total_expense = db.exec(
        select(func.sum(Transaction.amount))
        .where(Transaction.user_id == current_user.id, Transaction.type == "expense")
    ).first() or 0.0
    net_savings = total_income - total_expense
    return {"total_income": total_income, "total_expense": total_expense, "net_savings": net_savings}

# Тренды расходов
@router.get("/trends/spending", response_model=List[SpendingTrend])
def spending_trends(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    trends = db.exec(
        select(func.strftime("%Y-%m", Transaction.date).label("month"), func.sum(Transaction.amount).label("total_expense"))
        .where(Transaction.user_id == current_user.id, Transaction.type == "expense")
        .group_by(func.strftime("%Y-%m", Transaction.date))
        .order_by(func.strftime("%Y-%m", Transaction.date))
    ).all()
    return [{"month": row[0], "total_expense": row[1]} for row in trends]

@router.post("/categories", response_model=CategoryRead)
def create_category(category: CategoryCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    user_category = UserCategory(user_id=current_user.id, category_id=db_category.id, is_default=False)
    db.add(user_category)
    db.commit()
    return db_category

@router.get("/categories", response_model=List[CategoryRead])
def read_categories(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    categories = db.exec(
        select(Category)
        .join(UserCategory)
        .where(UserCategory.user_id == current_user.id)
    ).all()
    return categories

@router.put("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: int, category: CategoryCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_category = db.exec(
        select(Category)
        .join(UserCategory)
        .where(Category.id == category_id, UserCategory.user_id == current_user.id)
    ).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_category = db.exec(
        select(Category)
        .join(UserCategory)
        .where(Category.id == category_id, UserCategory.user_id == current_user.id)
    ).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(db_category)
    db.commit()
    return {"detail": "Category deleted"}

@router.post("/transactions", response_model=TransactionRead)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    user_category = db.exec(
        select(UserCategory).where(
            UserCategory.user_id == current_user.id,
            UserCategory.category_id == transaction.category_id,
        )
    ).first()
    if not user_category:
        raise HTTPException(status_code=403, detail="Access to category denied")

    data = transaction.dict()
    data.pop("user_id", None)

    db_transaction = Transaction(**data, user_id=current_user.id)

    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.get("/transactions", response_model=List[TransactionRead])
def read_transactions(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    transactions = db.exec(
        select(Transaction).where(Transaction.user_id == current_user.id)
    ).all()
    return transactions

@router.put("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, transaction: TransactionCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_transaction = db.exec(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    ).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    user_category = db.exec(
        select(UserCategory)
        .where(UserCategory.user_id == current_user.id, UserCategory.category_id == transaction.category_id)
    ).first()
    if not user_category:
        raise HTTPException(status_code=403, detail="Access to category denied")
    for key, value in transaction.dict().items():
        setattr(db_transaction, key, value)
    db_transaction.user_id = current_user.id
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@router.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_transaction = db.exec(
        select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)
    ).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(db_transaction)
    db.commit()
    return {"detail": "Transaction deleted"}

@router.post("/budgets", response_model=BudgetRead)
def create_budget(budget: BudgetCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user_category = db.exec(
        select(UserCategory)
        .where(UserCategory.user_id == current_user.id, UserCategory.category_id == budget.category_id)
    ).first()
    if not user_category:
        raise HTTPException(status_code=403, detail="Access to category denied")
    db_budget = Budget(**budget.dict(), user_id=current_user.id)
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.get("/budgets", response_model=List[BudgetRead])
def read_budgets(db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    budgets = db.exec(
        select(Budget).where(Budget.user_id == current_user.id)
    ).all()
    return budgets

@router.put("/budgets/{budget_id}", response_model=BudgetRead)
def update_budget(budget_id: int, budget: BudgetCreate, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_budget = db.exec(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    ).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    user_category = db.exec(
        select(UserCategory)
        .where(UserCategory.user_id == current_user.id, UserCategory.category_id == budget.category_id)
    ).first()
    if not user_category:
        raise HTTPException(status_code=403, detail="Access to category denied")
    for key, value in budget.dict().items():
        setattr(db_budget, key, value)
    db_budget.user_id = current_user.id
    db.commit()
    db.refresh(db_budget)
    return db_budget

@router.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, db: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    db_budget = db.exec(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == current_user.id)
    ).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    db.delete(db_budget)
    db.commit()
    return {"detail": "Budget deleted"}