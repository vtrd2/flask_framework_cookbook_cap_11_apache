activate_this = 'C:\Users\Paulo\Desktop\Python\Flask_Framework_Cookbook\cap_11\venv\bin\activate_this.py'
exec(open(activate_this).read(), dict(__file__=activate_this))

from my_app import app as application
import sys, logging
logging.basicConfig(stream = sys.stderr)