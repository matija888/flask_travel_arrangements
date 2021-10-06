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

`set FLASK_APP=manage.py && set MAIL_DEFAULT_SENDER='test@example.com' && set MAIL_USERNAME='test_user@example.com' && set MAIL_PASSWORD='test_password' && flask run`

This command is for WinOS. For Linux you should use export command instead of set.
If for some reason this does not enable sending emails, please type in you email credentials in config file:
MAIL_SERVER = 'smtp.gmail.com'
Instead of:

    `MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')`

set

   `MAIL_DEFAULT_SENDER = 'test@example.com'
    MAIL_USERNAME = 'test_user@example.com'
    MAIL_PASSWORD = 'test_password'`

After these steps the app is available using at http://localhost:5000 or http://127.0.0.1:5000

Coverage package is used to display coverage report.
In order to perform test coverage report perform following commands (from the project's route):
   
   `>> coverage run -m tests.test_app TestApp`

   `>> coverage combine`

   `>> coverage report`

And you will get report:
`````
Name                   Stmts   Miss  Cover
------------------------------------------
app\__init__.py           23      0   100%
app\auth\__init__.py       3      0   100%
app\auth\views.py         49      0   100%
app\decorators.py         21      7    67%
app\main\__init__.py       3      0   100%
app\main\views.py        107      6    94%
app\models.py             85      1    99%
------------------------------------------
TOTAL                    291     14    95%