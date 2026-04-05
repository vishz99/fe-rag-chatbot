"""
Phase 4: Evaluation Test Set
30 questions with known correct answers for systematic testing.
"""

test_questions = [
    # ================================================================
    # CATEGORY 1: MANUAL LOOKUPS (10 questions)
    # Answer should come from LS-DYNA manual
    # ================================================================
    {
        "id": 1,
        "category": "manual",
        "question": "What is *MAT_PIECEWISE_LINEAR_PLASTICITY and what is its material number?",
        "expected": "MAT_024, piecewise linear elasto-plastic material with strain rate effects",
        "key_terms": ["MAT_024", "piecewise", "plasticity"]
    },
    {
        "id": 2,
        "category": "manual",
        "question": "What is the Belytschko-Tsay shell element and why is it widely used?",
        "expected": "Default shell element in LS-DYNA, cost effective, most widely used in crash and metalforming",
        "key_terms": ["Belytschko", "Tsay", "cost", "shell"]
    },
    {
        "id": 3,
        "category": "manual",
        "question": "What does ELFORM=16 refer to in *SECTION_SHELL?",
        "expected": "Fully integrated shell element (type 16), improved accuracy over ELFORM=2",
        "key_terms": ["ELFORM", "16", "fully integrated"]
    },
    {
        "id": 4,
        "category": "manual",
        "question": "What is *CONTACT_AUTOMATIC_SINGLE_SURFACE used for?",
        "expected": "General purpose contact for self-contact, detects contact between all parts in the model",
        "key_terms": ["contact", "automatic", "single", "surface"]
    },
    {
        "id": 5,
        "category": "manual",
        "question": "What is hourglass control and why is it needed?",
        "expected": "Controls zero-energy deformation modes in under-integrated elements, prevents non-physical deformations",
        "key_terms": ["hourglass", "zero-energy", "deformation"]
    },
    {
        "id": 6,
        "category": "manual",
        "question": "What does *CONTROL_TIMESTEP do?",
        "expected": "Controls the time step size for explicit analysis, includes mass scaling options",
        "key_terms": ["timestep", "time step", "explicit"]
    },
    {
        "id": 7,
        "category": "manual",
        "question": "What is *MAT_RIGID and what is its material number?",
        "expected": "MAT_020, defines rigid body material, parts do not deform",
        "key_terms": ["MAT_020", "rigid"]
    },
    {
        "id": 8,
        "category": "manual",
        "question": "What is *INITIAL_VELOCITY used for?",
        "expected": "Assigns initial translational and rotational velocities to nodes or parts",
        "key_terms": ["initial", "velocity", "nodes"]
    },
    {
        "id": 9,
        "category": "manual",
        "question": "What is the difference between ELFORM=2 and ELFORM=16 for shell elements?",
        "expected": "ELFORM=2 is Belytschko-Tsay (under-integrated, fast), ELFORM=16 is fully integrated (more accurate, slower)",
        "key_terms": ["ELFORM", "2", "16", "Belytschko", "integrated"]
    },
    {
        "id": 10,
        "category": "manual",
        "question": "What is *DATABASE_BINARY_D3PLOT?",
        "expected": "Controls output frequency of the d3plot binary database for post-processing",
        "key_terms": ["d3plot", "database", "output", "binary"]
    },

    # ================================================================
    # CATEGORY 2: PROJECT DATABASE QUERIES (12 questions)
    # Answer should come from simulation database
    # ================================================================
    {
        "id": 11,
        "category": "project",
        "question": "What material was used for the B-pillar in the Atlas-X SOF simulation?",
        "expected": "Tailor-Welded 22MnB5/DP600 with *MAT_024, ELFORM=16",
        "key_terms": ["22MnB5", "MAT_024", "Atlas-X"]
    },
    {
        "id": 12,
        "category": "project",
        "question": "Which engineer ran the Meridian-3 FWDB simulation?",
        "expected": "M. Weber",
        "key_terms": ["Weber", "Meridian-3", "FWDB"]
    },
    {
        "id": 13,
        "category": "project",
        "question": "What was the peak intrusion in the Titan-R rear impact simulation SIM-1018?",
        "expected": "94.8mm",
        "key_terms": ["94.8", "Titan-R", "REAR"]
    },
    {
        "id": 14,
        "category": "project",
        "question": "Which simulations failed or terminated with negative volume?",
        "expected": "SIM-1005 (Meridian-3 SOF) and SIM-1019 (Titan-R REAR)",
        "key_terms": ["SIM-1005", "SIM-1019", "Negative Volume", "Terminated"]
    },
    {
        "id": 15,
        "category": "project",
        "question": "What element formulation was used for the front crash rails in SIM-1000?",
        "expected": "Left rail: ELFORM=16 with CP1000 and MAT_124. Right rail: ELFORM=2 with DP980 and MAT_024",
        "key_terms": ["ELFORM", "CP1000", "DP980", "SIM-1000"]
    },
    {
        "id": 16,
        "category": "project",
        "question": "Which projects used aluminium for the front bumper beam?",
        "expected": "SIM-1000 Atlas-X (AL6082-T6 rear bumper), SIM-1010 Vanguard-E (AL6082-T6 front bumper)",
        "key_terms": ["AL6082", "bumper"]
    },
    {
        "id": 17,
        "category": "project",
        "question": "What strain rate model was used for the floor pan in SIM-1000?",
        "expected": "Cowper-Symonds, material BH210",
        "key_terms": ["Cowper-Symonds", "BH210", "floor"]
    },
    {
        "id": 18,
        "category": "project",
        "question": "How many simulations did S. Takahashi run?",
        "expected": "Multiple: SIM-1000, SIM-1008, SIM-1009, SIM-1011, SIM-1014, SIM-1017, SIM-1022, SIM-1028",
        "key_terms": ["Takahashi"]
    },
    {
        "id": 19,
        "category": "project",
        "question": "What material keyword was used for the engine block in SIM-1000?",
        "expected": "*MAT_020 (rigid), Cast Iron, ELFORM=1",
        "key_terms": ["MAT_020", "rigid", "Cast Iron", "engine"]
    },
    {
        "id": 20,
        "category": "project",
        "question": "Which vehicle program is a BEV (battery electric vehicle)?",
        "expected": "Vanguard-E (B-segment Hatchback BEV)",
        "key_terms": ["Vanguard-E", "BEV"]
    },
    {
        "id": 21,
        "category": "project",
        "question": "What was the peak force in the Nova-S side pole simulation SIM-1025?",
        "expected": "Check simulation results for SIM-1025 peak force value",
        "key_terms": ["Nova-S", "SPOL", "SIM-1025"]
    },
    {
        "id": 22,
        "category": "project",
        "question": "Which simulations used *MAT_124 for any component?",
        "expected": "SIM-1000 (Atlas-X, front crash rails left with CP1000), SIM-1020 (Titan-R, rocker panels with CP1000), and others with CP1000",
        "key_terms": ["MAT_124", "CP1000"]
    },

    # ================================================================
    # CATEGORY 3: CROSS-SOURCE QUESTIONS (8 questions)
    # Need both manual and project database to answer fully
    # ================================================================
    {
        "id": 23,
        "category": "cross",
        "question": "The Atlas-X project used MAT_024 for the B-pillar. What type of material model is MAT_024?",
        "expected": "MAT_024 is piecewise linear plasticity. Atlas-X used it with Tailor-Welded 22MnB5/DP600 for B-pillar",
        "key_terms": ["MAT_024", "piecewise", "Atlas-X", "B-pillar"]
    },
    {
        "id": 24,
        "category": "cross",
        "question": "Several projects used ELFORM=16. What are the advantages of this element formulation according to the manual?",
        "expected": "ELFORM=16 is fully integrated, avoids hourglass issues. Used in Atlas-X, Vanguard-E, Titan-R etc.",
        "key_terms": ["ELFORM=16", "fully integrated", "hourglass"]
    },
    {
        "id": 25,
        "category": "cross",
        "question": "What is the Cowper-Symonds strain rate model and which of our projects used it?",
        "expected": "Cowper-Symonds scales yield stress with strain rate. Used in Titan-R, Nova-S, Pinnacle-7, Vanguard-E",
        "key_terms": ["Cowper-Symonds", "strain rate", "yield"]
    },
    {
        "id": 26,
        "category": "cross",
        "question": "The Titan-R RCAR simulation used MAT_124 for the rocker panels. What is MAT_124?",
        "expected": "MAT_124 is modified piecewise linear plasticity with failure. Used with CP1000 in Titan-R",
        "key_terms": ["MAT_124", "Titan-R", "CP1000"]
    },
    {
        "id": 27,
        "category": "cross",
        "question": "What contact types were used in our simulations and what does the manual say about CONTACT_AUTOMATIC_SINGLE_SURFACE?",
        "expected": "Used automatic single surface, surface to surface, tied contacts. Manual describes ASS as general purpose self-contact",
        "key_terms": ["CONTACT_AUTOMATIC", "self-contact"]
    },
    {
        "id": 28,
        "category": "cross",
        "question": "SIM-1000 used ELFORM=2 for several components. What are the limitations of ELFORM=2 according to the manual?",
        "expected": "ELFORM=2 is under-integrated (one point), susceptible to hourglass modes, needs hourglass control",
        "key_terms": ["ELFORM=2", "hourglass", "under-integrated"]
    },
    {
        "id": 29,
        "category": "cross",
        "question": "What is *MAT_020 and which components in our projects use it?",
        "expected": "MAT_020 is rigid material. Used for engine blocks (Cast Iron Rigid) in multiple simulations",
        "key_terms": ["MAT_020", "rigid", "engine"]
    },
    {
        "id": 30,
        "category": "cross",
        "question": "The Vanguard-E project is a BEV. Does it have a battery housing component and what material was used?",
        "expected": "Check if Vanguard-E simulations include Battery Housing component with AL6061-T6 or AL5754",
        "key_terms": ["Vanguard-E", "BEV", "battery", "housing"]
    },
]

if __name__ == "__main__":
    print(f"Total questions: {len(test_questions)}")
    for cat in ["manual", "project", "cross"]:
        count = len([q for q in test_questions if q["category"] == cat])
        print(f"  {cat}: {count}")
    print("\nSample questions:")
    for q in test_questions[:3]:
        print(f"  Q{q['id']}: {q['question']}")
