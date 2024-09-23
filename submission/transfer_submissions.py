import glob
import json

if __name__ == '__main__':

    submission_files = glob.glob('../resources/submissions/scenario_*.json')

    for path in submission_files:

        # Open original file
        with open(path, 'r') as f:
            data = json.load(f)

        # Add zero detection to every path
        for username in data:
            data[username]['detection'] = 0

        # Save the new submissions path
        new_path = path.replace('submissions', 'submissions2')
        with open(new_path, 'w') as f:
            json.dump(data, f)
