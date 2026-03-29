import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

# This script generates the synthetic "Project database" that is to be utilized in this RAG project

# ============================================================
# REFERENCE DATA
# ============================================================

vehicle_programs = [
    {"name": "Atlas-X", "segment": "C-segment SUV", "oem_phase": "Series Development"},
    {"name": "Meridian-3", "segment": "D-segment Sedan", "oem_phase": "Concept Validation"},
    {"name": "Vanguard-E", "segment": "B-segment Hatchback (BEV)", "oem_phase": "Detailed Design"},
    {"name": "Titan-R", "segment": "Full-size Pickup Truck", "oem_phase": "Pre-Production"},
    {"name": "Nova-S", "segment": "A-segment City Car", "oem_phase": "Series Development"},
    {"name": "Pinnacle-7", "segment": "E-segment Luxury Sedan", "oem_phase": "Concept Validation"},
]

load_cases = [
    {"type": "Euro NCAP Full-Width Frontal", "code": "FWDB", "barrier": "Full-Width Deformable Barrier", "velocity_kmh": 50, "termination_ms": 120},
    {"type": "Euro NCAP ODB Frontal", "code": "ODB", "barrier": "Offset Deformable Barrier (40%)", "velocity_kmh": 64, "termination_ms": 120},
    {"type": "Euro NCAP Side MDB", "code": "SMDB", "barrier": "Mobile Deformable Barrier 1400kg", "velocity_kmh": 60, "termination_ms": 100},
    {"type": "Euro NCAP Side Pole", "code": "SPOL", "barrier": "254mm Rigid Pole", "velocity_kmh": 32, "termination_ms": 80},
    {"type": "IIHS Small Overlap Front", "code": "SOF", "barrier": "25% Rigid Barrier", "velocity_kmh": 64, "termination_ms": 120},
    {"type": "FMVSS 301 Rear Impact", "code": "REAR", "barrier": "Moving Deformable Barrier 1368kg", "velocity_kmh": 80, "termination_ms": 150},
    {"type": "Roof Crush (FMVSS 216)", "code": "ROOF", "barrier": "Rigid Platen", "velocity_kmh": 0, "termination_ms": 200},
    {"type": "Low-Speed Bumper (RCAR)", "code": "RCAR", "barrier": "RCAR Barrier", "velocity_kmh": 15, "termination_ms": 100},
]

engineers = ["M. Weber", "S. Takahashi", "A. Fernandez", "L. Schmidt", "P. Nguyen", "R. Johansson"]

solver_versions = ["R12.0", "R13.0", "R13.1", "R14.0", "R15.0"]

