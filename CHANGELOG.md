# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Added
### Changed
### Fixed

## [0.4.0] - 2021-10-02
### Added
- Added authentication system
    - User login/logout using Flask-Login
    - User registering
### Changed
### Fixed

## [0.3.0] - 2021-09-30
### Added
- Added tests folder for testing app - 100% tested (Flask-Testing and coverage)
- Added first version of database using alembic and Flask-Migrate  
- Create auth blueprint for authentication via login page
- Hardcoded connection to the Postgresql database - to be changed to set it up when start app
- Added model for User
- Bootstrap, JQuery
### Changed
### Fixed

## [0.2.0] - 2021-09-29
### Added
- The app is created using create_app func when we start flask app with app.py script
- Configuration is defined in config.py file for development/testing/production environment
- Flask blueprints

## [0.1.0] - 2021-09-29
### Added
- Added basic Flask app structure