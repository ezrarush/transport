

This database contains seed data engineered to test the analytical logic and confirm that the Excel conditional formatting breaks past the > 5.0 warning threshold perfectly.
## Why this data triggers the alert
The pipeline uses a risk formula based on traffic volume density loops:

$\text{Adjusted Crash Rate} = \left( \frac{\text{Total Crash Count}}{\text{Daily Traffic Volume Index}} \right) \times 10,000$

The script maps specific speed zones to typical baseline vehicle volumes (e.g., 25 mph zones have a low capacity index of 12,000 daily vehicles, while 65 mph interstates handle 95,000).
The table modifications inside this database generate:

   1. The Target (High Risk): 10 distinct crash incidents inside a residential 25 mph zone. Because of the lower traffic pool, the mathematical exposure rate resolves to 8.33. This value sits above the 5.0 limit and will flag row items as red.
   2. The Control (Low Risk): 3 crash incidents logged across high-speed 65 mph highway loops. Spread over a major traffic baseline, its exposure index falls to a safe 0.32 and avoids any color overlay changes.


# Extend the SQLite schema to track vehicle mechanical failures or autonomous levels

To extend your SQLite schema to track vehicle mechanical failures and autonomous levels, we need to alter our data modeling strategy.
In our original setup, mechanical failures and autonomous levels were simple text and integer fields stuffed directly inside the vehicles table. While that works for small examples, real-world data systems require a normalized schema to ensure clean reporting, handle multi-failure scenarios, and avoid raw data duplication.

------------------------------
## The New Relational Architecture
To properly track these advanced metrics, the SQLite schema should be expanded to include two new lookup tables and one junction table:

   1. dim_autonomy_levels: A dimension lookup table holding the official structural definitions for the SAE (Society of Automotive Engineers) Autonomous Driving Levels (Levels 0 through 5). [1] 
   2. dim_mechanical_failures: A standardized lookup catalog of vehicle mechanical breakdowns (e.g., Brake Failure, Tire Blowout, Steering Loss).
   3. vehicle_failures_bridge: A junction bridge table mapping vehicles to their faults. This handles multi-failure accidents (e.g., if a truck suffers a brake failure and a subsequent steering loss during a single crash sequence).

```
   [ crashes ]
        │ (1:N)
        ▼
   [ vehicles ] ──(N:1)──► [ dim_autonomy_levels ]
        │ (1:N)
        ▼
[ vehicle_failures_bridge ] ◄──(N:1)── [ dim_mechanical_failures ]
```

------------------------------
## Executable Python Script (extend_schema.py)
Here is a complete script that will safely recreate your database (transportation_accidents.db), build out the new normalized tables, establish foreign key constraints, and seed it with realistic autonomous truck and passenger transit vehicle crash sequences.


## Verification Query Example
To extract meaningful analysis from this extended schema, your reporting pipelines can now run complex relational joins. If you connect to this database file using Python or a SQLite GUI viewer, running this sample SQL query will extract a clean log showing precisely which autonomous hardware levels are experiencing failures:

```sql
SELECT 
    v.vehicle_id,
    v.vehicle_type,
    a.sae_name as autonomy_classification,
    f.failure_category,
    f.description as flaw_detail,
    c.weather_conditionFROM vehicles vJOIN dim_autonomy_levels a ON v.autonomous_level = a.autonomy_levelJOIN vehicle_failures_bridge b ON v.vehicle_id = b.vehicle_idJOIN dim_mechanical_failures f ON b.failure_code = f.failure_codeJOIN crashes c ON v.crash_id = c.crash_id;
```

What this outputs from the seeded data:

* It exposes VEH_101 (Commercial Truck) as running at Level 4 (High Driving Automation) while simultaneously registering two separate errors (Sensor Blindness and Braking System Failure) during a single accident tracking sequence under heavy rain. [2] 

------------------------------
## Step-by-Step Running Guide

Run the script inside your terminal using your environment manager to generate the extended database file:
   
   uv run extend_schema.py

# Add a people table to this schema to track injuries across autonomous vehicle types

Here is your updated schema setup script. It expands the database by adding a normalized people table linked directly to the crashes and vehicles architecture. It tracks individual occupants, system roles (e.g., Driver, Pedestrian), age, and their corresponding injury severity code on the standardized KABCO scale.
This script replaces the database file (transportation_accidents.db) with a clean, fully normalized schema and injects realistic test cases—including injuries occurring in standard vehicles versus those inside autonomous vehicle sequences.
## Extended Database Initialization Script (extend_schema.py)


## Try Analytical Cross-Tabulations
With this updated structure in place, you can execute deep data inquiries matching automated system classes with direct health outcomes. Running the sample analytical query below directly returns the counts of fatalities and injuries grouped by the SAE Autonomy Classification Level:

```sql
SELECT 
    a.autonomy_level,
    a.sae_name as autonomy_type,
    p.injury_severity_kabco as severity_code,
    COUNT(p.person_id) as headcount
FROM people p
-- LEFT JOIN handles non-motorist individuals who aren't inside a car (e.g. Pedestrians)
LEFT JOIN vehicles v ON p.vehicle_id = v.vehicle_id
LEFT JOIN dim_autonomy_levels a ON v.autonomous_level = a.autonomy_level
GROUP BY v.autonomous_level, p.injury_severity_kabco
ORDER BY v.autonomous_level ASC, headcount DESC;
```

## Next Steps to Finalize Your System
   
   uv run extend_schema.py
   
# Add a stored SQL view to group demographic crash data by age bands (e.g., under 18, 18-65, 65+)

Here is your updated schema script. This version appends an automated Stored SQL View (view_demographic_safety_summary) directly into the SQLite database engine.
The view uses a conditional CASE statement to bucket individual ages into standardized demographic tiers: 'Under 18', '18-64', and '65+'. It links records across the people, vehicles, and dim_autonomy_levels tables so you can track injury outcomes (KABCO) across different age brackets and vehicle technologies with a single, simple query.
## Database Setup Script with Stored View (extend_schema.py)  

## How to Query the New Stored View
Because the demographic logic is stored inside the database view itself, you no longer have to write messy JOIN or CASE clauses in your application layers. You can select directly from the view as if it were a normal table.
## Example A: View full demographic logs
```sql
SELECT * FROM view_demographic_safety_summary;
```
## Example B: Total injuries by age band and severity

```sql
SELECT 
    age_band, 
    injury_severity, 
    COUNT(person_id) as total_count
FROM view_demographic_safety_summary
GROUP BY age_band, injury_severity
ORDER BY age_band ASC, total_count DESC;
```

## Execution Steps

   
   uv run extend_schema.py
   