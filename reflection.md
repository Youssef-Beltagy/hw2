# PawPal+ Project Reflection

In collaboration with kiro-cli.

## 1. System Design

**Core user actions (identified from the scenario):**

1. **Set up a pet and owner profile** — The user enters their name and adds one or more pets (name, species). This establishes who the owner is and which animals they care for.
2. **Define availability** — The user adds time blocks (start time + duration) representing when they are free to do pet care. Overlapping blocks are automatically merged. Past blocks are trimmed at scheduling time.
3. **Add and manage care tasks** — The user creates pet care tasks (e.g., walks, feeding, medication, grooming) with a duration, priority, optional due date, and optional recurrence. Tasks can be marked complete, deleted, or updated. Recurring tasks auto-reset after their reset interval.
4. **Generate a daily care plan** — The system produces a scheduled plan fitting tasks into availability blocks, prioritizing required tasks due soon, then by priority. The plan explains why each task was scheduled or skipped.
5. **Persist and resume** — The scheduler state is saved to disk (via pickle) so the user can close and reopen the app without losing data.

**a. Initial design**

The UML diagram includes five classes:

- **Owner** — Holds the owner's name and available minutes per day. Represents the human constraint on scheduling (how much time they can dedicate to pet care). An owner has one or more pets.
- **Pet** — Holds the pet's name and species. Each pet has its own list of care tasks. This lets the system distinguish tasks per pet if the owner has multiple animals.
- **Task** — Represents a single care activity (e.g., walk, feeding, medication). Holds a name, category, duration in minutes, and a priority level (postivie integers with smaller number representing higher priority). This is the core unit the scheduler works with.
- **ScheduleEntry** — Pairs a Task with a start time (in minutes from the start of the day). This separates "what to do" from "when to do it," keeping Task reusable across different schedules.
- **Scheduler** — The only class with real logic. Takes an Owner and a list of Tasks, then produces a daily plan. Has two methods: `generate_plan()` sorts tasks by priority and packs them into the available time, and `explain_plan()` produces a human-readable explanation of what was scheduled and what was dropped.

**b. Design changes**

Two changes were made after reviewing the initial design:

1. **Owner → Pet changed from one-to-one to one-to-many.** The user pointed out that an owner may have multiple pets. The `Owner.pet` attribute was replaced with `Owner.pets: list[Pet]`, and the UML relationship was updated from `"1" --> "1"` to `"1" --> "*"`. This was a straightforward requirement correction.

2. **Task gained a `pet` reference, and Scheduler gained `scheduled`/`skipped` state.** After AI review of the code, two issues were identified: (a) Task had no link back to Pet, so with multiple pets the scheduler couldn't tell which pet a task belonged to — fixed by adding `pet: Pet` to Task; (b) `explain_plan()` had no access to the results of `generate_plan()` since they shared no state — fixed by adding `scheduled` and `skipped` lists to Scheduler that `generate_plan()` populates and `explain_plan()` reads.

3. **Replaced `available_minutes` with explicit `Availability` blocks and `ScheduleEntry` with `Plan`.** The original design used a single integer for the owner's available time and a separate `ScheduleEntry` class to pair tasks with start times. This was replaced with a list of `Availability` objects (each with a `start_time: datetime` and `duration: timedelta`) on the Owner, and a `Plan` dataclass that holds scheduled tasks, scheduled explanations, and skipped explanations. This allows the scheduler to work across multiple disjoint time windows in a day and keeps scheduling output self-contained in a single object rather than spread across `ScheduleEntry` instances.

4. **Tasks gained recurrence, completion, and validation.** Tasks were originally simple data holders. They evolved to support: a `required` flag (mandatory vs optional), a `reset_every`/`next_reset_time` pair for recurring tasks that auto-reset after completion, a `mark_complete()` method that sets the next reset time for recurring tasks, a `reset()` method that clears completion when enough time has passed, and `__post_init__` validation enforcing that `required` and `reset_every` are mutually exclusive and that due dates are at day granularity. This made Task an active participant in scheduling logic rather than just a data container.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three main constraints:

