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
    for i in range(len(job_questionnaire)): 
        difference += abs(job_questionnaire[i] - seeker_answers[i])
    return difference / len(job_questionnaire) if len(job_questionnaire) > 0 else 0

# Load data
seekers = pd.read_csv('seekers.csv')
jobs = pd.read_csv('jobs.csv')
location_distances = pd.read_csv('location_distances.csv', index_col=0)

# Conversion of experience levels to integers 
for i in seekers['Seeker_ID']:
    seeker_row = seekers[seekers['Seeker_ID'] == i]
    level = seeker_row['Experience_Level'].iloc[0]
    if level == 'Entry-level':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 0
    elif level == 'Mid-level':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 1
    elif level == 'Senior':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 2
    elif level == 'Lead':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 3
    elif level == 'Manager':
        seekers.loc[seekers['Seeker_ID'] == i, 'Experience_Level'] = 4
for j in jobs['Job_ID']:
    job_row = jobs[jobs['Job_ID'] == j]
    level = job_row['Required_Experience_Level'].iloc[0]
    if level == 'Entry-level':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 0
    elif level == 'Mid-level':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 1
    elif level == 'Senior':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 2
    elif level == 'Lead':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 3
    elif level == 'Manager':
        jobs.loc[jobs['Job_ID'] == j, 'Required_Experience_Level'] = 4


# Load Mw from part1
with open("part1_result.txt", "r") as f:
    M_w = float(f.read())

w_values = [70, 75, 80, 85, 90, 95, 100]
results = []

for w in w_values:
    print(f"\nRunning Part 2 for ω = {w}")
    part2_model = gp.Model(f"part2_model_w{w}")
    part2_model.setParam("OutputFlag", 0) 

    # Variables
    x = {}
    d = {} 
    for i in seekers['Seeker_ID']:
        for j in jobs['Job_ID']:
            x[i, j] = part2_model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
            d[i, j] = part2_model.addVar(vtype=GRB.CONTINUOUS, name=f"d_{i}_{j}", lb=0)
    max_dissimilarity = part2_model.addVar(vtype=GRB.CONTINUOUS, name="max_dissimilarity", lb=0)

    # Constraint for assigning at most 1 job to every seeker.
    for i in seekers['Seeker_ID']:
        part2_model.addConstr(sum(x[i, j] for j in jobs['Job_ID']) <= 1)

    # Constraint for assigning at most the number of available positions for the job to seekers.
    for j in jobs['Job_ID']:
        job_row_for_capacity = jobs[jobs['Job_ID'] == j] # Use a distinct name
        num_positions = int(job_row_for_capacity['Num_Positions'].iloc[0])
        part2_model.addConstr(sum(x[i, j] for i in seekers['Seeker_ID']) <= num_positions)

    # Constraints for compatibility, d[i,j] definition, and max_dissimilarity linkage
    for i in seekers['Seeker_ID']:
        seeker_row = seekers[seekers['Seeker_ID'] == i]
        for j in jobs['Job_ID']:
            job_row = jobs[jobs['Job_ID'] == j]

            # Constraint for checking the job types match
            job_type_match_constr = 1 if seeker_row['Desired_Job_Type'].iloc[0] == job_row['Job_Type'].iloc[0] else 0
            part2_model.addConstr(x[i, j] <= job_type_match_constr)

            # Constraint for checking the salary expectations match
            salary_constr = 1 if int(job_row['Salary_Range_Min'].iloc[0]) <= int(seeker_row['Min_Desired_Salary'].iloc[0]) <= int(job_row['Salary_Range_Max'].iloc[0]) else 0
            part2_model.addConstr(x[i, j] <= salary_constr)

            # Constraint for checking whether seeker has the skillset
            seeker_skillset = ast.literal_eval(seeker_row['Skills'].iloc[0])
            job_required_skills = ast.literal_eval(job_row['Required_Skills'].iloc[0])
            skill_match_constr = 1 if skill_checker(job_required_skills, seeker_skillset) else 0
            part2_model.addConstr(x[i, j] <= skill_match_constr)

            # Constraint for the experience level
            exp_match_constr = 1 if int(seeker_row['Experience_Level'].iloc[0]) >= int(job_row['Required_Experience_Level'].iloc[0]) else 0
            part2_model.addConstr(x[i, j] <= exp_match_constr)

            # Constraint for location
            location_match_constr = 1 if int(job_row['Is_Remote'].iloc[0]) == 1 or \
                                       location_checker(seeker_row['Location'].iloc[0],
                                                        job_row['Location'].iloc[0],
                                                        seeker_row['Max_Commute_Distance'].iloc[0]) else 0
            part2_model.addConstr(x[i, j] <= location_match_constr)

            # Determine if the pair is fundamentally compatible based on all Python checks
            is_compatible = (job_type_match_constr == 1 and
                                           salary_constr == 1 and
                                           skill_match_constr == 1 and
                                           exp_match_constr == 1 and
                                           location_match_constr == 1)

            # Calculate questionnaire difference
            seeker_questionnaire = ast.literal_eval(seeker_row['Questionnaire'].iloc[0])
            job_questionnaire = ast.literal_eval(job_row['Questionnaire'].iloc[0])
            actual_dissimilarity_value = difference_calculator(job_questionnaire, seeker_questionnaire)

            # Set d[i,j] based on fundamental compatibility
            if is_compatible:
                part2_model.addConstr(d[i, j] == actual_dissimilarity_value)
            else:
                part2_model.addConstr(d[i, j] == 0)

            part2_model.addConstr(max_dissimilarity >= d[i, j] * x[i, j])

    # Constraint for ω: total weighted priority must be ≥ ω% of Mw
    part2_model.addConstr(
        sum(x[i, j] * int(jobs[jobs['Job_ID'] == j]['Priority_Weight'].iloc[0])
            for i in seekers['Seeker_ID'] for j in jobs['Job_ID']) >= M_w * w / 100
    )

    # Objective: minimize max dissimilarity
    part2_model.setObjective(max_dissimilarity, GRB.MINIMIZE)
    part2_model.optimize()


    current_max_dissim = max_dissimilarity.X
    print(f"ω = {w} → max dissimilarity = {current_max_dissim:.4f}")
    results.append((w, current_max_dissim))


# make the plot
df_results = pd.DataFrame(results, columns=["omega", "max_dissimilarity"])

# save the reuslts
df_results.to_csv("omega_vs_dissimilarity.csv", index=False)

# make the plot
plt.figure(figsize=(10, 6))
plt.plot(df_results["omega"], df_results["max_dissimilarity"], marker="o", linestyle="-", color="b")
plt.xlabel("ω (% of Mw)")
plt.ylabel("Max Dissimilarity")
plt.title("ω vs. Max Dissimilarity")
plt.grid(True)
plt.savefig("omega_vs_dissimilarity.png")
plt.show()

# print the optimal omega value
min_dissim_value = df_results['max_dissimilarity'].min()
best_omega_values = df_results[df_results['max_dissimilarity'] == min_dissim_value]['omega'].tolist()
print(f"\nThe minimum max dissimilarity ({min_dissim_value:.4f}) is achieved when ω is/are: {best_omega_values}")
