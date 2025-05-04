import pandas as pd
import ast
import gurobipy as gp
from gurobipy import GRB

# Read data
seekers = pd.read_csv('seekers.csv')
jobs = pd.read_csv('jobs.csv')
location_distances = pd.read_csv('location_distances.csv', index_col=0)

# Helper functions
experience_levels = {'Entry-level': 0, 'Mid-level': 1, 'Senior': 2, 'Lead': 3, 'Manager': 4}

def compatible(seeker, job):
    # Job Type
    if seeker['Desired_Job_Type'] != job['Job_Type']:
        return False
    
    # Salary
    if seeker['Min_Desired_Salary'] > job['Salary_Range_Max']:
        return False
    
    # Skills
    seeker_skills = set(ast.literal_eval(seeker['Skills']))
    job_skills = set(ast.literal_eval(job['Required_Skills']))
    if not job_skills.issubset(seeker_skills):
        return False
    
    # Experience
    if experience_levels[seeker['Experience_Level']] < experience_levels[job['Required_Experience_Level']]:
        return False
    
    # Location
    if job['Is_Remote'] == 1:
        return True
    else:
        distance = location_distances.loc[seeker['Location'], job['Location']]
        if distance > seeker['Max_Commute_Distance']:
            return False
    
    return True

# Build feasible pairs
pairs = []
for i, seeker in seekers.iterrows():
    for j, job in jobs.iterrows():
        if compatible(seeker, job):
            pairs.append((seeker['Seeker_ID'], job['Job_ID']))

print(f"Total compatible pairs: {len(pairs)}")

# Create model
model = gp.Model("Maximize Priority Weighted Matches")

# Decision variables
x = model.addVars(pairs, vtype=GRB.BINARY, name="assign")

# Objective
model.setObjective(gp.quicksum(jobs.loc[jobs['Job_ID'] == j, 'Priority_Weight'].values[0] * x[i,j] for i,j in pairs), GRB.MAXIMIZE)

# Constraints
# 1. Each seeker assigned to at most one job
for seeker_id in seekers['Seeker_ID']:
    model.addConstr(gp.quicksum(x[i,j] for i,j in pairs if i == seeker_id) <= 1)

# 2. Job position limits
for job_id in jobs['Job_ID']:
    num_positions = jobs.loc[jobs['Job_ID'] == job_id, 'Num_Positions'].values[0]
    model.addConstr(gp.quicksum(x[i,j] for i,j in pairs if j == job_id) <= num_positions)

# Solve
model.optimize()

# Get Mw
Mw = model.ObjVal
print(f"\nMax total priority weight (Mw) = {Mw}")

# Save selected assignments
assignments = [(i, j) for (i, j) in pairs if x[i, j].X > 0.5]
pd.DataFrame(assignments, columns=['Seeker_ID', 'Job_ID']).to_csv('assignments_part1.csv', index=False)
