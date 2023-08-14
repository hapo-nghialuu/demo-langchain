## Setting up this project in a virtual environment

1. Create a new virtual environment using Python venv by running the following command:
   ```
   python3 -m venv myenv
   ```
   This will create a new directory called myenv that contains the virtual environment.
2. Activate the virtual environment by running the following command:
   ```
   source myenv/bin/activate
   ```
3. Install libs:
   ```
   pip install --upgrade pip
   pip install -r requirement.txt
   ```
4. Run the test:
   ```
   python src/main.py
   ```
