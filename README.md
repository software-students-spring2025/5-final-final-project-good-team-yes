![build.yml](https://github.com/software-students-spring2025/5-final-final-project-good-team-yes/actions/workflows/build.yml/badge.svg?branch=main)
![tests.yml](https://github.com/software-students-spring2025/5-final-final-project-good-team-yes/actions/workflows/tests.yml/badge.svg)


# NYC Sandwich Price Tracker

A web application that tracks the price of sausage, egg, and cheese sandwiches from delis across New York City with user input. You can add any deli with any price, and other users will be able to view it. Have fun comparing and contrasting different prices of delis?

## Developers
- Nick Michael https://github.com/NMichael111
- Helen Kao https://github.com/hhelenho
- Isaac Fisher https://github.com/isaac1000000
- Ray Ochotta https://github.com/SnowyOchole


## Dependency Management

This project uses requirements.txt for managing dependencies. To add new dependencies:

1. Add them to requirements.txt
2. Rebuild the Docker image

## Development

Docker containers:
https://hub.docker.com/r/snowyochole/sandwich-mongodb
https://hub.docker.com/r/snowyochole/sandwich-web-app

## Run Locally

### 1. Download Docker Desktop
### 2. Clone our repository
### 3. Run with Docker
```
docker compose up --build
```
### 4. Visit localhost
http://104.236.230.96:5003/


