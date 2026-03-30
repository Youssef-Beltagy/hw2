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


@dataclass
class Pet:
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


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: dict[str, Pet] = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Add or update a pet by name, preserving existing tasks."""
        if pet.name in self.pets:
            existing = self.pets[pet.name]
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
        self.owners: dict[str, Owner] = {}

    def add_owner(self, owner: Owner) -> None:
        """Add or update an owner by name, preserving existing pets and tasks."""
        if owner.name in self.owners:
            existing = self.owners[owner.name]
            existing.available_minutes = owner.available_minutes

            # merge new pets into existing, keeping old ones
            # a bit unnecessary since "new" owner entries will not have pets.
            # but keeping it just in case I need it later.
            for name, pet in owner.pets.items():
                existing.add_pet(pet)
        else:
            self.owners[owner.name] = owner

    def generate_plan(self, owner: Owner) -> Plan:
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
                skipped_explanations.append(
                    f"  [{pet_name}] {task.name} skipped but would fit if shorter or higher priority "
                    f"({task.duration_minutes} min task duration > {remaining_minutes} min left):"
                )
            task_index += 1

        for task in tasks[task_index:]:
            pet_name = task.pet.name if task.pet else "Unknown"
            skipped_explanations.append(
                f"  [{pet_name}] {task.name} skipped because owner ran out of time but could fit if higher priority"
            )

        return Plan(
            scheduled_tasks=scheduled_tasks,
            scheduled_explanations=scheduled_explanations,
            skipped_explanations=skipped_explanations,
        )
