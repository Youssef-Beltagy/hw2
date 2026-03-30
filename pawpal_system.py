from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Task:
    name: str
    category: str
    duration_minutes: int
    priority: int  # 1=high, 2=medium, 3=low
    pet: Pet | None = None
    start_minute: int

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
        task.pet = self
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> Task | None:
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
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        return [t for p in self.pets for t in p.tasks]



class Scheduler:
    def __init__(self):
        self.owners = []# Read from json file data store

    def add_owner(self, owner):
        self.owners.append(owner)

    def generate_plan(self, owner) -> str:
        """Schedule tasks by priority, return explanation distinguishing
        skipped tasks that could have fit if shorter vs. those that never had a chance."""
        
        scheduled: list[Task] = []
        scheduled_lines = [f"Plan for {owner.name} ({owner.available_minutes} min available):\n"]
        skipped_lines = [f"Skipped tasks for {owner.name}:\n"]

        tasks = sorted(owner.all_tasks(), key=lambda t: t.priority)
        task_index = 0
        elapsed_min = 0
        while elapsed_min <= owner.available_minutes:
            for i, task in enumerate(tasks):
                task_index = i
                pet_name = task.pet.name if task.pet else "Unknown"
                remaining_minutes = owner.available_minutes - elapsed_min
                if task.duration_minutes <= remaining_minutes:
                    task.start_minute = elapsed_min
                    scheduled.append(task)
                    scheduled_lines.append(
                        f"  [{pet_name}] {task.name} (priority {task.priority}, "
                        f"{task.duration_minutes} min) — starts at minute {elapsed_min}"
                    )
                    task.pet.remove(task.name)
                    elapsed_min += task.duration_minutes
                else:
                    skipped_lines.append(f"[{pet_name}] {task.name} skipped but would fit if shorter or higher priority ({remaining_minutes} min left):")
        
        for i, task in enumerate(tasks, task_index + 1):
            pet_name = task.pet.name if task.pet else "Unknown"
            skipped_lines.append(f"[{pet_name}] {task.name} skipped because owner ran out of time")
            
        return "\n".join(scheduled_lines)
