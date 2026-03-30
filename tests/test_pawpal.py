import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from pawpal_system import Task, Pet, Owner, Availability, Plan, Scheduler, fmt_dt, fmt_td


# --- Helpers ---
TODAY = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
TOMORROW = TODAY + timedelta(days=1)
NEXT_WEEK = TODAY + timedelta(days=7)
FUTURE = datetime.now() + timedelta(hours=1)


def _make_task(name="Walk", priority=1, duration_min=10, **kwargs):
    return Task(name=name, category="general", priority=priority, duration=timedelta(minutes=duration_min), **kwargs)


# ===== Task Tests =====

class TestTask:
    def test_mark_complete(self):
        task = _make_task()
        assert task.completed is False
        task.mark_complete()
        assert task.completed is True

    def test_mark_complete_sets_next_reset_time_for_recurring(self):
        next_time_plus_1m = datetime.now() + timedelta(days=1, minutes=1)
        task = _make_task(required=False, reset_every=timedelta(days=1), next_reset_time=None)
        task.mark_complete()
        assert task.completed is True
        assert task.next_reset_time <= next_time_plus_1m and task.next_reset_time >= next_time_plus_1m - timedelta(minutes=2)

    def test_post_init_rejects_required_and_reset_every(self):
        with pytest.raises(ValueError, match="mutually exclusive"):
            _make_task(required=True, reset_every=timedelta(days=1))

    def test_post_init_rejects_non_day_due_date(self):
        with pytest.raises(ValueError, match="days granularity"):
            _make_task(due_date=datetime(2026, 3, 30, 10, 30))

    def test_post_init_accepts_day_due_date(self):
        task = _make_task(due_date=TOMORROW)
        assert task.due_date == TOMORROW

    def test_post_init_accepts_none_due_date(self):
        task = _make_task(due_date=None)
        assert task.due_date is None

    def test_reset_does_nothing_without_next_reset_time(self):
        task = _make_task()
        task.completed = True
        task.reset()
        assert task.completed is True

    def test_reset_does_nothing_if_not_time_yet(self):
        task = _make_task(required=False, reset_every=timedelta(days=1))
        task.next_reset_time = datetime.now() + timedelta(hours=1)
        task.completed = True
        task.reset()
        assert task.completed is True

    def test_reset_clears_when_past_next_reset_time(self):
        task = _make_task(required=False, reset_every=timedelta(days=1))
        task.next_reset_time = datetime.now() - timedelta(hours=1)
        task.completed = True
        task.start_time = datetime.now()
        task.reset()
        assert task.completed is False
        assert task.start_time is None
        assert task.next_reset_time is None


# ===== Pet Tests =====

class TestPet:
    def test_add_task(self):
        pet = Pet(name="Buddy", species="Dog")
        task = _make_task(name="walk")
        pet.add_task(task)
        assert len(pet.tasks) == 1
        assert task.pet is pet
        assert pet.tasks["walk"] is task


    def test_add_task_overwrites_same_name(self):
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="Walk", priority=1))
        pet.add_task(_make_task(name="Walk", priority=2))
        assert len(pet.tasks) == 1
        assert pet.tasks["Walk"].priority == 2

    def test_remove_task(self):
        pet = Pet(name="Buddy", species="Dog")
        task = _make_task()
        pet.add_task(task)
        removed = pet.remove_task("Walk")
        assert removed is task
        assert removed.pet is None
        assert len(pet.tasks) == 0

    def test_remove_task_not_found(self):
        pet = Pet(name="Buddy", species="Dog")
        assert pet.remove_task("Nonexistent") is None

    def test_list_tasks(self):
        pet = Pet(name="Buddy", species="Dog")
        t1 = _make_task(name="Walk")
        t2 = _make_task(name="Feed")
        pet.add_task(t1)
        pet.add_task(t2)
        assert len(pet.list_tasks()) == 2


# ===== Owner Tests =====

