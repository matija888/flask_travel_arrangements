# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]
### Added
### Changed
### Fixed


## [0.13.0] - 2021-10-06
### Added
- Add information who is currently logged user (username in nav)
### Fixed
- Do not display info about pending account type change if it is rejected by admin

## [0.12.1] - 2021-10-06
### Fixed
- Do not allow admin to delete arrangement if it is too late for that
- Show pending requests for account type change in admin panel

## [0.12.0] - 2021-10-06
### Added
- Add sorting for users' table in admin panel

## [0.11.0] - 2021-10-06
### Added
- Pagination for all tables and sorting for travel arrangements
- Filtering:
    - ADMIN can filter users by account type
    - TOURIST can search for arrangements base on a destination a period of time

## [0.10.0] - 2021-10-05
### Added
- Create reservations feature
  - Allow TOURIST to book travel arrangements
  - TOURIST can see all unbooked arrangements and all arrangements booked by them
### Fixed
- Fix get_available_travel_guides_ids method to return correct result 
  (take into account that we have four cases where some travel can overlap other travel)

## [0.9.0] - 2021-10-04
### Added
- Allow ADMIN to assign a travel guide to certain travel arrangement
  - Admin can only assign available travel guide - those who are not assigned to any arrangement 
    or who is assigned to a certain arrangement but not for the passed period of time
    
## [0.8.0] - 2021-10-04
### Added
- Insert a travel arrangement (ADMIN and TRAVEL GUIDE have this permission)
- Edit a travel arrangement (5 days before the travel start date at the latest)
  - ADMIN can edit all attributes of the travel arrangement 
  - TRAVEL can edit description of the travel arrangement
- Cancel a travel arrangement (5 days before the travel start date at the latest)
  - ADMIN can cancel the travel arrangement

## [0.7.0] - 2021-10-03
### Added 
- Add travel arrangements page
  - Allow ADMIN to insert and see all travel arrangements
  - Allow TRAVEL GUIDE only to see travel arrangements

## [0.6.1] - 2021-10-03
### Fixed
- When a user registering in the app first time, redirect them to the index(home) page
- If there is no action related to changing account type request, do not display desired account type
- Show a message related to waiting for a request (related to the change of the account type) to be resolved
only for a user who has sent the request.
- Set LOGIN_DISABLED to be False when we load development environment configuration

## [0.6.0] - 2021-10-03
### Added 
- Edit user data page
- confirmed_desired_account_type column in user table 
  which represents if admin has resolved pending requests for changing account type (approve/reject/pending)
### Fixed
- added requires_account_type and login_required decorators in order to restrict access to the admin panel

## [0.5.0] - 2021-10-03
### Added 
- Add the admin page 
- On the admin page, Admin can solve requests from the user related to account type
- Added modals for two-step (pop-up windows) for approving/rejecting a request
### Changed
- Give option to the user to choose which account type they want to have
### Fixed

## [0.4.0] - 2021-10-02
### Added
- Added new column desired_account_type in user table

## [0.4.0] - 2021-10-02
### Added
- Added authentication system
    - User login/logout using Flask-Login
    - User registering

## [0.3.0] - 2021-09-30
### Added
- Added tests folder for testing app - 100% tested (Flask-Testing and coverage)
- Added first version of database using alembic and Flask-Migrate  
- Create auth blueprint for authentication via login page
- Hardcoded connection to the Postgresql database - to be changed to set it up when start app
- Added model for User
- Bootstrap, JQuery

## [0.2.0] - 2021-09-29
### Added
- The app is created using create_app func when we start flask app with app.py script
- Configuration is defined in config.py file for development/testing/production environment
- Flask blueprints

## [0.1.0] - 2021-09-29
### Added
- Added basic Flask app structure