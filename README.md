# backend-service

Python Flask backend

## Boilerplate

This repository contains boilerplate codes to build an API service using Python Flask.


## Step by step

A sample endpoint for Calculate Square is in this repo, where you can `POST` to the API endpoint `/square`.

- Go to `square.py` under `app/routes` folder in this template and you will find a post method with name  `/square`
- Write your implementation in this method. This method will be the entry point when you submit your solution for evaluation
- Note the __init__.py file in each folder. This file makes Python treat directories containing it to be loaded in a module

## To run

You will first need to have Python's `virtualenv`. Below are the instructions for Windows.

```sh
pip install virtualenv
```

Next up, create the virtual environment.

```sh
python -m venv venv
```

You can run/activate the virtual environment and install the required packages.

```sh
.\venv\Scripts\activate
pip install -r requirements.txt
```

Finally, run the services!

```sh
python app.py
```