class TestOwner:
    def test_add_pet(self):
        owner = Owner(name="Alex")
        owner.add_pet(Pet(name="Buddy", species="Dog"))
        assert len(owner.pets) == 1

    def test_add_pet_merges_existing(self):
        owner = Owner(name="Alex")
        pet1 = Pet(name="Buddy", species="Dog")
        t = _make_task(name="Walk")
        pet1.add_task(t)
        owner.add_pet(pet1)
        pet2 = Pet(name="Buddy", species="Cat")
        owner.add_pet(pet2)
        assert owner.pets["Buddy"].species == "Cat"
        assert "Walk" in owner.pets["Buddy"].tasks

    def test_remove_pet(self):
        owner = Owner(name="Alex")
        owner.add_pet(Pet(name="Buddy", species="Dog"))
        removed = owner.remove_pet("Buddy")
        assert removed is not None
        assert len(owner.pets) == 0

    def test_remove_pet_not_found(self):
        owner = Owner(name="Alex")
        assert owner.remove_pet("Ghost") is None

    def test_list_pets(self):
        owner = Owner(name="Alex")
        owner.add_pet(Pet(name="A", species="Dog"))
        owner.add_pet(Pet(name="B", species="Cat"))
        assert len(owner.list_pets()) == 2

    def test_all_tasks(self):
        owner = Owner(name="Alex")
        p1 = Pet(name="A", species="Dog")
        p2 = Pet(name="B", species="Cat")
        p1.add_task(_make_task(name="T1"))
        p2.add_task(_make_task(name="T2"))
        owner.add_pet(p1)
        owner.add_pet(p2)
        assert len(owner.all_tasks()) == 2

    def test_add_availability(self):
        owner = Owner(name="Alex")
        owner.add_availability(Availability(start_time=FUTURE, duration=timedelta(minutes=30)))
        assert len(owner.availabilities) == 1

    def test_add_availability_rejects_past(self):
        owner = Owner(name="Alex")
        with pytest.raises(ValueError, match="past"):
            owner.add_availability(Availability(start_time=datetime(2020, 1, 1), duration=timedelta(minutes=30)))

    def test_add_availability_merges_overlapping(self):
        owner = Owner(name="Alex")
        base = FUTURE
        owner.add_availability(Availability(start_time=base, duration=timedelta(minutes=30)))
        owner.add_availability(Availability(start_time=base + timedelta(minutes=15), duration=timedelta(minutes=30)))
        assert len(owner.availabilities) == 1
        assert owner.availabilities[0].duration == timedelta(minutes=45)

    def test_add_availability_inserts_before_non_overlapping(self):
        owner = Owner(name="Alex")
        base = FUTURE
        owner.add_availability(Availability(start_time=base + timedelta(hours=2), duration=timedelta(minutes=30)))
        owner.add_availability(Availability(start_time=base, duration=timedelta(minutes=30)))
        assert len(owner.availabilities) == 2
        assert owner.availabilities[0].start_time == base

    def test_remove_availability(self):
        owner = Owner(name="Alex")
        owner.add_availability(Availability(start_time=FUTURE, duration=timedelta(minutes=30)))
        removed = owner.remove_availability(0)
        assert removed is not None
        assert len(owner.availabilities) == 0


# ===== Plan Tests =====

class TestPlan:
    def test_str_with_skipped(self):
        plan = Plan(
            scheduled_tasks=[],
            scheduled_explanations=["Scheduled:"],
            skipped_explanations=["Skipped:", "  task1 skipped"],
        )
        output = str(plan)
        assert "Scheduled:" in output
        assert "task1 skipped" in output

    def test_str_without_skipped(self):
        plan = Plan(
            scheduled_tasks=[],
            scheduled_explanations=["Scheduled:"],
            skipped_explanations=["Skipped:"],
        )
        output = str(plan)
        assert "Scheduled:" in output
        assert output.count("Skipped") == 0


# ===== Formatter Tests =====

class TestFormatters:
    def test_fmt_dt_none(self):
        assert fmt_dt(None) == "None"

    def test_fmt_dt_value(self):
        dt = datetime(2026, 3, 30, 14, 5)
        assert fmt_dt(dt) == "2026-03-30 14:05"

    def test_fmt_td_minutes_only(self):
        assert fmt_td(timedelta(minutes=45)) == "45m"

    def test_fmt_td_hours_and_minutes(self):
        assert fmt_td(timedelta(hours=1, minutes=30)) == "1h30m"

    def test_fmt_td_zero(self):
        assert fmt_td(timedelta()) == "0m"


# ===== Scheduler Tests =====

