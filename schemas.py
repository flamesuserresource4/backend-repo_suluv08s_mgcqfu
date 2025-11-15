"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Existing example schemas (kept for reference)
class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# App-specific schemas
class Userprofile(BaseModel):
    """
    User profiles for the diet planner app
    Collection name: "userprofile"
    """
    name: str = Field(..., description="Display name")
    age: int = Field(..., ge=13, le=70, description="Age (13-70)")
    level: int = Field(1, ge=1, description="Gamified level")
    xp: int = Field(0, ge=0, description="Experience points")

class Task(BaseModel):
    """
    Tasks assigned or added by users
    Collection name: "task"
    """
    user_id: str = Field(..., description="Related userprofile _id as string")
    title: str = Field(..., description="Task title")
    day: Optional[str] = Field(None, description="Optional day label, e.g., 2025-11-15")
    completed: bool = Field(False, description="Whether the task is completed")
    xp_value: int = Field(10, ge=0, description="XP earned upon completion")
