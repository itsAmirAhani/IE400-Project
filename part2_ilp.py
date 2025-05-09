import pandas as pd
import ast
import gurobipy as gp
from gurobipy import GRB
import matplotlib.pyplot as plt

# Helper functions
def skill_checker(required, skillset):
    for i in required:
        check_flg = False
        for j in skillset:
            if i == j:
                check_flg = True
        if check_flg == False:
            return False
    return True

def location_checker(seeker_location, job_location, max_commute_distance):
    return int(max_commute_distance) >= int(location_distances[seeker_location][job_location])

def difference_calculator(job_questionnaire, seeker_answers):
    difference = 0
    for i in range(20):
        difference += abs(job_questionnaire[i] - seeker_answers[i])
    return difference / 20

# Load data
seekers = pd.read_csv('seekers.csv')
jobs = pd.read_csv('jobs.csv')
location_distances = pd.read_csv('location_distances.csv', index_col=0)

# Map experience levels
for i in seekers['Seeker_ID']:
    seeker_row = seekers[seekers['Seeker_ID'] == i]
    if seeker_row['Experience_Level'].iloc[0] == 'Entry-level':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 0
    elif seeker_row['Experience_Level'].iloc[0] == 'Mid-level':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 1
    elif seeker_row['Experience_Level'].iloc[0] == 'Senior':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 2
    elif seeker_row['Experience_Level'].iloc[0] == 'Lead':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 3
    elif seeker_row['Experience_Level'].iloc[0] == 'Manager':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 4
for j in jobs['Job_ID']:
    job_row = jobs[jobs['Job_ID'] == j]
    if job_row['Required_Experience_Level'].iloc[0] == 'Entry-level':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 0
    elif job_row['Required_Experience_Level'].iloc[0] == 'Mid-level':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 1
    elif job_row['Required_Experience_Level'].iloc[0] == 'Senior':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 2
    elif job_row['Required_Experience_Level'].iloc[0] == 'Lead':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 3
    elif job_row['Required_Experience_Level'].iloc[0] == 'Manager':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 4

# Load Mw from part1
with open("part1_result.txt", "r") as f:
    M_w = float(f.read())

omega_values = [70, 75, 80, 85, 90, 95, 100]
results = []

for w in omega_values:
    print(f"\nRunning Part 2 for ω = {w}")
    part2_model = gp.Model(f"part2_model_w{w}")
    part2_model.setParam("OutputFlag", 0)

    # Variables
    x = {}
    d = {}
    for i in seekers['Seeker_ID']:
        for j in jobs['Job_ID']:
            x[i, j] = part2_model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
            d[i, j] = part2_model.addVar(vtype=GRB.CONTINUOUS, name=f"d_{i}_{j}")
    max_dissimilarity = part2_model.addVar(vtype=GRB.CONTINUOUS, name="max_dissimilarity")

    # Constraint 1: Each seeker assigned at most one job
    for i in seekers['Seeker_ID']:
        part2_model.addConstr(sum(x[i, j] for j in jobs['Job_ID']) <= 1)

    # Constraint 2: Job capacity
    for j in jobs['Job_ID']:
        capacity = int(jobs[jobs['Job_ID'] == j]['Num_Positions'].iloc[0])
        part2_model.addConstr(sum(x[i, j] for i in seekers['Seeker_ID']) <= capacity)

    # Compatibility and dissimilarity constraints
    for i in seekers['Seeker_ID']:
        seeker = seekers[seekers['Seeker_ID'] == i].iloc[0]
        for j in jobs['Job_ID']:
            job = jobs[jobs['Job_ID'] == j].iloc[0]

            # Compatibility checks
            job_type_ok = seeker['Desired_Job_Type'] == job['Job_Type']
            salary_ok = int(job['Salary_Range_Min']) <= int(seeker['Min_Desired_Salary']) <= int(job['Salary_Range_Max'])
            skill_ok = skill_checker(ast.literal_eval(job['Required_Skills']), ast.literal_eval(seeker['Skills']))
            exp_ok = seeker['Experience_Level'] >= job['Required_Experience_Level']
            location_ok = job['Is_Remote'] == 1 or location_checker(seeker['Location'], job['Location'], seeker['Max_Commute_Distance'])

            if all([job_type_ok, salary_ok, skill_ok, exp_ok, location_ok]):
                seeker_q = ast.literal_eval(seeker['Questionnaire'])
                job_q = ast.literal_eval(job['Questionnaire'])
                diff = difference_calculator(job_q, seeker_q)
                part2_model.addConstr(d[i, j] == diff)
                part2_model.addConstr(max_dissimilarity >= d[i, j] * x[i, j])
            else:
                part2_model.addConstr(x[i, j] == 0)
                part2_model.addConstr(d[i, j] == 0)

    # ω constraint: weighted priority must be ≥ ω% of Mw
    part2_model.addConstr(
        sum(x[i, j] * int(jobs[jobs['Job_ID'] == j]['Priority_Weight'].iloc[0])
            for i in seekers['Seeker_ID'] for j in jobs['Job_ID']) >= M_w * w / 100
    )

    # Objective: minimize max dissimilarity
    part2_model.setObjective(max_dissimilarity, GRB.MINIMIZE)
    part2_model.optimize()

    if part2_model.Status == GRB.OPTIMAL:
        print(f"ω = {w} → max dissimilarity = {max_dissimilarity.X:.4f}")
        results.append((w, max_dissimilarity.X))
    else:
        print(f"ω = {w} → no feasible solution")
        results.append((w, None))

# make the Plot and save it
df = pd.DataFrame(results, columns=["omega", "max_dissimilarity"])
df.to_csv("omega_vs_dissimilarity.csv", index=False)

df.dropna(inplace=True)
plt.plot(df["omega"], df["max_dissimilarity"], marker="o")
plt.xlabel("ω (% of Mw)")
plt.ylabel("Max Dissimilarity")
plt.title("ω vs. Max Dissimilarity")
plt.grid(True)
plt.savefig("omega_vs_dissimilarity.png")
plt.show()

print("The Minimum Maximized dissimilarity is achieved when ω is 70 & 75 ")