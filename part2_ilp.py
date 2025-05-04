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
    if seeker['Desired_Job_Type'] != job['Job_Type']:
        return False
    if seeker['Min_Desired_Salary'] > job['Salary_Range_Max']:
        return False
    seeker_skills = set(ast.literal_eval(seeker['Skills']))
    job_skills = set(ast.literal_eval(job['Required_Skills']))
    if not job_skills.issubset(seeker_skills):
        return False
    if experience_levels[seeker['Experience_Level']] < experience_levels[job['Required_Experience_Level']]:
        return False
    if job['Is_Remote'] == 1:
        return True
    else:
        distance = location_distances.loc[seeker['Location'], job['Location']]
        if distance > seeker['Max_Commute_Distance']:
            return False
    return True

# Calculate dissimilarities for compatible pairs
pairs = []
dissimilarities = {}
for i, seeker in seekers.iterrows():
    seeker_q = ast.literal_eval(seeker['Questionnaire'])
    for j, job in jobs.iterrows():
        if compatible(seeker, job):
            job_q = ast.literal_eval(job['Questionnaire'])
            dij = sum(abs(q1 - q2) for q1, q2 in zip(seeker_q, job_q)) / 20
            pairs.append((seeker['Seeker_ID'], job['Job_ID']))
            dissimilarities[(seeker['Seeker_ID'], job['Job_ID'])] = dij

print(f"Total compatible pairs with dissimilarities: {len(pairs)}")

# Input Mw manually or read from Part 1
Mw = float(input("Enter Mw from Part 1: "))

# Test different ω values
omegas = [0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
results = []

for omega in omegas:
    model = gp.Model(f"Minimize_Max_Dissimilarity_w_{omega}")

    x = model.addVars(pairs, vtype=GRB.BINARY, name="assign")
    D = model.addVar(vtype=GRB.CONTINUOUS, name="D")

    # Objective
    model.setObjective(D, GRB.MINIMIZE)

    # Constraints
    for seeker_id in seekers['Seeker_ID']:
        model.addConstr(gp.quicksum(x[i,j] for i,j in pairs if i == seeker_id) <= 1)
    
    for job_id in jobs['Job_ID']:
        num_positions = jobs.loc[jobs['Job_ID'] == job_id, 'Num_Positions'].values[0]
        model.addConstr(gp.quicksum(x[i,j] for i,j in pairs if j == job_id) <= num_positions)
    
    for (i,j) in pairs:
        model.addConstr(dissimilarities[(i,j)] * x[i,j] <= D)

    model.addConstr(gp.quicksum(jobs.loc[jobs['Job_ID'] == j, 'Priority_Weight'].values[0] * x[i,j] for i,j in pairs) >= omega * Mw)

    model.optimize()

    if model.status == GRB.OPTIMAL:
        results.append((omega, D.X))
        print(f"Omega={omega}, Max dissimilarity={D.X}")
    else:
        results.append((omega, None))
        print(f"Omega={omega}, No feasible solution.")

# Save results
pd.DataFrame(results, columns=['Omega', 'Max_Dissimilarity']).to_csv('omega_vs_dissimilarity.csv', index=False)
