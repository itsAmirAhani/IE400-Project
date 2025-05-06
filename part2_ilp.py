import pandas as pd
import ast
import gurobipy as gp
from gurobipy import GRB

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
    if int(max_commute_distance) >= int(location_distances[seeker_location][job_location]):
        return True
    return False

# Read data
seekers = pd.read_csv('seekers.csv')
jobs = pd.read_csv('jobs.csv')
location_distances = pd.read_csv('location_distances.csv', index_col=0)
part2_model = gp.Model("part2_model")

x={}
for i in seekers['Seeker_ID']:
    for j in jobs['Job_ID']:
        x[i, j] = part2_model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}") # Binary variable. 1 if seeker i is assigned to job j, 0 otherwise.

# Constraint for assigning at most 1 job to every seeker.
for i in seekers['Seeker_ID']:
    part2_model.addConstr(sum(x[i, j] for j in jobs['Job_ID']) <= 1) 

# Constraint for assigning at most the number of available positions for the job to seekers.
for j in jobs['Job_ID']:
    job_row = jobs[jobs['Job_ID'] == j]
    num_positions = int(job_row['Num_Positions'].iloc[0])

    part2_model.addConstr(sum(x[i, j] for i in seekers['Seeker_ID']) <= num_positions) 

# Constraint for checking the job types match between the seekers and the jobs
for i in seekers['Seeker_ID']:
    for j in jobs['Job_ID']:
        seeker_row = seekers[seekers['Seeker_ID'] == i]
        job_row = jobs[jobs['Job_ID'] == j]
        job_type_constr = 1 if seeker_row['Desired_Job_Type'].iloc[0] == job_row['Job_Type'].iloc[0] else 0
        part2_model.addConstr(x[i, j] <= job_type_constr)

# Constraint for checking the salary expectations match between the seekers and the jobs
for i in seekers['Seeker_ID']:
    for j in jobs['Job_ID']:
        seeker_row = seekers[seekers['Seeker_ID'] == i]
        job_row = jobs[jobs['Job_ID'] == j]
        salary_constr = 1 if int(job_row['Salary_Range_Min'].iloc[0]) <= int(seeker_row['Min_Desired_Salary'].iloc[0]) <= int(job_row['Salary_Range_Max'].iloc[0]) else 0
        part2_model.addConstr(x[i, j] <= salary_constr)

# Constraint for checking whether seeker has the skillset for the job requirements
for i in seekers['Seeker_ID']:
    for j in jobs['Job_ID']:
        seeker_row = seekers[seekers['Seeker_ID'] == i]
        job_row = jobs[jobs['Job_ID'] == j]
        seeker_skillset = ast.literal_eval(seeker_row['Skills'].iloc[0])
        job_required = ast.literal_eval(job_row['Required_Skills'].iloc[0])
        requirement_constr = 1 if skill_checker(job_required, seeker_skillset) == True else 0
        part2_model.addConstr(x[i, j] <= requirement_constr)

# Conversion of job levels to integers
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

# Constraint for the experience level
for i in seekers['Seeker_ID']:
    for j in jobs['Job_ID']:
        seeker_row = seekers[seekers['Seeker_ID'] == i]
        job_row = jobs[jobs['Job_ID'] == j]
        experience_constr = 1 if int(job_row['Required_Experience_Level'].iloc[0]) <= int(seeker_row['Experience_Level'].iloc[0]) else 0
        part2_model.addConstr(x[i, j] <= experience_constr)

# Constraint for location 
for i in seekers['Seeker_ID']:
    for j in jobs['Job_ID']:
        seeker_row = seekers[seekers['Seeker_ID'] == i]
        job_row = jobs[jobs['Job_ID'] == j]
        location_constr = 1 if int(job_row['Is_Remote'].iloc[0]) == 1 or location_checker(seeker_row['Location'].iloc[0], job_row['Location'].iloc[0], int(seeker_row['Max_Commute_Distance'].iloc[0])) == True else 0
        part2_model.addConstr(x[i, j] <= location_constr)
