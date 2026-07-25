

This database contains seed data engineered to test the analytical logic and confirm that the Excel conditional formatting breaks past the > 5.0 warning threshold perfectly.
## Why this data triggers the alert
The pipeline uses a risk formula based on traffic volume density loops:

$\text{Adjusted Crash Rate} = \left( \frac{\text{Total Crash Count}}{\text{Daily Traffic Volume Index}} \right) \times 10,000$

The script maps specific speed zones to typical baseline vehicle volumes (e.g., 25 mph zones have a low capacity index of 12,000 daily vehicles, while 65 mph interstates handle 95,000).
The table modifications inside this database generate:

   1. The Target (High Risk): 10 distinct crash incidents inside a residential 25 mph zone. Because of the lower traffic pool, the mathematical exposure rate resolves to 8.33. This value sits above the 5.0 limit and will flag row items as red.
   2. The Control (Low Risk): 3 crash incidents logged across high-speed 65 mph highway loops. Spread over a major traffic baseline, its exposure index falls to a safe 0.32 and avoids any color overlay changes.

