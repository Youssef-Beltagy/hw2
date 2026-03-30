from dataclasses import dataclass, field


@dataclass
class Pet:
    name: str
    species: str


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: list[Pet] = field(default_factory=list)


@dataclass
class Task:
    name: str
    category: str
    duration_minutes: int
    priority: int  # 1=high, 2=medium, 3=low


@dataclass
class ScheduleEntry:
    task: Task
    start_minute: int


class Scheduler:
    def __init__(self, owner: Owner, tasks: list[Task]):
        self.owner = owner
        self.tasks = tasks

    def generate_plan(self) -> list[ScheduleEntry]:
        """Return scheduled entries sorted by priority, fitting within available time."""
        pass

    def explain_plan(self) -> str:
        """Return a string explaining why tasks were ordered/included/excluded."""
        pass
