import pandas as pd
import ast
import gurobipy as gp
from gurobipy import GRB

# Read data
seekers = pd.read_csv('seekers.csv')
jobs = pd.read_csv('jobs.csv')
location_distances = pd.read_csv('location_distances.csv', index_col=0)
