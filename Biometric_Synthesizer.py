import os
import datetime

import numpy as np
import pandas as pd

from resign_telemetry_chain import resign_telemetry_chain


def generate_biomedical_stream(
    filename: str = os.path.join("data", "BIOMETRIC_SENTINEL_STREAM.csv"),
    rows: int = 5000,
):
    print("Initializing high-fidelity biomedical simulation asset generation...")

    # Establish a continuous high-frequency temporal baseline (5-second increments)
    start_time = datetime.datetime(2026, 6, 1, 0, 0, 0)
    timestamps = [start_time + datetime.timedelta(seconds=5 * i) for i in range(rows)]

    data_records = []

    # Define clinical zone/sensor targets to iterate through
    zones = ["ZONE-01-AUTONOMIC-TREMOR", "ZONE-02-METABOLIC-CONTINUUM"]

    for zone in zones:
        np.random.seed(42 if "ZONE-01" in zone else 84)

        # Base physiological parameters
        if "ZONE-01" in zone:
            # Tracking autonomic neurological drift metrics
            base_obs = 0.40       # Baseline sub-visual micro-tremor coordinate
            base_power = 1.20     # Basal Metabolic Power scaling (kcal/min)
            base_shear = 0.01     # Structural autonomic shear delta
        else:
            # Tracking glycemic/endocrine continuum metrics
            base_obs = 5.20       # Baseline glycemic tracking metric
            base_power = 1.50     # Metabolic power reserve allocation
            base_shear = 0.02     # Interstitial volume fluid displacement delta

        for i, ts in enumerate(timestamps):
            # Introduce a transient, high-amplitude cyclical phase excursion
            # Simulated peak execution window occurs roughly between row indices 3500 and 4200
            excursion_factor = 0.0
            if 3500 <= i <= 4200:
                # Sine wave envelope simulating an acute autonomic shock and natural rebalancing arc
                excursion_factor = np.sin(np.pi * (i - 3500) / 700)

            # Compress stochastic physiological noise below the titration ceiling (sigma = 1e-9)
            # so the baseline stays mathematically quiet and kinetic breaches register only
            # inside the explicit cyclical excursion window (rows 3500-4200).
            noise_obs = np.random.normal(0, 1e-9)
            noise_power = np.random.normal(0, 1e-9)
            noise_shear = np.random.normal(0, 1e-9)

            # Inject dynamic values shifting based on the cyclical shock event
            if "ZONE-01" in zone:
                # Acute tremor spike forcing tracking coordinate deviations
                observed_value = base_obs + (0.35 * excursion_factor) + noise_obs
                power_matrix = base_power + (0.50 * excursion_factor) + noise_power
                # Boundary shear breaks past the 0.05 U limit during peak excursion window
                spatial_displacement = base_shear + (0.06 * excursion_factor) + noise_shear
            else:
                # Severe metabolic/insulin titration decoupling shift
                observed_value = base_obs - (1.80 * excursion_factor) + noise_obs
                power_matrix = base_power - (0.40 * excursion_factor) + noise_power
                spatial_displacement = base_shear + (0.04 * excursion_factor) + noise_shear

            # Protect absolute physical boundary limits against negative anomalies
            observed_value = max(0.001, observed_value)
            power_matrix = max(0.001, power_matrix)
            spatial_displacement = max(0.0001, spatial_displacement)

            data_records.append(
                {
                    "sensor_id": zone,
                    "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                    "observed_value": round(observed_value, 8),
                    "power_matrix": round(power_matrix, 8),
                    "spatial_displacement": round(spatial_displacement, 8),
                }
            )

    # Compile array into standard structural Pandas Frame
    df = pd.DataFrame(data_records)
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
    df.to_csv(filename, index=False)

    # Delegate cryptographic sealing to the forensic resign utility so the biometric
    # stream carries a valid per-zone chain of custody (matches Data_Synthesizer.py).
    resign_telemetry_chain(filename)
    print(f"Asset compilation complete. File saved successfully as: '{filename}' ({len(df)} rows mapped).")


if __name__ == "__main__":
    generate_biomedical_stream()
