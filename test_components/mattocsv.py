import os
import scipy.io
import pandas as pd

# Directory containing the .mat files
directory = '/Users/fareza_e/y3proj/proj/matdata'

# Iterate over each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.mat'):
        # Full path to the current .mat file
        file_path = os.path.join(directory, filename)
        
        # Load .mat file
        mat = scipy.io.loadmat(file_path)
        
        # Filter out any keys starting with '__'
        mat = {k: v for k, v in mat.items() if k[0] != '_'}
        
        # Create a DataFrame from the mat file data
        data = pd.DataFrame({k: pd.Series(v[0]) for k, v in mat.items()})
        
        # Create CSV filename (change extension from .mat to .csv)
        csv_filename = filename[:-4] + '.csv'
        csv_path = os.path.join(directory, csv_filename)
        
        # Save DataFrame to CSV
        data.to_csv(csv_path, index=False)

        print(f"Converted {file_path} to {csv_path}")