1. **Time availability** — The owner defines explicit availability blocks (start time + duration). Tasks can only be scheduled within these windows. If a task's duration exceeds the remaining time in a block, it is skipped for that block but may fit in a later one.
2. **Priority** — Each task has a numeric priority (lower = more important). Higher-priority tasks are scheduled first within each availability block.
3. **Due date urgency** — Required tasks due today or tomorrow are promoted ahead of all other tasks, sorted by due date first and then by priority. This ensures time-sensitive tasks aren't crowded out by lower-urgency but higher-priority items that aren't due yet.

Priority and due date urgency were chosen as the most important constraints because pet care tasks like medication or vet visits have real deadlines, while routine tasks like grooming can be deferred. Time availability is the hard constraint — the owner simply can't do more than they have time for. Other possible constraints (e.g., task dependencies, preferred time of day, energy level) were omitted to keep the scheduler simple and predictable.

**b. Tradeoffs**

The scheduler uses a greedy, priority-first packing strategy: it sorts tasks by urgency (required tasks due soon come first, ordered by due date then priority), then iterates through each availability block and greedily assigns the next highest-priority task that fits in the remaining time. Once a task is skipped because it doesn't fit, it may still be scheduled in a later availability block, but the scheduler never backtracks to try a different combination within a single block.

This means the scheduler can miss optimal packings. For example, if a 50-minute block has a 40-minute priority-1 task and two 25-minute priority-2 tasks, the greedy approach schedules the 40-minute task (leaving 10 minutes wasted), even though scheduling both 25-minute tasks would use the time more fully. In fact, this issue can happen even if all tasks were of the same priority but it so happened that the 40-minute task was earlier in the list because it was inserted earlier. A knapsack-style algorithm could find the better packing, but would be more complex and harder to explain to the user.

This tradeoff is reasonable because pet care scheduling is a low-stakes, daily activity. The owner benefits more from a simple, predictable plan ("highest priority tasks go first") than from a mathematically optimal but harder-to-understand schedule. The greedy approach also makes the plan's reasoning easy to explain: each task is scheduled or skipped with a clear, single reason.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI throughout the project as a coding partner. The main ways I used it:

- **Incremental implementation** — I gave the AI small, specific instructions like "add a `required` field to Task" or "switch `duration_minutes` to a `timedelta`" and let it make the changes across all files. This kept each change small and reviewable.
- **Code review and bug detection** — After making my own changes to `pawpal_system.py`, I asked the AI to "read it and summarize my changes" and "review the code and let me know of any bugs." It caught several real bugs: a missing `return` after merging availability blocks, a stale variable reference in `generate_plan`, wrong index in `trim_availabilities`, and a double "m" suffix in the UI display.
- **Test generation** — I asked the AI to write unit tests covering all functions. It produced 45 tests and the test run itself uncovered the availability merge bug.
- **Boilerplate and UI work** — I delegated Streamlit UI updates (adding delete buttons, formatting task displays, wiring up persistence) to the AI since those were mechanical and low-risk.

The most helpful prompts were specific, scoped requests ("add X field", "fix those issues", "review the code") rather than broad ones. Asking the AI to summarize my own changes was useful for catching things I missed.

I also used the AI to write the docs and summarize this section of how I used it.

**b. Judgment and verification**

It often times tried to make changes that seemed to locally make sense but would not be good in the bigger picture. When the AI first suggested raising a `ValueError` in `reset()` for non-recurring tasks, I decided against it. My reasoning was that I wanted to call `reset()` in a loop over all tasks during `get_sorted_tasks`, and forcing callers to check `reset_every` before calling `reset()` would add unnecessary complexity. Instead, I changed `reset()` to silently return if the task isn't recurring.

I also didn't accept the AI's initial `add_availability` implementation that rejected overlapping blocks with an error. I changed it to merge overlapping blocks instead, since a user adding "9:00–10:00" and "9:30–10:30" almost certainly means "9:00–10:30" rather than making a mistake. I verified the merge logic by testing adjacent, overlapping, and contained intervals manually.

I also reviewed all the code and had the AI write unit tests to sanity check the code.

---

## 4. Testing and Verification

**a. What you tested**