# Components with realistic LS-DYNA parameters
# Format: name, typical_materials, typical_mat_keywords, typical_elforms, thickness_range, is_structural
components_db = [
    {"name": "Front Bumper Beam", "materials": ["DP600", "DP780", "AL6082-T6"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.4, 2.5), "mesh_size": (4, 6), "structural": True},
    {"name": "Front Crash Rails (Left)", "materials": ["DP780", "DP980", "CP1000"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_124"], "elforms": [2, 16], 
     "thickness": (1.2, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "Front Crash Rails (Right)", "materials": ["DP780", "DP980", "CP1000"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_124"], "elforms": [2, 16], 
     "thickness": (1.2, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "Shotgun Inner (Left)", "materials": ["DP600", "DP780"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.0, 1.8), "mesh_size": (4, 6), "structural": True},
    {"name": "Shotgun Inner (Right)", "materials": ["DP600", "DP780"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.0, 1.8), "mesh_size": (4, 6), "structural": True},
    {"name": "Firewall", "materials": ["DC04", "DP600"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (0.7, 1.2), "mesh_size": (5, 8), "structural": True},
    {"name": "A-Pillar (Left)", "materials": ["22MnB5 (Hot Stamped)", "DP1000"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.0, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "A-Pillar (Right)", "materials": ["22MnB5 (Hot Stamped)", "DP1000"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.0, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "B-Pillar (Left)", "materials": ["22MnB5 (Hot Stamped)", "DP1000", "Tailor-Welded 22MnB5/DP600"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.2, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "B-Pillar (Right)", "materials": ["22MnB5 (Hot Stamped)", "DP1000", "Tailor-Welded 22MnB5/DP600"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.2, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "Rocker Panel / Sill (Left)", "materials": ["DP780", "CP1000", "22MnB5 (Hot Stamped)"], 
     "mat_keywords": ["*MAT_024", "*MAT_124", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.0, 1.8), "mesh_size": (4, 6), "structural": True},
    {"name": "Rocker Panel / Sill (Right)", "materials": ["DP780", "CP1000", "22MnB5 (Hot Stamped)"], 
     "mat_keywords": ["*MAT_024", "*MAT_124", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.0, 1.8), "mesh_size": (4, 6), "structural": True},
    {"name": "Floor Pan", "materials": ["DC04", "DP600", "BH210"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_024"], "elforms": [2], 
     "thickness": (0.65, 1.0), "mesh_size": (6, 10), "structural": True},
    {"name": "Tunnel Reinforcement", "materials": ["DP780", "DP980"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.2, 2.0), "mesh_size": (4, 6), "structural": True},
    {"name": "Roof Panel", "materials": ["BH210", "DC04", "AL5182"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_024"], "elforms": [2], 
     "thickness": (0.65, 0.8), "mesh_size": (6, 10), "structural": False},
    {"name": "Roof Bow (Front)", "materials": ["DP600", "DP780"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2], 
     "thickness": (0.8, 1.2), "mesh_size": (4, 6), "structural": True},
    {"name": "Door Intrusion Beam (Left Front)", "materials": ["22MnB5 (Hot Stamped)", "DP1000", "Tubular Steel"], 
     "mat_keywords": ["*MAT_024", "*MAT_024", "*MAT_024"], "elforms": [2, 16, 1], 
     "thickness": (1.0, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "Door Intrusion Beam (Left Rear)", "materials": ["22MnB5 (Hot Stamped)", "DP1000"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.0, 2.0), "mesh_size": (3, 5), "structural": True},
    {"name": "Rear Bumper Beam", "materials": ["DP600", "AL6082-T6"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (1.4, 2.5), "mesh_size": (4, 6), "structural": True},
    {"name": "Battery Housing (BEV only)", "materials": ["AL6061-T6", "AL5754"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 16], 
     "thickness": (2.0, 4.0), "mesh_size": (4, 6), "structural": True},
    {"name": "Subframe Front", "materials": ["DP600", "AL6061-T6 (Cast)"], 
     "mat_keywords": ["*MAT_024", "*MAT_024"], "elforms": [2, 1], 
     "thickness": (2.5, 4.0), "mesh_size": (4, 8), "structural": True},
    {"name": "Engine Block (Rigid)", "materials": ["Cast Iron (Rigid)"], 
     "mat_keywords": ["*MAT_020"], "elforms": [1], 
     "thickness": (0, 0), "mesh_size": (8, 15), "structural": False},
    {"name": "Steering Column", "materials": ["Steel (Rigid + Deformable)"], 
     "mat_keywords": ["*MAT_024"], "elforms": [1, 2], 
     "thickness": (1.5, 2.5), "mesh_size": (4, 6), "structural": False},
]

contact_types = [
    {"keyword": "*CONTACT_AUTOMATIC_SINGLE_SURFACE", "description": "General self-contact for all sheet metal parts", "friction": (0.1, 0.2)},
    {"keyword": "*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE", "description": "Part-to-part contact", "friction": (0.1, 0.3)},
    {"keyword": "*CONTACT_TIED_SHELL_EDGE_TO_SURFACE", "description": "Spot weld representation", "friction": (0.0, 0.0)},
    {"keyword": "*CONTACT_TIED_SURFACE_TO_SURFACE", "description": "Adhesive bond or tied constraint", "friction": (0.0, 0.0)},
    {"keyword": "*CONTACT_AUTOMATIC_NODES_TO_SURFACE", "description": "Barrier-to-vehicle contact", "friction": (0.2, 0.4)},
]

hourglass_types = [
    {"ihq": 4, "qm": 0.03, "description": "Flanagan-Belytschko stiffness form (default)"},
    {"ihq": 5, "qm": 0.05, "description": "Flanagan-Belytschko viscous form"},
    {"ihq": 6, "qm": 0.03, "description": "Belytschko-Bindeman assumed strain"},
    {"ihq": 8, "qm": 0.1, "description": "Warping stiffness for shells"},
]

strain_rate_models = [
    {"model": "Cowper-Symonds", "params": "C=40.4, p=5 (typical for mild steel)"},
    {"model": "Cowper-Symonds", "params": "C=802, p=3.585 (DP600)"},
    {"model": "Cowper-Symonds", "params": "C=1522, p=4.8 (DP780)"},
    {"model": "None (quasi-static material curve)", "params": "N/A"},
    {"model": "Tabulated strain rate curves", "params": "LCSR with 5 curves at 0.001, 0.1, 10, 100, 500 /s"},
]

engineer_notes_templates = [
    "Baseline run. All parameters from previous project carried over. Good correlation with test {test_id}.",
    "Increased mesh density in {region} to capture local buckling. Runtime increased by {pct}%.",
    "Changed {component} material from {old_mat} to {new_mat} per material team recommendation. Improved energy absorption by {val} kJ.",
    "Hourglass energy exceeds 5% threshold in {component}. Switched from IHQ={old_ihq} to IHQ={new_ihq}. Resolved.",
    "Added Cowper-Symonds strain rate effects to {component}. Peak force increased by {pct}% compared to quasi-static.",
    "Timestep controlled by {component} (element {eid}). Added mass scaling DTMS={dtms}. Total added mass < 1%.",
    "Spotweld failure pattern does not match test. Adjusted MAT_100 parameters: SN={sn}, SS={ss}.",
    "Contact penetration detected between {comp1} and {comp2}. Increased SLSFAC to {slsfac}. Resolved.",
    "Run failed at t={t}ms due to negative volume in {component}. Refined mesh locally and restarted.",
    "Final correlation run for {loadcase}. Intrusion within {val}mm of test. Signed off by {eng}.",
    "Sensitivity study: varied {component} thickness from {t1}mm to {t2}mm. Optimal at {t_opt}mm.",
    "BEV battery housing integrity check: no cell deformation above {val}mm threshold. PASS.",
    "Door opening force check post-crash: simulated via springback analysis. Door opens within spec.",
    "Dummy kinematics show head contact with A-pillar trim. Added padding per interior team request.",
]

# ============================================================
# GENERATE SIMULATIONS
# ============================================================

simulations = []
sim_id = 1000

for vp in vehicle_programs:
    n_runs = random.randint(4, 7)
    base_date = datetime(2022, 6, 1) + timedelta(days=random.randint(0, 500))
    
    for run_idx in range(n_runs):
        lc = random.choice(load_cases)
        eng = random.choice(engineers)
        solver = random.choice(solver_versions)
        run_date = base_date + timedelta(days=run_idx * random.randint(3, 21))
        
        # Generate realistic results based on load case
        if lc["code"] in ["FWDB", "ODB", "SOF"]:
            peak_intrusion = round(random.uniform(45, 180), 1)
            peak_force = round(random.uniform(180, 520), 1)
            energy_absorbed = round(random.uniform(25, 65), 1)
        elif lc["code"] in ["SMDB", "SPOL"]:
            peak_intrusion = round(random.uniform(80, 280), 1)
            peak_force = round(random.uniform(40, 180), 1)
            energy_absorbed = round(random.uniform(8, 30), 1)
        elif lc["code"] == "REAR":
            peak_intrusion = round(random.uniform(30, 120), 1)
            peak_force = round(random.uniform(60, 200), 1)
            energy_absorbed = round(random.uniform(15, 40), 1)
        elif lc["code"] == "ROOF":
            peak_intrusion = round(random.uniform(10, 50), 1)
            peak_force = round(random.uniform(60, 150), 1)
            energy_absorbed = round(random.uniform(5, 20), 1)
        else:
            peak_intrusion = round(random.uniform(5, 30), 1)
            peak_force = round(random.uniform(20, 80), 1)
            energy_absorbed = round(random.uniform(2, 10), 1)
        
        status = random.choices(["Completed", "Completed", "Completed", "Completed", "Terminated - Negative Volume", "Completed - High HG Energy Warning"], weights=[60, 20, 10, 5, 3, 2])[0]
        
        dt = round(random.uniform(0.3e-3, 1.2e-3), 6)
        mass_scaling = random.choice(["None", "None", "None", "DTMS=0.9e-3", "DTMS=0.8e-3"])
        
        # Generate a note
        note_template = random.choice(engineer_notes_templates)
        note = note_template.format(
            test_id=f"T{random.randint(100,999)}", region="front rail crush zone",
            pct=random.randint(8, 35), component=random.choice(["B-pillar", "front rails", "bumper beam", "floor pan"]),
            old_mat="DP600", new_mat="DP780", val=round(random.uniform(1.5, 8.0), 1),
            old_ihq=4, new_ihq=6, eid=random.randint(100000, 999999),
            dtms="0.9e-3", comp1="front rail", comp2="subframe", slsfac=round(random.uniform(0.08, 0.15), 3),
            t=round(random.uniform(20, 80), 1), loadcase=lc["type"],
            eng=random.choice(engineers), t1=round(random.uniform(1.0, 1.5), 1),
            t2=round(random.uniform(2.0, 3.0), 1), t_opt=round(random.uniform(1.5, 2.2), 1),
            sn=round(random.uniform(3.0, 8.0), 1), ss=round(random.uniform(2.0, 6.0), 1),
        )
        
        sim = {
            "sim_id": f"SIM-{sim_id}",
            "project_name": vp["name"],
            "vehicle_segment": vp["segment"],
            "project_phase": vp["oem_phase"],
            "load_case": lc["type"],
            "load_case_code": lc["code"],
            "barrier_type": lc["barrier"],
            "impact_velocity_kmh": lc["velocity_kmh"],
            "termination_time_ms": lc["termination_ms"],
            "solver_version": f"LS-DYNA {solver}",
            "engineer": eng,
            "date": run_date.strftime("%Y-%m-%d"),
            "min_timestep_ms": dt,
            "mass_scaling": mass_scaling,
            "peak_intrusion_mm": peak_intrusion,
            "peak_force_kn": peak_force,
            "energy_absorbed_kj": energy_absorbed,
            "status": status,
            "notes": note,
        }
        simulations.append(sim)
        sim_id += 1

# ============================================================
# GENERATE COMPONENTS
# ============================================================

component_rows = []
comp_id = 1

for sim in simulations:
    # Select subset of components (12-18 per sim)
    is_bev = "BEV" in sim["vehicle_segment"]
    available = [c for c in components_db if c["name"] != "Battery Housing (BEV only)" or is_bev]
    n_comps = random.randint(12, min(18, len(available)))
    selected = random.sample(available, n_comps)
    
    for comp_def in selected:
        mat_idx = random.randint(0, len(comp_def["materials"]) - 1)
        material = comp_def["materials"][mat_idx]
        mat_kw = comp_def["mat_keywords"][min(mat_idx, len(comp_def["mat_keywords"])-1)]
        elform = random.choice(comp_def["elforms"])
        
        t_min, t_max = comp_def["thickness"]
        thickness = round(random.uniform(t_min, t_max), 2) if t_max > 0 else 0
        
        m_min, m_max = comp_def["mesh_size"]
        mesh = round(random.uniform(m_min, m_max), 1)
        
        hg = random.choice(hourglass_types)
        sr = random.choice(strain_rate_models)
        
        # Assign number of integration points
        nip = random.choice([3, 5, 5, 5, 7])
        
        part_id = random.randint(1000, 9999)
        
        row = {
            "comp_id": f"COMP-{comp_id:04d}",
            "sim_id": sim["sim_id"],
            "component_name": comp_def["name"],
            "part_id": part_id,
            "material_grade": material,
            "mat_keyword": mat_kw,
            "element_formulation": f"ELFORM={elform}",
            "thickness_mm": thickness,
            "mesh_size_mm": mesh,
            "num_integration_points": nip,
            "hourglass_type": f"IHQ={hg['ihq']} (QM={hg['qm']})",
            "hourglass_description": hg["description"],
            "strain_rate_model": sr["model"],
            "strain_rate_params": sr["params"],
        }
        component_rows.append(row)
        comp_id += 1

# ============================================================
# GENERATE CONTACTS
# ============================================================

contact_rows = []
ct_id = 1

for sim in simulations:
    # Each sim has 5-10 contact definitions
    n_contacts = random.randint(5, 10)
    
    for _ in range(n_contacts):
        ct = random.choice(contact_types)
        friction = round(random.uniform(ct["friction"][0], ct["friction"][1]), 2)
        
        master_parts = random.sample(range(1000, 9999), 2)
        
        row = {
            "contact_id": f"CT-{ct_id:04d}",
            "sim_id": sim["sim_id"],
            "contact_keyword": ct["keyword"],
            "contact_description": ct["description"],
            "static_friction": friction,
            "dynamic_friction": round(friction * 0.8, 2) if friction > 0 else 0,
            "master_set_id": master_parts[0],
            "slave_set_id": master_parts[1],
            "soft_constraint": random.choice([0, 1, 2]),
            "ignore_initial_penetration": random.choice(["Yes", "Yes", "No"]),
        }
        contact_rows.append(row)
        ct_id += 1

# ============================================================
# WRITE CSVs
# ============================================================

out_dir = "/home/claude/synthetic_db"
os.makedirs(out_dir, exist_ok=True)

# Simulations
with open(f"{out_dir}/simulations.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=simulations[0].keys())
    writer.writeheader()
    writer.writerows(simulations)

# Components
with open(f"{out_dir}/components.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=component_rows[0].keys())
    writer.writeheader()
    writer.writerows(component_rows)

# Contacts
with open(f"{out_dir}/contacts.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=contact_rows[0].keys())
    writer.writeheader()
    writer.writerows(contact_rows)

print(f"Generated {len(simulations)} simulations")
print(f"Generated {len(component_rows)} component entries")
print(f"Generated {len(contact_rows)} contact definitions")
print(f"Vehicle programs: {[v['name'] for v in vehicle_programs]}")
print(f"Files saved to {out_dir}/")

