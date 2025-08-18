# Electric Vehicle Smart Charging (In Progess)

This project is a demonstration of Electric Vehicle (EV) Smart Charging concept. 
The context is simple, a Charge Point Operator (CPO) managing many charging terminals determines when and at what power to give to each terminal, 
depending on vehicles' needs (arrival, departure, nominal charging power and required energy) and infrastructure limit (transformer power capacity).    


This project provides a day-ahead planning algorithm for a typical CPO, based on Linear Programming and Mixed Integer Linear Programming. 
In addition, an API and Dashboard application are built using [FastAPI](https://fastapi.tiangolo.com/) and [Plotly Dash](https://dash.plotly.com/).
The optimization problem is formulated using [CVXPY](https://www.cvxpy.org/). The planner algorithm uses the solver [HiGHS](https://github.com/ERGO-Code/HiGHS) and [CLARABEL](https://github.com/oxfordcontrol/Clarabel.rs) for MILP and LP formulation, respectively.  


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



- Step 1: Clone the repo

  `git clone <repo-link>`

- Step 2: install requirement

  `pip install -r requirements.txt`

The API and dashboard application can be launched separately by running `core\api\main.py` and `core\dashboard\main.py`, respectively. 
 
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

## Planner example:

This example concerns the charge planning for 40 vehicles, a infrastructure capacity of 100kW, for a horizon of 24 hours, with 15-minute time step. 
The first step is to get the prediction for EV charging demand, given in the following table: 

|    |   vehicle |   powerNom |   energyRequired |   energyMax | arrivalTime         | departureTime       |   parkingDuration |
|---:|----------:|-----------:|-----------------:|------------:|:--------------------|:--------------------|------------------:|
|  0 |         0 |         22 |          26      |          52 | 2025-08-18 11:59:53 | 2025-08-18 16:46:38 |           4.77917 |
|  1 |         1 |          7 |          17.6711 |          30 | 2025-08-18 08:18:18 | 2025-08-18 10:49:46 |           2.52444 |
|  2 |         2 |         11 |          45.815  |          52 | 2025-08-18 10:26:38 | 2025-08-18 14:36:32 |           4.165   |
|  3 |         3 |         11 |          27.9156 |          88 | 2025-08-18 14:47:47 | 2025-08-18 17:20:03 |           2.53778 |
|  4 |         4 |          6 |          20.305  |          88 | 2025-08-18 08:10:04 | 2025-08-18 11:33:07 |           3.38417 |

  where:

  - `vehicle`: vehicle ID or index
  - `powerNom`: nominal power (kW) of the vehicle 
  - `energyRequired`: the charging energy (kWh) requested by the vehicle
  - `energyMax`: the capacity (kWh) of the vehicle's battery
  - `arrivalTime`: arrival time of the vehicle, assuming it is plugged in immediately
  - `departureTime`: departure time of the vehicle
  - `parkingDuration`: parking duration (hour) of the vehicle, i.e. `= departureTime - arrivalTime`
    
This table can be synthetically generated using `generate_demand_data` function:

```
    from core.utility.data.data_processor import generate_demand_data

    # Parameters
    nVE = 40
    time_step = 900         # [Seconds] time step of the planning horizon
    horizon_length = 96     # [Time Step] the horizon length
    capacity = 100          # [kW] infrastructure capacity
    
    # Generate demand data
    data_sessions = generate_demand_data(
        nbr_vehicles=nVE, horizon_length=horizon_length, time_step=time_step, horizon_start=horizon_start
    )
```


#### Total Station Power (kW)
This Figure visualizes the total charging power (kW) withdrawn from electricity grid (blue line), along with the infrastructure power capacity (dash red line). 
<img width="1592" height="450" alt="example_station_power" src="https://github.com/user-attachments/assets/91c4b7db-11de-4c29-b702-d91d6bb398c6" />

#### Individual Vehicles Charging Powers (kW)
Vehicles charging powers are visualized in form of heatmap, where the x axis is the time, y axis is the vehicle and the color represents the assigned charging power. 
<img width="1592" height="450" alt="example_vehicle_power" src="https://github.com/user-attachments/assets/3f8eae57-65b3-4f3d-9273-ba2298270c0a" />

#### Station KPIs 
<img width="791" height="495" alt="example_kpi" src="https://github.com/user-attachments/assets/8aea4793-2e5b-4081-954e-0943e819967e" tag="station_kpi"/>


## API 
The api can be launched by running the `core\api\main.py` script. 

## Dashboard Application 
The api can be launched by running the `core\dashboard\main.py` script. 




