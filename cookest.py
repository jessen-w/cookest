import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt

# Define cooking tasks and their durations in minutes
# Task name, duration, type (exclusive or parallel)
tasks = {
    "rice_wash": (2, "exclusive"),
    "rice_steam": (20, "parallel"),
    "egg_chop": (5, "exclusive"),
    "egg_fry": (5, "exclusive"),
    "tofu_chop": (5, "exclusive"),
    "tofu_fry": (10, "exclusive"),
    "chickenbrocolli_chop": (10, "exclusive"),
    "chickenbrocolli_fry": (10, "exclusive"),
}

# List of tasks by dish
task_sequence = {
    "rice": ["rice_wash", "rice_steam"],
    "tomato_egg": ["egg_chop", "egg_fry"],
    "tofu": ["tofu_chop", "tofu_fry"],
    "chickenbroclli": ["chickenbrocolli_chop", "chickenbrocolli_fry"]
}

# Define time horizon, enough to cover the longest tasks
T = range(sum(duration for duration, _ in tasks.values()))

# Model
m = gp.Model("Cooking_Scheduler")

# Decision Variables
# Allocation: Whether task starts at a specific time
start = m.addVars(tasks.keys(), T, vtype=GRB.BINARY, name="start")

# Constraint 1
# Ensure each task starts only once
for task in tasks:
    m.addConstr(gp.quicksum(start[task, t] for t in T) == 1, f"start_once_{task}")

# Constraint 2
# Duration constraints: enforce task duration after start
for task, (duration, _) in tasks.items():
    for t in T:
        if t + duration <= len(T):
            m.addConstr(gp.quicksum(start[task, t_prime] for t_prime in range(t, t + duration)) <= duration, 
                        f"duration_{task}_{t}")

# Ensure sequence for tasks within each dish
for dish, dish_tasks in task_sequence.items():
    for i in range(len(dish_tasks) - 1):
        task_1 = dish_tasks[i]
        task_2 = dish_tasks[i + 1]
        m.addConstr(
            gp.quicksum((t + tasks[task_1][0]) * start[task_1, t] for t in T) <=
            gp.quicksum(t * start[task_2, t] for t in T),
            f"sequence_{task_1}_{task_2}"
        )

# Limit to one exclusive task at any given time - wrong - only account of 1st T of each task not the whole duration.
for t in T:
    m.addConstr(
        gp.quicksum(start[task, t] for task, (_, task_type) in tasks.items() if task_type == "exclusive") <= 1,
        f"exclusive_limit_{t}"
    )

# Objective: Minimize makespan
makespan = m.addVar(vtype=GRB.CONTINUOUS, name="makespan")
for task, (duration, _) in tasks.items():
    m.addConstr(makespan >= gp.quicksum((t + duration) * start[task, t] for t in T), f"makespan_{task}")

m.setObjective(makespan, GRB.MINIMIZE)

# Optimize
m.optimize()

# Display results
if m.status == GRB.OPTIMAL:
    print("Optimal solution found!")
    schedule = {task: [] for task in tasks}
    
    # Collect start times
    for task in tasks:
        for t in T:
            if start[task, t].x > 0.5:
                schedule[task] = (t, t + tasks[task][0])
                print(f"{task} starts at time {t} and ends at {t + tasks[task][0]}")

    # Visualization
    fig, ax = plt.subplots(figsize=(10, 5))
    y_labels = []
    colors = plt.cm.get_cmap("tab10", len(tasks))
    
    for i, (task, (start_time, end_time)) in enumerate(schedule.items()):
        ax.barh(i, end_time - start_time, left=start_time, color=colors(i), edgecolor="black")
        y_labels.append(task)
    
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels)
    ax.set_xlabel("Time (minutes)")
    ax.set_title("Cooking Schedule Optimization")
    plt.show()
else:
    print("No optimal solution found.")
