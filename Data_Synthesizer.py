import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import Forensic_kernel as kernel

def generate_macro_sentinel_telemetry():
    print("Initializing Unconstrained Planetary Telemetry Synthesizer...")
    
    # 100-year simulated run sampled at weekly intervals (~5,200 steps per zone)
    start_date = datetime(2026, 5, 20)
    total_steps = 5200
    timestamps = [start_date + timedelta(weeks=i) for i in range(total_steps)]
    
    zones = [
        "ZONE-01-AMOC-CONVEYOR",
        "ZONE-02-JET-STREAM-ENVELOPE",
        "ZONE-03-CONTROL-BASELINE"
    ]
    
    master_frames = []
    
    for zone in zones:
        data = {
            "timestamp": [ts.strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps],
            "sensor_id": [zone] * total_steps
        }
        
        # Timeline phase thresholds
        # Stage 1 (Sub-resolution drift): Weeks 0 to 2500
        # Stage 1 (Mid-point degradation): Weeks 2501 to 4800
        # Stage 1 (Late-stage pre-collapse): Weeks 4801 to 5100
        # Stage 2 (Catastrophic Bifurcation): Weeks 5101 to 5200
        
        # 1. Primary Observable Matrix (e.g., Crystalline Density / Salinity Titration Fractions)
        # Nominal target baseline = 35.00000000 parts per thousand
        observed_value = np.full(total_steps, 35.00000000)
        
        # 2. Power Matrix (e.g., Heat Transport Velocity / Thermal Exchange Delta in Megawatts)
        # Nominal baseline = 1000.00000000 MW
        power_matrix = np.full(total_steps, 1000.00000000)
        
        # 3. Spatial Displacement Metric (e.g., Boundary Tracking Drift in Kilometers)
        # Nominal baseline = 0.00000000 km deviation
        displacement_vector = np.zeros(total_steps)
        
        # Inject stochastic white noise floor strictly below the 1e-7 titration gate
        noise_floor = np.random.normal(0, 2e-8, total_steps)
        observed_value += noise_floor
        
        if zone == "ZONE-01-AMOC-CONVEYOR":
            for t in range(total_steps):
                # Phase A: Early Stage 1 - Micro-titration drift hidden beneath surface noise
                if t <= 2500:
                    observed_value[t] -= (t * 1e-8)  # Linear micro-decay
                    
                # Phase B: Mid Stage 1 - Crossing the 0.07 Margin Gate, thermal engine brakes drag
                elif 2500 < t <= 4800:
                    observed_value[t] -= (2500 * 1e-8) + ((t - 2500) * 5e-7)
                    power_matrix[t] -= (t - 2500) * 0.15  # Thermal energy loss begins
                    
                # Phase C: Late Stage 1 - Power Ghost arms, exponential acceleration toward cliff
                elif 4800 < t <= 5100:
                    dt = t - 4800
                    observed_value[t] -= (2500 * 1e-8) + (2300 * 5e-7) + (dt * dt * 2e-5)
                    power_matrix[t] -= (2300 * 0.15) + (dt * 1.8)  # Sharp power crash
                    displacement_vector[t] += dt * 0.15  # Boundary begins to drift outward
                    
                # Phase D: Stage 2 - Absolute Veto Gate crossed. The 200km Catastrophic Jump
                else:
                    dt_stage2 = t - 5100
                    observed_value[t] -= 2.5  # Complete chemical saturation failure
                    power_matrix[t] -= 600.0  # Total loss of kinetic circulation
                    # The Utrecht Tipping Point: 200km northward vector shift executing in a 2-year window
                    displacement_vector[t] += 45.0 + (np.log1p(dt_stage2) * 35.0)
                    
        elif zone == "ZONE-02-JET-STREAM-ENVELOPE":
            # Jet Stream tracks a parallel atmospheric amplification decay curve
            for t in range(total_steps):
                if t > 3000:
                    # Slower, wavy deceleration profile
                    observed_value[t] -= np.sin(t / 100) * (t - 3000) * 1e-6
                    power_matrix[t] -= (t - 3000) * 0.08
                    if t > 4900:
                        displacement_vector[t] += (t - 4900) * 0.4
                        
        elif zone == "ZONE-03-CONTROL-BASELINE":
            # Remains completely un-degraded to verify engine fidelity and shield against false flags
            pass

        data["observed_value"] = observed_value
        data["power_matrix"] = power_matrix
        data["spatial_displacement"] = displacement_vector
        
        df_zone = pd.DataFrame(data)

        row_hashes = []
        for idx, row in df_zone.iterrows():
            row_dict = row.to_dict()
            if row_hashes:
                row_dict["prev_hash"] = row_hashes[-1]
            row_hashes.append(kernel.generate_stateless_row_hash(row_dict))

        df_zone["row_hash"] = row_hashes
        master_frames.append(df_zone)

    MASTER_TELEMETRY = pd.concat(master_frames, ignore_index=True)
    os.makedirs("data", exist_ok=True)
    filename = os.path.join("data", "MACRO_SYSTEM_PLANETARY_STREAM.csv")
    MASTER_TELEMETRY.to_csv(filename, index=False)
    print(f"Success. Generated structural dataset profile: {filename} ({len(MASTER_TELEMETRY)} total rows synced).")

if __name__ == "__main__":
    generate_macro_sentinel_telemetry()
