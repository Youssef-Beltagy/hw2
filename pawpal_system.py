from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    category: str
    duration_minutes: int
    priority: int  # 1=high, 2=medium, 3=low
    pet: Pet | None = None
    start_minute: int = -1
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

# @dataclass
# class TaskTemplate:
#     task: Task
#     # repeat every cadence days
#     cadence: int
#     nextDate: 

@dataclass
class Pet:
    name: str
    species: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and set its back-reference."""
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> Task | None:
        """Remove and return a task by name, or None if not found."""
        for i, t in enumerate(self.tasks):
            if t.name == task_name:
                return self.tasks.pop(i)
        return None

@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Return a flat list of all tasks across all pets."""
        return [t for p in self.pets for t in p.tasks]
@dataclass
class Plan:
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




class Scheduler:
    def __init__(self):
        self.owners = []# Read from json file data store

    def add_owner(self, owner):
        """Add an owner to the scheduler's list."""
        self.owners.append(owner)

    def generate_plan(self, owner) -> Plan:
        """Generate a prioritized schedule for the owner and return a Plan with explanations."""
        
        scheduled_tasks: list[Task] = []
        scheduled_explanations = [f"Plan for {owner.name} ({owner.available_minutes} min available):\n"]
        skipped_explanations = [f"Skipped tasks for {owner.name}:\n"]

        tasks = sorted(filter(lambda t: not t.completed, owner.all_tasks()), key=lambda t: t.priority)
        task_index = 0
        elapsed_min = 0
        while elapsed_min <= owner.available_minutes and task_index < len(tasks):
            task = tasks[task_index]
            pet_name = task.pet.name if task.pet else "Unknown"
            remaining_minutes = owner.available_minutes - elapsed_min
            if task.duration_minutes <= remaining_minutes:
                task.start_minute = elapsed_min
                scheduled_tasks.append(task)
                scheduled_explanations.append(
                    f"  [{pet_name}] {task.name} (priority {task.priority}, "
                    f"{task.duration_minutes} min) — {elapsed_min} to {elapsed_min + task.duration_minutes} min"
                )
                elapsed_min += task.duration_minutes
            else:
                skipped_explanations.append(f"[{pet_name}] {task.name} skipped but would fit if shorter or higher priority ({task.duration_minutes} min task duration > {remaining_minutes} min left):")

            task_index += 1
        
        for task in tasks[task_index:]:
            pet_name = task.pet.name if task.pet else "Unknown"
            skipped_explanations.append(f"  [{pet_name}] {task.name} skipped because owner ran out of time but could fit if higher priority")
            
        return Plan(scheduled_tasks=scheduled_tasks, scheduled_explanations=scheduled_explanations, skipped_explanations=skipped_explanations)
