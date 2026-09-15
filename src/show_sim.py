import json

chunks = json.load(open("data/processed/chunks.json", "r", encoding="utf-8"))
sim = [c for c in chunks if c.get("type") == "simulation" and c.get("sim_id") == "SIM-1000"]

for i, chunk in enumerate(sim):
    print(f"=== CHUNK {i+1} (index: {chunk.get('chunk_index', '?')}) ===")
    print(chunk["text"][:500])
    print("...\n")


    """
    === CHUNK 1 (index: 0) ===
Crash Simulation Report: SIM-1000
Project: Atlas-X (C-segment SUV)
Project Phase: Series Development
Load Case: IIHS Small Overlap Front (SOF)
Barrier: 25% Rigid Barrier, Impact Velocity: 64 km/h
Solver: LS-DYNA R13.0, Termination Time: 120 ms
Engineer: S. Takahashi, Date: 2022-06-13
Minimum Timestep: 0.00068 ms, Mass Scaling: None

Results:
  Peak Intrusion: 144.4 mm
  Peak Force: 410.1 kN
  Energy Absorbed: 60.7 kJ
  Status: Completed
  Engineer Notes: Increased mesh density in front rail crus
...

=== CHUNK 2 (index: 1) ===
Crash Simulation Report: SIM-1000
Project: Atlas-X (C-segment SUV)
Project Phase: Series Development
Load Case: IIHS Small Overlap Front (SOF)
Barrier: 25% Rigid Barrier, Impact Velocity: 64 km/h
Solver: LS-DYNA R13.0, Termination Time: 120 ms
Engineer: S. Takahashi, Date: 2022-06-13
Minimum Timestep: 0.00068 ms, Mass Scaling: None

Results:
  Peak Intrusion: 144.4 mm
  Peak Force: 410.1 kN
  Energy Absorbed: 60.7 kJ
  Status: Completed
  Engineer Notes: Increased mesh density in front rail crus
...
    """