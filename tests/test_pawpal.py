from pawpal_system import Task, Pet


def test_mark_complete():
    task = Task(name="Walk", category="exercise", duration_minutes=30, priority=1)
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_count():
    pet = Pet(name="Buddy", species="Dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task(name="Walk", category="exercise", duration_minutes=30, priority=1))
    assert len(pet.tasks) == 1
    pet.add_task(Task(name="Feed", category="feeding", duration_minutes=10, priority=2))
    assert len(pet.tasks) == 2
