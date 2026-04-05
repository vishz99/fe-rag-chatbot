import csv

sims = list(csv.DictReader(open("data/raw/simulations.csv", "r")))
comps = list(csv.DictReader(open("data/raw/components.csv", "r")))
contacts = list(csv.DictReader(open("data/raw/contacts.csv", "r")))

# Show all simulations
print("=== ALL SIMULATIONS ===")
for s in sims:
    print(f"{s['sim_id']} | {s['project_name']:12} | {s['load_case_code']:5} | {s['engineer']:15} | intrusion={s['peak_intrusion_mm']}mm | {s['status']}")

# Show components for specific sims
for sid in ["SIM-1000", "SIM-1010", "SIM-1020"]:
    print(f"\n=== COMPONENTS: {sid} ===")
    for c in comps:
        if c["sim_id"] == sid:
            print(f"  {c['component_name']:30} | {c['material_grade']:25} | {c['mat_keyword']:10} | {c['element_formulation']:10} | {c['strain_rate_model']}")

# Show which sims have B-pillar data
print("\n=== B-PILLAR ENTRIES ===")
for c in comps:
    if "B-Pillar" in c["component_name"]:
        sim = next((s for s in sims if s["sim_id"] == c["sim_id"]), None)
        if sim:
            print(f"  {c['sim_id']} | {sim['project_name']:12} | {c['material_grade']:25} | {c['mat_keyword']} | {c['element_formulation']}")
