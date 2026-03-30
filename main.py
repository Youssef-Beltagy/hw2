from pawpal_system import Owner, Pet, Task, Scheduler, Availability
from datetime import datetime, timedelta

scheduler = Scheduler()
today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
tomorrow = today + timedelta(days=1)
next_week = today + timedelta(days=7)

# --- Case 1: Multiple tasks with the same due date, different priorities ---
print("=== Case 1: Same due date, different priorities ===")
owner1 = Owner(name="Alex")
dog = Pet(name="Buddy", species="Dog")
dog.add_task(Task(name="Feed Dinner", category="feeding", priority=3, duration=timedelta(minutes=10), due_date=tomorrow))
dog.add_task(Task(name="Give Meds", category="meds", priority=1, duration=timedelta(minutes=5), due_date=tomorrow))
dog.add_task(Task(name="Morning Walk", category="exercise", priority=2, duration=timedelta(minutes=30), due_date=tomorrow))
owner1.add_pet(dog)
owner1.add_availability(Availability(start_time=datetime.now() + timedelta(minutes=1), duration=timedelta(minutes=60)))
scheduler.add_owner(owner1)
print(scheduler.generate_plan(owner1))

# --- Case 2: Mixed due dates — urgent tasks scheduled before later ones ---
print("=== Case 2: Mixed due dates ===")
owner2 = Owner(name="Sam")
cat = Pet(name="Whiskers", species="Cat")
cat.add_task(Task(name="Brush Fur", category="grooming", priority=2, duration=timedelta(minutes=15), due_date=next_week))
cat.add_task(Task(name="Vet Checkup", category="meds", priority=1, duration=timedelta(minutes=30), due_date=tomorrow))
cat.add_task(Task(name="Play Session", category="enrichment", priority=3, duration=timedelta(minutes=20), due_date=tomorrow))
owner2.add_pet(cat)
owner2.add_availability(Availability(start_time=datetime.now() + timedelta(minutes=1), duration=timedelta(minutes=90)))
scheduler.add_owner(owner2)
print(scheduler.generate_plan(owner2))

# --- Case 3: Not enough time — some tasks skipped ---
print("=== Case 3: Not enough time ===")
owner3 = Owner(name="Jordan")
bird = Pet(name="Tweety", species="Bird")
bird.add_task(Task(name="Clean Cage", category="grooming", priority=1, duration=timedelta(minutes=15), due_date=tomorrow))
bird.add_task(Task(name="Sing Along", category="enrichment", priority=2, duration=timedelta(minutes=10), due_date=tomorrow))
bird.add_task(Task(name="Feed Seeds", category="feeding", priority=1, duration=timedelta(minutes=5), due_date=tomorrow))
owner3.add_pet(bird)
owner3.add_availability(Availability(start_time=datetime.now() + timedelta(minutes=1), duration=timedelta(minutes=20)))
scheduler.add_owner(owner3)
print(scheduler.generate_plan(owner3))

# --- Case 4: Completed and recurring tasks ---
print("=== Case 4: Completed + recurring ===")
owner4 = Owner(name="Pat")
hamster = Pet(name="Nibbles", species="Hamster")
hamster.add_task(Task(name="Already Done", category="exercise", priority=1, duration=timedelta(minutes=10), completed=True)) # Skip this
hamster.add_task(Task(name="Already Done But Recurring", category="exercise", priority=1, duration=timedelta(minutes=10), completed=True, required=False, reset_every=timedelta(days=1), next_reset_time=datetime.now() - timedelta(minutes=1))) # Print this
hamster.add_task(Task(name="Wheel Time", category="enrichment", priority=2, duration=timedelta(minutes=20), required=False, reset_every=timedelta(days=1)))
hamster.add_task(Task(name="Fresh Water", category="feeding", priority=1, duration=timedelta(minutes=5), due_date=tomorrow))
owner4.add_pet(hamster)
owner4.add_availability(Availability(start_time=datetime.now() + timedelta(minutes=1), duration=timedelta(minutes=60)))
scheduler.add_owner(owner4)
print(scheduler.generate_plan(owner4))

# --- Case 5: Multiple availability blocks ---
print("=== Case 5: Multiple availability blocks ===")
owner5 = Owner(name="Riley")
dog2 = Pet(name="Max", species="Dog")
dog2.add_task(Task(name="Walk", category="exercise", priority=1, duration=timedelta(minutes=20), due_date=tomorrow))
dog2.add_task(Task(name="Train", category="enrichment", priority=2, duration=timedelta(minutes=15), due_date=tomorrow))
dog2.add_task(Task(name="Groom", category="grooming", priority=3, duration=timedelta(minutes=20), due_date=tomorrow))
owner5.add_pet(dog2)
base = datetime.now() + timedelta(minutes=1)
owner5.add_availability(Availability(start_time=base, duration=timedelta(minutes=25)))
owner5.add_availability(Availability(start_time=base + timedelta(hours=2), duration=timedelta(minutes=20)))
scheduler.add_owner(owner5)
print(scheduler.generate_plan(owner5))
