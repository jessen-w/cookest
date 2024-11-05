import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt

# Define the Task class
class Task:
    def __init__(self, name, task_type, duration, sequence):
        self.name = name          # Dish name, e.g., "egg"
        self.task_type = task_type  # Action, e.g., "chop"
        self.duration = duration    # Duration in minutes
        self.sequence = sequence    # Sequence order in the dish preparation
        self.start_time = None      # Start time (to be determined by optimization)
        self.end_time = None        # End time (to be determined by optimization)

# Define cooking tasks for each dish
tasks = [
    Task("egg", "chop", 5, 1),
    Task("egg", "fry", 5, 2),
    Task("tofu", "chop", 5, 1),
    Task("tofu", "fry", 10, 2),
    Task("rice", "wash", 2, 1),
    Task("rice", "steam", 20, 2),
    Task("chickenbrocolli", "chop", 10, 1),
    Task("chickenbrocolli", "fry", 10, 2)
]

# Define exclusive tasks:
exclusive_tasks = ["chop", "fry", "wash"]

# Define time horizon, enough to cover the longest tasks
T = range(sum(task.duration for task in tasks))

# Model
m = gp.Model("Cooking_Scheduler")

# Decision Variables
# Allocation: Whether a task starts at a specific time
start = m.addVars([task.name + "_" + task.task_type for task in tasks], T, vtype=GRB.BINARY, name="start")

# Constraint 1: Ensure each task starts only once
for task in tasks:
    m.addConstr(gp.quicksum(start[task.name + "_" + task.task_type, t] for t in T) == 1, f"start_once_{task.name}_{task.task_type}")

# Constraint 2: Duration constraints - each task must run continuously for its duration once it starts
for task in tasks:
    for t in T:
        if t + task.duration <= len(T):
            m.addConstr(gp.quicksum(start[task.name + "_" + task.task_type, t_prime] for t_prime in range(t, t + task.duration)) <= task.duration,
                        f"duration_{task.name}_{task.task_type}_{t}")

# Constraint 3: Task sequencing within each dish
dishes = {}
for task in tasks:
    if task.name not in dishes:
        dishes[task.name] = []
    dishes[task.name].append(task)

for dish, dish_tasks in dishes.items():
    # Sort tasks by their sequence attribute
    dish_tasks.sort(key=lambda x: x.sequence)
    for i in range(len(dish_tasks) - 1):
        task_1 = dish_tasks[i]
        task_2 = dish_tasks[i + 1]
        m.addConstr(
            gp.quicksum((t + task_1.duration) * start[task_1.name + "_" + task_1.task_type, t] for t in T) <=
            gp.quicksum(t * start[task_2.name + "_" + task_2.task_type, t] for t in T),
            f"sequence_{task_1.name}_{task_1.task_type}_{task_2.name}_{task_2.task_type}"
        )

# Constraint 4: Enforce exclusivity for exclusive tasks
for task in tasks:
    if task.task_type in exclusive_tasks:  # Exclusive tasks
        for t in T:
            # If this task starts at time t, no other exclusive task can start during its duration
            m.addConstr(
                gp.quicksum(
                    start[other_task.name + "_" + other_task.task_type, t_prime]
                    for other_task in tasks
                    if other_task.task_type in exclusive_tasks and other_task != task
                    for t_prime in range(t, min(t + task.duration, len(T)))
                ) <= (1 - start[task.name + "_" + task.task_type, t]) * len(T),
                f"exclusive_constraint_{task.name}_{task.task_type}_{t}"
            )

# Objective: Minimize makespan
makespan = m.addVar(vtype=GRB.CONTINUOUS, name="makespan")
for task in tasks:
    m.addConstr(makespan >= gp.quicksum((t + task.duration) * start[task.name + "_" + task.task_type, t] for t in T),
                f"makespan_{task.name}_{task.task_type}")

m.setObjective(makespan, GRB.MINIMIZE)

# Optimize
m.optimize()

# Display results
if m.status == GRB.OPTIMAL:
    print("Optimal solution found!")
    schedule = {task.name + "_" + task.task_type: [] for task in tasks}
    
    # Collect start times
    for task in tasks:
        task_key = task.name + "_" + task.task_type
        for t in T:
            if start[task_key, t].x > 0.5:
                task.start_time = t
                task.end_time = t + task.duration
                schedule[task_key] = (task.start_time, task.end_time)
                print(f"{task.name} {task.task_type} starts at time {task.start_time} and ends at {task.end_time}")

    # Visualization
    fig, ax = plt.subplots(figsize=(10, 5))
    y_labels = []
    colors = plt.cm.get_cmap("tab10", len(tasks))
    
    for i, (task_key, (start_time, end_time)) in enumerate(schedule.items()):
        ax.barh(i, end_time - start_time, left=start_time, color=colors(i), edgecolor="black")
        y_labels.append(task_key)
    
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Time (minutes)")
    ax.set_title("Cooking Schedule Optimization")
    plt.show()
else:
    print("No optimal solution found.")
