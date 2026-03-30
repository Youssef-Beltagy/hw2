import streamlit as st
from datetime import datetime, timedelta, time
from pawpal_system import Owner, Pet, Task, Scheduler, Availability, fmt_dt, fmt_td


def render_tasks(tasks: list[Task], key_prefix):
    priority_labels = {1: "🔴 Highest", 2: "🟠 High", 3: "🟡 Medium", 4: "🔵 Low", 5: "⚪ Irrelevant"}
    for t in tasks:
        pn = t.pet.name if t.pet else "?"
        due = fmt_dt(t.due_date) if t.due_date else "—"
        pri = priority_labels.get(t.priority, f"P{t.priority}")
        status = "✅" if t.completed else "🔲"
        tags = f"{'🔁 recurring' if t.reset_every else ''} {'⭐ required' if t.required else ''}".strip()
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(
                f"{status} **{t.name}** &nbsp;·&nbsp; 🐾 {pn} &nbsp;·&nbsp; {pri} &nbsp;·&nbsp; ⏱ {fmt_td(t.duration)}m"
                + (f" &nbsp;·&nbsp; 📅 {due}" if t.due_date else "")
                + (f" &nbsp;·&nbsp; {tags}" if tags else "")
            )
        with col2:
            if st.button("❌", key=f"{key_prefix}_del_task_{pn}_{t.name}"):
                t.pet.remove_task(t.name)
                st.session_state.plan = None
                st.rerun()


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
owner_name = st.text_input("Owner name")

if st.button("Register Owner"):
    if owner_name.strip():
        owner = Owner(name=owner_name.strip())
        scheduler.add_owner(owner)
        st.session_state.current_owner = owner
        st.success(f"Registered {owner_name}!")
    else:
        st.warning("Please enter a name.")

# --- Select / Delete Owner ---
if scheduler.owners:
    owner_names = list(scheduler.owners.keys())
    cur_sel = len(owner_names) - 1
    if st.session_state.current_owner:
        cur_sel = owner_names.index(st.session_state.current_owner.name)
    selected = st.selectbox("Select owner", owner_names, index=cur_sel)
    st.session_state.current_owner = scheduler.owners[selected]

    if st.button("Delete Owner"):
        scheduler.remove_owner(selected)
        st.session_state.current_owner = None
        st.session_state.plan = None
        st.rerun()

owner = st.session_state.current_owner

if not owner:
    st.info("Register an owner to get started.")
    st.stop()

# --- Availability ---
st.divider()
st.subheader(f"Availability for {owner.name}")
col1, col2 = st.columns(2)
with col1:
    avail_start = st.datetime_input("Start time", value=datetime.now() + timedelta(minutes=15))
with col2:
    avail_duration = st.number_input("Duration (min)", min_value=1, max_value=1440, value=20, key="avail_dur")

if st.button("Add Availability"):
    try:
        owner.add_availability(Availability(start_time=avail_start, duration=timedelta(minutes=avail_duration)))
        st.success(f"Added availability at {fmt_dt(avail_start)} for {avail_duration} mins")
    except ValueError as e:
        st.warning(str(e))

for i, a in enumerate(owner.availabilities):
    end_dt = a.start_time + a.duration
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"🕐 {fmt_dt(a.start_time)} – {fmt_dt(end_dt)} ({fmt_td(a.duration)})")
    with col2:
        if st.button("❌", key=f"del_avail_{i}"):
            owner.remove_availability(i)
            st.rerun()

# --- Pets ---
st.divider()
st.subheader(f"Pets for {owner.name}")
pet_name = st.text_input("Pet name")
species = st.selectbox("Species", ["Dog", "Cat", "Chicken", "Abomination", "Other"])

if st.button("Add/Update Pet"):
    if pet_name.strip():
        owner.add_pet(Pet(name=pet_name.strip(), species=species))
        st.success(f"Added {pet_name} the {species}!")
    else:
        st.warning("Please enter a pet name.")

for pname, pet in list(owner.pets.items()):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.write(f"🐾 **{pet.name}** ({pet.species}) — {len(pet.tasks)} task(s)")
    with col2:
        if st.button("❌", key=f"del_pet_{pname}"):
            owner.remove_pet(pname)
            st.rerun()

# --- Tasks ---
if owner.pets:
    st.divider()
    st.subheader("Add Tasks")
    pet_names = list(owner.pets.keys())
    selected_pet = st.selectbox("Assign to pet", pet_names)

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task name")
    with col2:
        duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20, key="task_dur")
    with col3:
        priority = st.selectbox("Priority", [1, 2, 3, 4, 5], format_func=lambda x: {1: "Highest", 2: "High", 3: "Medium", 4: "Low", 5: "Irrelevant"}[x])

    category = st.text_input("Category", value="exercise")
    description = st.text_input("Description", value="")
    due_date = st.date_input("Due date (optional)", value=None)
    task_required = st.checkbox("Required", value=False)
    reset_every = None
    reset_days = st.number_input("Recur every (days, 0 = not recurring)", min_value=0, value=0, max_value=400, key="reset_days")
    if reset_days > 0:
        reset_every = timedelta(days=reset_days)

    if st.button("Add/Update Task"):
        dd = datetime.combine(due_date, time(0, 0)) if due_date else None
        if reset_days > 0 and task_required:
            st.warning("Recurring tasks can't be required")
        if dd and dd < datetime.combine(datetime.now(), time(0, 0)):
            st.warning("Due Date can't be in the past")
        elif task_title.strip():
            pet = owner.pets[selected_pet]
            pet.add_task(Task(
                name=task_title.strip(),
                category=category,
                description=description,
                priority=priority,
                duration=timedelta(minutes=int(duration)),
                due_date=dd,
                required=task_required,
                reset_every=reset_every,
            ))
            st.success(f"Added '{task_title}' to {selected_pet}!")
        else:
            st.warning("Please enter a task name.")

    all_tasks = owner.all_tasks()
    if all_tasks:
        st.markdown("### Current Tasks")
        render_tasks(all_tasks, "all_tasks")


# --- Generate Schedule ---
st.divider()
st.subheader("Generate Schedule")

if st.button("Generate schedule"):
    if not owner.all_tasks():
        st.warning("Add at least one pet with tasks first.")
    elif not owner.availabilities:
        st.warning("Add at least one availability block first.")
    else:
        st.session_state.plan = scheduler.generate_plan(owner)

if st.session_state.plan:
    render_tasks(st.session_state.plan.scheduled_tasks, "plan")
    st.code(str(st.session_state.plan))
