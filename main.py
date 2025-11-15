import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents

app = FastAPI(title="Retro Diet Quest API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility to convert ObjectId to str

def to_str_id(doc: dict):
    if doc is None:
        return None
    d = dict(doc)
    if "_id" in d:
        d["_id"] = str(d["_id"])
    return d

# Diet plan generator logic

def get_diet_plan_for_age(age: int) -> List[dict]:
    # Simplified sample diet plan per age band
    bands = [
        (13, 17, {
            "calories": "2200-2600",
            "focus": ["growth", "protein", "calcium"],
            "meals": [
                {"name": "Breakfast", "items": ["Oats + milk", "Banana", "Boiled eggs"]},
                {"name": "Lunch", "items": ["Whole-grain roti/rice", "Dal/beans", "Chicken/tofu", "Salad"]},
                {"name": "Snack", "items": ["Fruit yogurt", "Nuts"]},
                {"name": "Dinner", "items": ["Rice/roti", "Paneer/fish", "Veg stir-fry"]},
            ],
        }),
        (18, 29, {
            "calories": "2000-2400",
            "focus": ["lean protein", "complex carbs", "hydration"],
            "meals": [
                {"name": "Breakfast", "items": ["Egg sandwich", "Orange", "Black coffee/tea"]},
                {"name": "Lunch", "items": ["Brown rice", "Grilled chicken/chickpeas", "Mixed veggies"]},
                {"name": "Snack", "items": ["Apple", "Peanut butter"]},
                {"name": "Dinner", "items": ["Quinoa", "Fish/tofu", "Soup"]},
            ],
        }),
        (30, 45, {
            "calories": "1800-2200",
            "focus": ["fiber", "heart health", "balanced macros"],
            "meals": [
                {"name": "Breakfast", "items": ["Greek yogurt", "Berries", "Granola"]},
                {"name": "Lunch", "items": ["Millet/brown rice", "Beans/lentils", "Veg curry"]},
                {"name": "Snack", "items": ["Carrot sticks", "Hummus"]},
                {"name": "Dinner", "items": ["Whole-wheat roti", "Paneer/chicken", "Salad"]},
            ],
        }),
        (46, 59, {
            "calories": "1600-2000",
            "focus": ["bone health", "iron", "vitamin D"],
            "meals": [
                {"name": "Breakfast", "items": ["Veg omelette", "Toast", "Papaya"]},
                {"name": "Lunch", "items": ["Brown rice", "Dal", "Sauteed greens"]},
                {"name": "Snack", "items": ["Buttermilk", "Almonds"]},
                {"name": "Dinner", "items": ["Soup", "Grilled fish/tofu", "Veg salad"]},
            ],
        }),
        (60, 70, {
            "calories": "1500-1900",
            "focus": ["easy-to-digest", "protein", "hydration"],
            "meals": [
                {"name": "Breakfast", "items": ["Poha/upma", "Milk", "Soft fruit"]},
                {"name": "Lunch", "items": ["Rice/roti", "Moong dal", "Curd", "Cooked veggies"]},
                {"name": "Snack", "items": ["Banana shake", "Walnuts"]},
                {"name": "Dinner", "items": ["Khichdi", "Steamed veg", "Soup"]},
            ],
        }),
    ]
    for lo, hi, plan in bands:
        if lo <= age <= hi:
            return plan
    raise HTTPException(status_code=400, detail="Age must be between 13 and 70")

# Request models
class ProfileCreate(BaseModel):
    name: str
    age: int

class TaskCreate(BaseModel):
    user_id: str
    title: str
    day: Optional[str] = None
    xp_value: int = 10

class TaskToggle(BaseModel):
    completed: bool

@app.get("/")
def read_root():
    return {"message": "Retro Diet Quest API running"}

@app.get("/api/diet-plan/{age}")
def diet_plan(age: int):
    return get_diet_plan_for_age(age)

@app.post("/api/profile")
def create_profile(body: ProfileCreate):
    if not (13 <= body.age <= 70):
        raise HTTPException(status_code=400, detail="Age must be between 13 and 70")
    from schemas import Userprofile
    profile = Userprofile(name=body.name, age=body.age)
    new_id = create_document("userprofile", profile)
    doc = db["userprofile"].find_one({"_id": ObjectId(new_id)})
    return to_str_id(doc)

@app.get("/api/profile/{user_id}")
def get_profile(user_id: str):
    try:
        doc = db["userprofile"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    return to_str_id(doc)

@app.get("/api/profile/{user_id}/tasks")
def list_tasks(user_id: str):
    tasks = get_documents("task", {"user_id": user_id})
    return [to_str_id(t) for t in tasks]

@app.post("/api/tasks")
def add_task(body: TaskCreate):
    from schemas import Task
    # basic existence check for user
    try:
        _ = db["userprofile"].find_one({"_id": ObjectId(body.user_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user id")
    task = Task(user_id=body.user_id, title=body.title, day=body.day, xp_value=body.xp_value)
    new_id = create_document("task", task)
    doc = db["task"].find_one({"_id": ObjectId(new_id)})
    return to_str_id(doc)

@app.patch("/api/tasks/{task_id}")
def toggle_task(task_id: str, body: TaskToggle):
    try:
        oid = ObjectId(task_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid task id")
    res = db["task"].find_one_and_update({"_id": oid}, {"$set": {"completed": body.completed, "updated_at": None}}, return_document=True)
    doc = db["task"].find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")
    # Increment XP and possibly level up when a task is completed
    if body.completed:
        task = doc
        user_id = task.get("user_id")
        if user_id:
            db["userprofile"].update_one({"_id": ObjectId(user_id)}, {"$inc": {"xp": task.get("xp_value", 10)}})
    return to_str_id(doc)

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
