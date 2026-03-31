from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Task:
    """A pet care task with priority, duration, and optional recurrence."""
    name: str
    category: str
    priority: int  # lower is higher
    duration: timedelta
    description: str = ""
    due_date: datetime | None = None

    completed: bool = False
    required: bool = True # resetable tasks can't be required. So required and reset_every are mutually exclusive
    reset_every: timedelta | None = None
    next_reset_time: datetime | None = None

    pet: Pet | None = None

    # Set by the scheduler
    start_time: datetime | None = None


    def __post_init__(self) -> None:
        """Validate that reset_every and required are mutually exclusive, and due_date is day-granularity."""
        if self.reset_every and self.required:
            raise ValueError(f"Task '{self.name}': reset_every and required are mutually exclusive.")
        
        if self.due_date is None:
            return
        
        if self.due_date.hour != 0 or self.due_date.minute != 0 or self.due_date.second != 0 or self.due_date.microsecond != 0:
            raise ValueError(f"Task '{self.name}': due dates should be at the days granularity.")

        
    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True
        if self.reset_every:
            self.next_reset_time = datetime.now() + self.reset_every

    def reset(self) -> None:
        """Reset task completion and advance next_reset_time if recurring and enough time passed. Else, do nothing"""
        if not self.next_reset_time:
            return
        
        if datetime.now() < self.next_reset_time:
            return

        self.completed = False
        self.start_time = None
        self.next_reset_time = None


@dataclass
class Pet:
    """A pet with identifying info and a collection of care tasks."""
    name: str
    species: str
    tasks: dict[str, Task] = field(default_factory=dict)

    def add_task(self, task: Task) -> None:
        """Add or update a task by name, preserving the pet back-reference."""
        task.pet = self
        self.tasks[task.name] = task

    def remove_task(self, task_name: str) -> Task | None:
        """Remove and return a task by name, or None if not found."""
        task = self.tasks.pop(task_name, None)
        if task:
            task.pet = None
        return task

    def list_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        return list(self.tasks.values())


@dataclass
class Availability:
    """A time block when the owner is available for pet care."""
    start_time: datetime
    duration: timedelta


