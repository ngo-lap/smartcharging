# Electric Vehicle Smart Charging (In Progess)

This project is a demonstration of Electric Vehicle (EV) Smart Charging concept. 
The context is simple, a Charge Point Operator (CPO) managing many charging terminals determines when and at what power to give to each terminal, 
depending on vehicles' needs (arrival, departure, nominal charging power and required energy) and infrastructure limit (transformer power capacity).    


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
├───api            # API for calling the planner  
    ├───routers
    ├───schemas
    ├───tests
    │   ├───data
├───dashboard      # Simple dash page for EV Day-ahead Planning 
    ├───assets
    ├───pages
    ├───tests
├───examples       # Examples of running the planner
├───planner        # Algorithms for the EV Smart Charging Planner 
├───utility        # Other tools 
    ├───data
    ├───kpi
    ├───logger
    ├───tests
```

## Description of the Mathematical Problem

## API 

## Dashboard Application 

With 40 vehicles and a infrastructure capacity of 100kW, the planner gives the following results for a horizon of 24 hours, with 15-minute time step. 


#### Total Station Power (kW)
This Figure visualizes the total charging power (kW) withdrawn from electricity grid (blue line), along with the infrastructure power capacity (dash red line). 
<img width="1592" height="450" alt="example_station_power" src="https://github.com/user-attachments/assets/91c4b7db-11de-4c29-b702-d91d6bb398c6" />

#### Individual Vehicles Charging Powers (kW)
Vehicles charging powers are visualized in form of heatmap, where the x axis is the time, y axis is the vehicle and the color represents the assigned charging power. 
<img width="1592" height="450" alt="example_vehicle_power" src="https://github.com/user-attachments/assets/3f8eae57-65b3-4f3d-9273-ba2298270c0a" />

#### Station KPIs 
<img width="791" height="495" alt="example_kpi" src="https://github.com/user-attachments/assets/8aea4793-2e5b-4081-954e-0943e819967e" tag="station_kpi"/>

## First Use



