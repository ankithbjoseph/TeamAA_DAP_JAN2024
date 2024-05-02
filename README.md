# TeamAA_DAP_JAN2024
Database and Analytics Programming Team Project 

Team members
1. Ankith Babu Joseph- x23185813
2. Alphons Zacharia James- x23169702
3. Abhilash Janardhanan- x23121424



### Getting Started....

Requirments :
Up and running docker engine in your local PC: [Docker](https://www.docker.com/products/docker-desktop/)

Extract the compressed contents to a folder 

Rename ```.env.sample```  to ```.env``` to set your enviornment variables.

initiate Command Prompt and navigate to  extracted folder  on your system

execute  command :    

```docker compose up -d```

After building all the containers terminal will be detached and docker containers will be up and running

Navigate to container tab in docker 

View **dagster etl** at  [http://localhost:3000/](http://localhost:3000/)

Open launchpad and run the job (ETL job will start executing)

once etl run gets completed successfully 

view the **dashboard** at [http://localhost:5006/dashboard](http://localhost:5006/dashboard) 

