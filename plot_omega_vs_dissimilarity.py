import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('omega_vs_dissimilarity.csv')

plt.figure()
plt.plot(data['Omega'], data['Max_Dissimilarity'], marker='o')
plt.xlabel('Omega (%)')
plt.ylabel('Maximum Dissimilarity')
plt.title('Omega vs Maximum Dissimilarity')
plt.grid(True)
plt.show()
