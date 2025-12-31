# Paper TODO TUI

Dice-based TODO application inspired by [Paper Apps TODO](https://gladdendesign.com/products/paper-apps-todo).

## Features

- Track up to 6 tasks at a time
- Roll dice to randomly select which task to work on
- Roll dice to determine work duration (1-5 = 10x minutes, 6 = 10-minute break)
- Countdown timer that persists across sessions
- Mark tasks as complete
- All state saved automatically to `~/.paper_todo_state.json`

## Installation

```bash
# Install dependencies
uv venv
source .venv/bin/activate
uv pip install -e .

# Run the app
paper-todo
```

## Usage

### Keyboard Shortcuts

- **1-6**: Edit task by number
- **R**: Roll dice to select a task
- **T**: Roll dice for time duration
- **Space**: Start/pause timer
- **C**: Mark current task as complete
- **Q**: Quit

### Workflow

1. Add your tasks using keys 1-6
2. Press **T** to roll for time duration:
   - Roll 1-5: Work for (roll × 10) minutes on a random task
   - Roll 6: Take a 10-minute break
3. Press **Space** to start the timer
4. Press **C** to mark the current task complete when done
5. Repeat!

## How It Works

The dice-based approach adds an element of randomness and fun to task management:

- Rolling for time creates variety in your work sessions
- Rolling for tasks helps you avoid decision paralysis
- The 10-minute break on rolling a 6 ensures regular breaks
- Timer persistence means you can quit and resume anytime
