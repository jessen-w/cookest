# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import main 

app = FastAPI()

class TaskModel(BaseModel):
    name: str
    task_type: str  # Example: "chop", "fry", "steam"
    duration: int   # Duration in minutes
    sequence: int   # Order in the sequence for the dish

tasks = []

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/add_task/", response_model=dict)
def add_task(task: TaskModel):
    # Check if task_type is valid
    if task.task_type not in ["chop", "fry", "wash", "steam"]:  # Adjust task types as needed
        raise HTTPException(status_code=400, detail="Invalid task_type. Must be 'chop', 'fry', 'wash', or 'steam'")
    
    # Append the task to our task list
    tasks.append(task.dict())
    return {"status": "Task added successfully", "task": task.dict()}

@app.post("/run_optimizer/")
def run_optimizer():
    if not tasks:
        raise HTTPException(status_code=400, detail="No tasks available to run the optimizer.")

    # Convert tasks into Task objects as expected by main.py
    task_objects = [main.Task(**task) for task in tasks]  # Ensure Task class is imported or defined in main.py

    # Run optimizer with the task list
    try:
        schedule = main.run_optimizer(task_objects)  # Ensure `main.py` has `run_optimizer(tasks)` function that returns a schedule
        return {"status": "Optimization completed successfully", "schedule": schedule}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimizer failed: {str(e)}")

@app.get("/tasks/", response_model=List[TaskModel])
def get_tasks():
    return tasks

@app.delete("/tasks/", response_model=dict)
def clear_tasks():
    tasks.clear()
    return {"status": "All tasks cleared"}
