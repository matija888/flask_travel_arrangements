from flask import Blueprint

main = Blueprint('main', __name__)

from . import views  # Must stay at the end to prevent circular imports!