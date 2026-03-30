# PawPal+ Project Reflection

## 1. System Design

**Core user actions (identified from the scenario):**

1. **Set up a pet and owner profile** — The user enters basic information about themselves (name, available time) and their pet (name, species/breed). This establishes the context and constraints for scheduling.
2. **Add and edit care tasks** — The user creates pet care tasks (e.g., walks, feeding, medication, grooming, enrichment) specifying at least a duration and priority for each. They can also edit existing tasks as needs change.
3. **Generate a daily care plan** — The system produces a scheduled plan for the day, ordering tasks by priority and fitting them within the owner's available time. The plan is displayed clearly and includes an explanation of why tasks were ordered or included/excluded.

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

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