@dataclass
class Owner:
    """A pet owner with available time, pets, and availability blocks."""
    name: str
    pets: dict[str, Pet] = field(default_factory=dict)
    availabilities: list[Availability] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add or update a pet by name, preserving existing tasks."""
        if pet.name in self.pets:
            existing = self.pets[pet.name]

            # Update Species and tasks
            existing.species = pet.species
            # merge new tasks into existing, keeping old ones
            # a bit unnecessary since "new" pet entries will not have tasks.
            # but keeping it just in case I need it later.
            for name, task in pet.tasks.items():
                existing.tasks.setdefault(name, task)
        else:
            self.pets[pet.name] = pet

    def all_tasks(self) -> list[Task]:
        """Return a flat list of all tasks across all pets."""
        return [t for p in self.pets.values() for t in p.tasks.values()]

    def list_pets(self) -> list[Pet]:
        """Return all pets for this owner."""
        return list(self.pets.values())

    def remove_pet(self, pet_name: str) -> Pet | None:
        """Remove and return a pet by name, or None if not found."""
        return self.pets.pop(pet_name, None)

    def add_availability(self, availability: Availability) -> None:
        """Add an availability block, raising ValueError if it overlaps an existing one."""

        if availability.start_time < datetime.now() - timedelta(minutes=1):
            raise ValueError(f"Availability start time is in the past")
        
        new_end = availability.start_time + availability.duration
        for i, existing in enumerate(self.availabilities):
            ex_end = existing.start_time + existing.duration

            if availability.start_time > ex_end:
                continue

            if new_end < existing.start_time:
                self.availabilities.insert(i, availability)
                return
            
            # Overlapping intervals
            # Merge the times
            start_time = min(existing.start_time, availability.start_time)
            end_time = max(ex_end, new_end)

            self.availabilities[i].start_time = start_time
            self.availabilities[i].duration = end_time - start_time
            # Check if the merged block now overlaps with the next block
            while i + 1 < len(self.availabilities):
                next_avail = self.availabilities[i + 1]
                merged_end = self.availabilities[i].start_time + self.availabilities[i].duration
                if merged_end >= next_avail.start_time:
                    next_end = next_avail.start_time + next_avail.duration
                    self.availabilities[i].duration = max(merged_end, next_end) - self.availabilities[i].start_time
                    self.availabilities.pop(i + 1)
                else:
                    break
            return
            
        self.availabilities.append(availability)

    def trim_availabilities(self):
        """Remove or adjust availability blocks that are in the past."""
        while len(self.availabilities) > 0 and self.availabilities[0].start_time < datetime.now():
            now_1 = datetime.now() + timedelta(minutes=1)
            cur_avail = self.availabilities[0]
            end_time = cur_avail.start_time + cur_avail.duration
            if end_time < now_1 or (end_time - now_1) < timedelta(minutes=1):
                self.remove_availability(0)
            else:
                cur_avail.duration = end_time - now_1
                cur_avail.start_time = now_1
                break


    def remove_availability(self, index: int) -> Availability:
        """Remove and return an availability block by index."""
        return self.availabilities.pop(index)


@dataclass
class Plan:
    """The result of scheduling: scheduled tasks with explanations and skipped task reasons."""
    scheduled_tasks: list[Task]
    scheduled_explanations: list[str]
    skipped_explanations: list[str]

    def __str__(self) -> str:
        """Return a formatted string of the scheduled and skipped tasks."""
        lines = self.scheduled_explanations[:]

        if len(self.skipped_explanations) > 1:
            lines.append("")
            lines.extend(self.skipped_explanations)

        lines.append("")
        return "\n".join(lines)


def fmt_dt(dt: datetime | None) -> str:
    """Format a datetime to minute precision, or 'None'."""
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "None"

def fmt_td(td: timedelta) -> str:
    """Format a timedelta to hours and minutes."""
    total_min = int(td.total_seconds() // 60)
    h, m = divmod(total_min, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m"


class Scheduler:
    """Manages owners and generates prioritized daily care plans across all pets."""

    def __init__(self):
        self.owners: dict[str, Owner] = {}

    def add_owner(self, owner: Owner) -> None:
        """Add or update an owner by name, preserving existing pets and tasks."""
        if owner.name in self.owners:
            # Owner already exists, do nothing
            return
        else:
            self.owners[owner.name] = owner

    def remove_owner(self, owner_name: str) -> Owner | None:
        """Remove and return an owner by name, or None if not found."""
        return self.owners.pop(owner_name, None)

    def get_all_tasks(self, owner: Owner) -> list[Task]:
        """Retrieve all tasks across all pets for a given owner, sorted by priority."""
        return sorted(owner.all_tasks(), key=lambda t: t.priority)
    
    def get_sorted_tasks(self, owner: Owner) -> list[Task]:
        """Return tasks sorted by urgency: required tasks due soon first (by due date, then priority), then remaining tasks by priority. Resets recurring tasks before sorting."""


        # Computationally inefficient, but who cares?
        tasks: list[Task] = owner.all_tasks()
        
        # Reset recurring tasks
        for t in tasks:
            t.reset()

        tasks = [t for t in tasks if not t.completed]

        tomorrow = datetime.now() + timedelta(days=1)

        # For tasks that are due today or tomorrow, prioritize the due date then the priority
        tasks_required_soon = sorted(filter(lambda t: t.required and t.due_date and t.due_date <= tomorrow, tasks), key=lambda t: (t.due_date, t.priority))

        # For other tasks, order by priority
        other_tasks = filter(lambda t: t not in tasks_required_soon, tasks)
        other_tasks = sorted(other_tasks, key=lambda t: (t.priority))

        # Merge the two lists
        return tasks_required_soon + other_tasks



    def generate_plan(self, owner: Owner) -> Plan:
        """Generate a prioritized schedule for the owner and return a Plan with explanations."""
        scheduled_tasks: list[Task] = []
        scheduled_explanations = [f"Plan for {owner.name}:\n"]
        skipped_explanations: dict[str, str] = dict([["header", f"Skipped tasks for {owner.name}:\n"]])

        all_tasks = self.get_sorted_tasks(owner)

        # Clear start_time from previous plans
        for task in all_tasks:
            task.start_time = None

        # Get rid of old time
        owner.trim_availabilities()

        for availability in owner.availabilities:

            cur_tasks = [t for t in all_tasks if t not in scheduled_tasks]

            task_index = 0
            elapsed = timedelta()
            available_time = availability.duration
            while elapsed + timedelta(seconds=30) <= available_time and task_index < len(cur_tasks):
                task = cur_tasks[task_index]
                pet_name = task.pet.name if task.pet else "Unknown"
                remaining = available_time - elapsed
                if task.duration <= remaining:
                    task.start_time = availability.start_time + elapsed
                    scheduled_tasks.append(task)
                    scheduled_explanations.append(
                        f"  [{pet_name}] {task.name} scheduled at {fmt_dt(task.start_time)} --> {fmt_dt(task.start_time + task.duration)} (priority: {task.priority}, due_date: {fmt_dt(task.due_date)}, duration: {fmt_td(task.duration)})"
                    )
                    elapsed += task.duration
                    
                    if f"{pet_name}-{task.name}" in skipped_explanations:
                        del skipped_explanations[f"{pet_name}-{task.name}"]
                    
                else:
                    skipped_explanations[f"{pet_name}-{task.name}"] = f"  [{pet_name}] {task.name} skipped but would fit if shorter or higher priority ({fmt_td(task.duration)} task duration > {fmt_td(remaining)} left):"
                task_index += 1

        for task in all_tasks:
            if task in scheduled_tasks:
                continue
            
            pet_name = task.pet.name if task.pet else "Unknown"

            if f"{pet_name}-{task.name}" in skipped_explanations:
                continue
            skipped_explanations[f"{pet_name}-{task.name}"] = f"  [{pet_name}] {task.name} skipped because owner ran out of time"

        return Plan(
            scheduled_tasks=sorted(scheduled_tasks, key=lambda t: t.start_time), # The schedule should be returned sorted
            scheduled_explanations=scheduled_explanations,
            skipped_explanations=list(skipped_explanations.values()),
        )
