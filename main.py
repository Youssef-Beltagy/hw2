from pawpal_system import Owner, Pet, Task, Scheduler

scheduler = Scheduler()

owner = Owner(name="Alex", available_minutes=60)

dog = Pet(name="Buddy", species="Dog")
cat = Pet(name="Whiskers", species="Cat")

dog.add_task(Task(name="Exist", category="exercise", duration_minutes=20, priority=0, completed=True))
dog.add_task(Task(name="Morning Walk", category="exercise", duration_minutes=30, priority=1))
dog.add_task(Task(name="Feed Dinner", category="feeding", duration_minutes=10, priority=2))
cat.add_task(Task(name="Brush Fur", category="grooming", duration_minutes=15, priority=2))
cat.add_task(Task(name="Play Session", category="enrichment", duration_minutes=20, priority=3))

owner.add_pet(dog)
owner.add_pet(cat)

scheduler.add_owner(owner)

print(scheduler.generate_plan(owner))
