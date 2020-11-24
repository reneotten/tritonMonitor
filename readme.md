# Triton Monitoring App

Monitoring/Log Viewing Browser app for Oxford Instruments Triton (and probabply newer Kelvinox) Fridges.
Works sowly on the log file, no tempering with the fridge control software required.

# Screenshot
![Screenshot of the app](https://github.com/reneotten/tritonMonitor/blob/master/doc/images/FridgeMonitor.PNG "Screenshot")

# Getting Started
This app consists of two parts:
- app.py is a dash app that can be run on heroku. It relies on a Postgres SQL database to update the graphs (There is a 'local_mode' flag in the settings file, to force legacy behaviour.)
- upload_client.py is a python script that reads the Oxford Instruments .vcl files and pushes them to the SQL database. 

## Setting up the heroku app.
Set up a heroku app with Postgres SQL selected under ressources. Create a branch for you fridge and connect it to you heroku app. Create a 'seetings.json' file from the examples provided. The Channels should match the names given to them during fridge installation. Make sure that the URL of your Database reads "DATABASE_URL" before deploying.
After deploying the app clone the repo to your local machine which has the log files. Change the SQL database URL to your Postgres database and run 'upload_client.py'.

# Legacy Usage

As of 24.11.2020 this app has been remodeled do work as a heroku/web app with an SQL database, that is constantly updated by a client script using the log files.
Checkout the branch heroku-deploy to test out the ne way to use this app.
```
python app.py --filename triton200.json --port 1234
```
`triton200.json` contains all Titles and channel names that vary from system to system and needs to be adopted. Two examples for two of our systems are included. Feel free to add more!



