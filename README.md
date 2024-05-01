# TeamAA_DAP_JAN2024
Database and Analytics Programming Team Project 

Team members
1. Ankith Babu Joseph- x23185813
2. Alphons Zacharia James- x23169702
3. Abhilash Janardhanan- x23121424


Getting Started....

Requirments :Up and running docker desktop in your local PC: https://www.docker.com/products/docker-desktop/

Extract the compressed folder DAP Project_AA.zip

Rename ".env.sample" file contain authentication details to ".env"

initiate Command Prompt and navigate to  extracted folder DAP Project_AA on your Windows system

execute  command :    docker compose up -d

After building all the containers terminal will be detached and docker containers will be running

Navigate to container tab in docker 

open port of container "dagster etl" 3000:3000/copy url http://localhost:3000/locations/__repository__etl@extract_transform_load.py/jobs/etl 

Run launchpad (ETL job will starts executing)

once etl run gets completed 

open from docker container "dashboard" open port 5006:5006 /copy url (http://localhost:5006/dashboard) 