The test suite (45 tests) covers every public method across all classes:

- **Task** (9 tests) — `mark_complete` (basic and recurring with reset time), `__post_init__` validation (required+reset_every mutual exclusivity, bad due date, valid due date, None due date), `reset` (no-op without reset time, no-op before reset time, clears when past reset time).
- **Pet** (5 tests) — `add_task` (sets pet back-reference), overwriting a task with the same name, `remove_task` (clears pet reference), removing a nonexistent task, `list_tasks`.
- **Owner** (10 tests) — `add_pet`, merging an existing pet (updates species, keeps tasks), `remove_pet`, removing a nonexistent pet, `list_pets`, `all_tasks` across multiple pets, `add_availability`, rejecting past availability, merging overlapping availability blocks, inserting non-overlapping blocks in sorted order, `remove_availability`.
- **Plan** (2 tests) — `__str__` output with and without skipped tasks.
- **Formatters** (5 tests) — `fmt_dt` with None and a real datetime, `fmt_td` with minutes only, hours+minutes, and zero.
- **Scheduler** (14 tests) — `add_owner`, ignoring duplicate owners, `remove_owner`, removing nonexistent owner, `get_all_tasks` sorted by priority, `get_sorted_tasks` (required-soon tasks first, same due date sorted by priority, completed tasks filtered out), `generate_plan` (tasks fit within availability, skips when no time, spans multiple availability blocks, empty tasks, no availability).

These tests were important because they verify the core scheduling contract: tasks are sorted correctly, fit into time windows, and edge cases (no tasks, no availability, completed tasks, overlapping availability) don't crash or produce wrong results. The validation tests ensure bad data is rejected early rather than causing subtle bugs downstream.

I also tested all the related features manually through the UI.

**b. Confidence**

I'm fairly confident the scheduler works correctly for the supported use cases. The 45 tests cover the happy paths and the most important edge cases, and the AI-driven code reviews caught several bugs before they reached users (stale variable references, missing returns, wrong indices).

Edge cases I would test next with more time:
- **Chained availability merges** — adding a block that bridges three or more existing blocks.
- **Recurring task lifecycle** — completing a recurring task, advancing time past the reset interval, and verifying it reappears in the next plan.
- **`trim_availabilities`** — blocks partially in the past being correctly shortened, and fully-past blocks being removed.
- **Pickle round-trip** — saving and loading a scheduler with owners, pets, tasks, and availabilities, then verifying all data survives.
- **Concurrent same-name tasks across pets** — two pets with a task named "Feed" to verify the skipped-explanation dict keys don't collide.

---

## 5. Reflection

**a. What went well**

The incremental development approach worked well. By building the system in small steps — starting with simple dataclasses, then adding fields one at a time, then layering in scheduling logic, then the UI — each change was small enough to review and test confidently. The AI code review loop was particularly effective: making changes myself, then asking the AI to read and find bugs caught issues (like the missing `return` in availability merging) that I would have missed on my own.

**b. What you would improve**

The scheduler's greedy algorithm is the biggest limitation. If I had another iteration, I would explore a two-pass approach: first schedule all required/urgent tasks greedily, then use a knapsack-style algorithm to fill remaining gaps with optional tasks. I would also decouple the scheduling logic from `datetime.now()` calls — currently `trim_availabilities`, `reset`, and `get_sorted_tasks` all call `datetime.now()` internally, which makes them hard to test deterministically. Injecting a clock or passing a "current time" parameter would make the system fully testable.

I also missed some logical fallacies like allowing a due date for a recurring task. I duct-taped an if condition to guard agains that in the streamlit app but didn't want to spend the time fixint it elsewhere.

I would like to be more efficient with my time.

**c. Key takeaway**

The most important thing I learned is that AI is most useful as a reviewer and implementer of well-scoped changes, not as an architect. When I gave the AI broad instructions, the results needed more correction. When I made design decisions myself and gave the AI specific, small tasks ("add this field", "fix these bugs", "write tests for all functions"), the output was reliable and saved significant time. The combination of human design judgment and AI implementation speed was more productive than either alone.

Also, I left updating the docs mostly to it.