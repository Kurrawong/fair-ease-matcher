# Components

# src folder
Contains code for the application. Much of this code is no longer used and needs to be cleaned up. Do not spend effort
trying to understand it until it has been cleaned up - I have mentioned the key files that are used below.

The Python environment and requirements are handled using [Poetry](https://python-poetry.org/) - please install poetry and run `poetry install` to 
setup the environment/requirements. See the Dockerfile for an example of this.
# src/app/flask_app.py

The flask application used to run the analyser at https://99koor0nmj.execute-api.ap-southeast-2.amazonaws.com/production/process_metadata
The analyser is running as an AWS Lambda function.
The analyser is packaged/deployed using Zappa. Zappa makes it easy to deploy python applications on AWS Lambda. The Zappa config for this is in `./zappa_settings.json`

# src/app/fastapi_app.py

FastAPI is an async equivalent to Flask. It is what I would have used if not deploying the application on AWS Lambda. 
Async apps on AWS Lambda are possible but have some pitfalls. The FastAPI app is not deployed anywhere.

# src/app/main.py

Equivalent to `flask_app.py` but to just run the script on local files.

# compose directory
Can be used to process the Vocab data locally and run a Fuseki instance. **You will need a copy of the vocab files from 
me - these are in S3 and too large to sensibly check in to version control - these can be provided on request**

NB the compose app is *not* set up to run the analyser itself. You can run the analyser via and IDE and point it to 
Fuseki running in compose.

# Dockerfile
Not currently used.
Was used to build a docker image for the fastapi version of the analyser.
Expect this will require some minor changes but will work again with the flask or fastapi versions.

# notebooks directory
Not currently used.
Was used to demonstrate an alternate version of the analyser using LLMs.

# aws directory
Not currently used.
Contains information on connecting to an AWS Neptune instance that was previously stood up for the LLM version. This 
instance has now been removed as Fuseki is online.