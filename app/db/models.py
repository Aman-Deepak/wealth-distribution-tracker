from decimal import Decimal
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import DECIMAL, Column, Integer, String, ForeignKey, Date, DateTime, UniqueConstraint, DECIMAL
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from sqlalchemy import Column, String

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)


    incomes = relationship("Income", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
    investments = relationship("Invest", back_populates="user")
    interests = relationship("Interest", back_populates="user")
    loans = relationship("Loan", back_populates="user")
    savings = relationship("Savings", back_populates="user")
    configs = relationship("Config", back_populates="user")
    uploads = relationship("UploadHistory", back_populates="user")
    yearly_closing_balances = relationship("YearlyClosingBankBalance", back_populates="user")


class Income(Base):
    __tablename__ = "income"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10))
    year = Column(String(4))
    month = Column(String(2))
    day = Column(String(2))
    salary = Column(DECIMAL(14, 4))
    tax = Column(DECIMAL(14, 4))

    user = relationship("User", back_populates="incomes")

class Expense(Base):
    __tablename__ = "expense"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10))
    year = Column(String(4))
    month = Column(String(2))
    day = Column(String(2))
    type = Column(String(20))
    category = Column(String(50))
    cost = Column(DECIMAL(14, 4))

    user = relationship("User", back_populates="expenses")

class Invest(Base):
    __tablename__ = "invest"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10))
    year = Column(String(4))
    month = Column(String(2))
    day = Column(String(2))
    type = Column(String(20))
    folio_number = Column(String(20))
    name = Column(String(50))
    type_of_order = Column(String(5))
    units = Column(DECIMAL(14, 4))
    nav = Column(DECIMAL(14, 4))
    cost = Column(DECIMAL(14, 4))

    user = relationship("User", back_populates="investments")

class Interest(Base):
    __tablename__ = "interest"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10))
    year = Column(String(4))
    month = Column(String(2))
    day = Column(String(2))
    type = Column(String(20))
    name = Column(String(100))
    cost_in = Column(DECIMAL(14, 4))
    cost_out = Column(DECIMAL(14, 4))

    user = relationship("User", back_populates="interests")

class Loan(Base):
    __tablename__ = "loan"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10))
    year = Column(String(4))
    month = Column(String(2))
    day = Column(String(2))
    type = Column(String(50))
    name = Column(String(100))
    interest = Column(DECIMAL(14, 4))
    loan_amount = Column(DECIMAL(14, 4))
    loan_repayment = Column(DECIMAL(14, 4))
    cost = Column(DECIMAL(14, 4))

    user = relationship("User", back_populates="loans")

class Savings(Base):
    __tablename__ = "savings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    type = Column(String(20))
    name = Column(String(50))
    t_buy = Column(DECIMAL(14, 4))
    t_sell = Column(DECIMAL(14, 4))
    profit_booked = Column(DECIMAL(14, 4))
    current_invested = Column(DECIMAL(14, 4))
    current_value = Column(DECIMAL(14, 4))
    profit_loss = Column(DECIMAL(14, 4))
    return_percentage = Column(DECIMAL(14, 4))

    user = relationship("User", back_populates="savings")
    __table_args__ = (UniqueConstraint("user_id", "name", name="UC_UserSavingsName"),)

class MonthlyDistribution(Base):
    __tablename__ = "monthly_distribution"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10))
    year = Column(String(4))
    month = Column(String(20))
    income = Column(DECIMAL(14, 4))
    inv_buy = Column(DECIMAL(14, 4))
    inv_sell = Column(DECIMAL(14, 4))
    expenses = Column(DECIMAL(14, 4))
    bank = Column(DECIMAL(14, 4))
    tax = Column(DECIMAL(14, 4))
    interest_in = Column(DECIMAL(14, 4))
    interest_out = Column(DECIMAL(14, 4))
    loan_amount = Column(DECIMAL(14, 4))
    loan_repayment = Column(DECIMAL(14, 4))

    __table_args__ = (UniqueConstraint("user_id", "year", "month", name="UC_UserYearMonth"),)

class YearlyDistribution(Base):
    __tablename__ = "yearly_distribution"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10))
    income = Column(DECIMAL(14, 4))
    inv_buy = Column(DECIMAL(14, 4))
    inv_sell = Column(DECIMAL(14, 4))
    expenses = Column(DECIMAL(14, 4))
    bank = Column(DECIMAL(14, 4))
    tax = Column(DECIMAL(14, 4))
    interest_in = Column(DECIMAL(14, 4))
    interest_out = Column(DECIMAL(14, 4))
    loan_amount = Column(DECIMAL(14, 4))
    loan_repayment = Column(DECIMAL(14, 4))

    __table_args__ = (UniqueConstraint("user_id", "financial_year", name="UC_UserYearly"),)

class Config(Base):
    __tablename__ = "configs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    last_updated_date = Column(Date)
    invest_last_updated_date = Column(Date)
    expense_last_updated_date = Column(Date)
    financial_last_updated_date = Column(Date)

    user = relationship("User", back_populates="configs")
    __table_args__ = (UniqueConstraint("user_id", name="UC_UserConfig"),)


class UploadHistory(Base):
    __tablename__ = "upload_history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    filename = Column(String(255))
    file_type = Column(String(50))
    upload_time = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="uploads")


class NAV(Base):
    __tablename__ = "navs"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # e.g., MUTUALFUND, STOCK
    fund_name = Column(String(255), nullable=False)
    unique_identifier = Column(String(100), nullable=False)  # ISIN, AMFI Code, Ticker
    nav = Column(DECIMAL(14, 4), nullable=True)
    last_updated = Column(DateTime, nullable=True)

    __table_args__ = (UniqueConstraint("unique_identifier", name="UC_FundUnique"),)

class YearlyClosingBankBalance(Base):
    __tablename__ = "yearly_closing_bank_balance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    financial_year = Column(String(10), nullable=False)
    closing_balance = Column(DECIMAL(14, 4), nullable=False)

    user = relationship("User", back_populates="yearly_closing_balances")

