# TeamAA_DAP_JAN2024
Database and Analytics Programming Team Project 

Team members
1. Ankith Babu Joseph- x23185813
2. Alphons Zacharia James- x23169702
3. Abhilash Janardhanan- x23121424


How to Run code?

Requirments :Up and running docker desktop in your local PC: https://www.docker.com/products/docker-desktop/
Extract the folder 
open CMD inside the extracted folder 
type command :    docker compose up -d
after building all the containers terminal will be detached and docker containers will be running
Navigate to container tab in docker 
open port of container dagster etl 3000:3000/copy url http://localhost:3000/locations/__repository__etl@extract_transform_load.py/jobs/etl 
run launchpad (ETL job will starts executing)
once etl run gets completed 
open from docker container dashboard open port 5006:5006 /copy url (http://localhost:5006/dashboard) 

