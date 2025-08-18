# Electric Vehicle Smart Charging (In Progess)

This project is a demonstration of Electric Vehicle (EV) Smart Charging concept. 
The context is simple, a Charge Point Operator (CPO) managing many charging terminals determines when and at what power to give to each terminal, 
depending on vehicles' needs (arrival, departure, nominal charging power and required energy).   


This project provides a day-ahead planning algorithm for a typical CPO, based on Linear Programming and Mixed Integer Linear Programming. 
In addition, simple APIs (`FastAPI`) and a simple Dashboard application (`dash`) are also developed. 


<p align="center">
  <a href="">
      <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://fastapi.tiangolo.com">
      <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" alt="FastAPI">
  </a>
  <a href="https://docs.pydantic.dev/2.4/">
      <img src="https://img.shields.io/badge/Pydantic-E92063?logo=pydantic&logoColor=fff&style=for-the-badge" alt="Pydantic">
  </a>
  <a href="https://redis.io">
      <img src="https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=fff&style=for-the-badge" alt="Redis">
  </a>
</p>


## Requirement & Installation 

## Project Structure 
```
├───api
    ├───routers
    ├───schemas
    ├───tests
    │   ├───data
├───dashboard
    ├───assets
    ├───pages
    ├───tests
├───examples
├───planner
├───utility
    ├───data
    ├───kpi
    ├───logger
    ├───tests
```

## First Use
