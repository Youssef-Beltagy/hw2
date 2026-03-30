import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Plan

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# --- Session State Initialization ---
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler()
if "current_owner" not in st.session_state:
    st.session_state.current_owner = None
if "plan" not in st.session_state:
    st.session_state.plan = None

scheduler = st.session_state.scheduler

st.title("🐾 PawPal+")

# --- Register Owner ---
st.subheader("Register Owner")
col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name")
with col2:
    available_minutes = st.number_input("Available minutes today", min_value=1, max_value=1440, value=60)

if st.button("Register Owner"):
    if owner_name.strip():
        owner = Owner(name=owner_name.strip(), available_minutes=available_minutes)
        scheduler.add_owner(owner)
        st.session_state.current_owner = owner
        st.success(f"Registered {owner_name}!")
    else:
        st.warning("Please enter a name.")

# --- Select Owner ---
if scheduler.owners:
    owner_names = list(scheduler.owners.keys())
    cur_sel = len(owner_names) - 1
    if st.session_state.current_owner:
        cur_sel = owner_names.index(st.session_state.current_owner.name)
    selected = st.selectbox("Select owner", owner_names, index=cur_sel)
    st.session_state.current_owner = scheduler.owners[selected]

owner = st.session_state.current_owner

if not owner:
    st.info("Register an owner to get started.")
    st.stop()

# --- Add Pet ---
st.divider()
st.subheader(f"Pets for {owner.name}")
pet_name = st.text_input("Pet name")
species = st.selectbox("Species", ["Dog", "Cat", "Abomination", "Other"])

if st.button("Add Pet"):
    if pet_name.strip():
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
        st.success(f"Added {pet_name} the {species}!")
    else:
        st.warning("Please enter a pet name.")

for pet in owner.pets.values():
    st.write(f"🐾 **{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s)")

# --- Add Tasks ---
if owner.pets:
    st.divider()
    st.subheader("Add Tasks")
    pet_names = list(owner.pets.keys())
    selected_pet = st.selectbox("Assign to pet", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task name")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", [1, 2, 3, 4, 5], format_func=lambda x: {1: "Highest", 2: "High", 3: "Medium", 4: "Low", 5: "Irrelevant"}[x])

    category = st.text_input("Category", value="exercise")

    if st.button("Add Task"):
        if task_title.strip():
            pet = owner.pets[selected_pet]
            pet.add_task(Task(name=task_title.strip(), category=category, duration_minutes=int(duration), priority=priority))
            st.success(f"Added '{task_title}' to {selected_pet}!")
        else:
            st.warning("Please enter a task name.")

    all_tasks = owner.all_tasks()
    if all_tasks:
        st.markdown("### Current Tasks")
        for t in all_tasks:
            pn = t.pet.name if t.pet else "?"
            st.write(f"[{pn}] {t.name} — {t.duration_minutes} min, priority {t.priority}")

# --- Generate Schedule ---
st.divider()
st.subheader("Generate Schedule")

if st.button("Generate schedule"):
    if owner.all_tasks():
        st.session_state.plan = scheduler.generate_plan(owner)
    else:
        st.warning("Add at least one pet with tasks first.")

if st.session_state.plan:
    st.code(str(st.session_state.plan))
