# flask_travel_arrangements

This app is created using PyCharm Create Project tool.
It sets up venv folder using virtualenv and install all python packages necessary for basic flask project.

1. If you want to set up project without using PyCharm tool, before starting app you need to
Make a Python virtual environment somewhere using virtualenv package (you need to install that package using `pip install virtualenv`):
   `vitualenv venv`
   
2. Activate the virtual environment (using Bash installed on WinOS):
   `source venv/Scripts/activate`
   
3. Navigate to the project directory:

`cd path/to/project/directory`

4. Install project requirements:

`pip install -r requirements.txt`

5. Run the app from project directory with the following command:

`export FLASK_APP=app.py && flask run`

After these steps the app is available using at http://localhost:5000 or http://127.0.0.1:5000