class TestScheduler:
    def test_add_owner(self):
        s = Scheduler()
        s.add_owner(Owner(name="Alex"))
        assert "Alex" in s.owners

    def test_add_owner_ignores_duplicate(self):
        s = Scheduler()
        o1 = Owner(name="Alex")
        p = Pet(name="Buddy", species="Dog")
        o1.add_pet(p)
        s.add_owner(o1)
        o2 = Owner(name="Alex")
        s.add_owner(o2)
        assert len(s.owners["Alex"].pets) == 1

    def test_remove_owner(self):
        s = Scheduler()
        s.add_owner(Owner(name="Alex"))
        removed = s.remove_owner("Alex")
        assert removed is not None
        assert len(s.owners) == 0

    def test_remove_owner_not_found(self):
        s = Scheduler()
        assert s.remove_owner("Ghost") is None

    def test_get_all_tasks_sorted_by_priority(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="Low", priority=3))
        pet.add_task(_make_task(name="High", priority=1))
        owner.add_pet(pet)
        tasks = s.get_all_tasks(owner)
        assert tasks[0].name == "High"
        assert tasks[1].name == "Low"

    def test_get_sorted_tasks_required_soon_first(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="Due Tomorrow", priority=2, due_date=TOMORROW))
        pet.add_task(_make_task(name="Due Next Week", priority=1, due_date=NEXT_WEEK))
        owner.add_pet(pet)
        tasks = s.get_sorted_tasks(owner)
        assert tasks[0].name == "Due Tomorrow"

    def test_get_sorted_tasks_same_due_date_sorted_by_priority(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="LowPri", priority=3, due_date=TOMORROW))
        pet.add_task(_make_task(name="HighPri", priority=1, due_date=TOMORROW))
        owner.add_pet(pet)
        tasks = s.get_sorted_tasks(owner)
        assert tasks[0].name == "HighPri"
        assert tasks[1].name == "LowPri"

    def test_get_sorted_tasks_filters_completed(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="Done", priority=1))
        pet.tasks["Done"].completed = True
        pet.add_task(_make_task(name="Todo", priority=2))
        owner.add_pet(pet)
        tasks = s.get_sorted_tasks(owner)
        assert len(tasks) == 1
        assert tasks[0].name == "Todo"

    def test_generate_plan_schedules_within_availability(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="Walk", priority=1, duration_min=20, due_date=TOMORROW))
        pet.add_task(_make_task(name="Feed", priority=2, duration_min=10, due_date=TOMORROW))
        owner.add_pet(pet)
        owner.add_availability(Availability(start_time=FUTURE, duration=timedelta(minutes=30)))
        plan = s.generate_plan(owner)
        assert len(plan.scheduled_tasks) == 2

    def test_generate_plan_skips_when_no_time(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="Long", priority=1, duration_min=60, due_date=TOMORROW))
        pet.add_task(_make_task(name="Short", priority=2, duration_min=5, due_date=TOMORROW))
        owner.add_pet(pet)
        owner.add_availability(Availability(start_time=FUTURE, duration=timedelta(minutes=10)))
        plan = s.generate_plan(owner)
        assert len(plan.scheduled_tasks) == 1
        assert plan.scheduled_tasks[0].name == "Short"

    def test_generate_plan_multiple_availability_blocks(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="A", priority=1, duration_min=20, due_date=TOMORROW))
        pet.add_task(_make_task(name="B", priority=2, duration_min=20, due_date=TOMORROW))
        owner.add_pet(pet)
        base = FUTURE
        owner.add_availability(Availability(start_time=base, duration=timedelta(minutes=25)))
        owner.add_availability(Availability(start_time=base + timedelta(hours=2), duration=timedelta(minutes=25)))
        plan = s.generate_plan(owner)
        assert len(plan.scheduled_tasks) == 2

    def test_generate_plan_empty_tasks(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        owner.add_availability(Availability(start_time=FUTURE, duration=timedelta(minutes=30)))
        plan = s.generate_plan(owner)
        assert len(plan.scheduled_tasks) == 0

    def test_generate_plan_no_availability(self):
        s = Scheduler()
        owner = Owner(name="Alex")
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(_make_task(name="Walk", priority=1, duration_min=10))
        owner.add_pet(pet)
        plan = s.generate_plan(owner)
        assert len(plan.scheduled_tasks) == 0
