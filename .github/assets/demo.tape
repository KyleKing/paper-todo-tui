# VHS documentation
#
# Run with:
#  vhs < .github/assets/demo.tape
#
# Output:
#   Output <path>.gif               Create a GIF output at the given <path>
#   Output <path>.mp4               Create an MP4 output at the given <path>
#   Output <path>.webm              Create a WebM output at the given <path>
#
# Settings:
#   Set FontSize <number>           Set the font size of the terminal
#   Set FontFamily <string>         Set the font family of the terminal
#   Set Height <number>             Set the height of the terminal
#   Set Width <number>              Set the width of the terminal
#   Set LetterSpacing <float>       Set the font letter spacing (tracking)
#   Set LineHeight <float>          Set the font line height
#   Set Theme <string>              Set the theme of the terminal (JSON)
#   Set Padding <number>            Set the padding of the terminal
#   Set Framerate <number>          Set the framerate of the recording
#   Set PlaybackSpeed <float>       Set the playback speed of the recording
#
# Sleep:
#   Sleep <time>                    Sleep for a set amount of <time> in seconds
#
# Type:
#   Type[@<time>] "<characters>"    Type <characters> into the terminal with a
#                                   <time> delay between each character
#
# Keys:
#   Backspace[@<time>] [number]     Press the Backspace key
#   Down[@<time>] [number]          Press the Down key
#   Enter[@<time>] [number]         Press the Enter key
#   Space[@<time>] [number]         Press the Space key
#   Tab[@<time>] [number]           Press the Tab key
#   Left[@<time>] [number]          Press the Left Arrow key
#   Right[@<time>] [number]         Press the Right Arrow key
#   Up[@<time>] [number]            Press the Up Arrow key
#   Down[@<time>] [number]          Press the Down Arrow key
#   Ctrl+<key>                      Press the Control key + <key> (e.g. Ctrl+C)
#
# Display:
#   Hide                            Hide the subsequent commands from the output
#   Show                            Show the subsequent commands in the output

Output .github/assets/demo.gif
Set PlaybackSpeed 2.0
Set TypingSpeed 50ms

Set Theme "SpaceGray Eighties"
Set FontFamily "Hack Nerd Font Mono"

Set FontSize 15
Set Width 1200
Set Height 800

Hide
# Clean up any existing state
Type `rm -rf ~/.local/share/paper-todo/state.json`  Enter  Sleep 500ms
Type `clear`  Enter
Show

# Start the application
Type `uv run paper-todo`  Enter  Sleep 2s

# Add first task
Type "1"  Sleep 750ms
Type "Review pull requests"  Enter  Sleep 1s

# Add second task
Type "2"  Sleep 250ms
Type "Write documentation"  Enter  Sleep 500ms

# Add third task
Type "3"  Sleep 250ms
Type "Fix bug in timer"  Enter  Sleep 500ms

# Add fourth task
Type "4"  Sleep 250ms
Type "Update dependencies"  Enter  Sleep 500ms

# Show the tasks for a moment
Sleep 1s

# Randomly select a Time and Task
Type "s"  Sleep 10s

# Accept the task and let the timer run
Enter  Sleep 4s

# Complete the task
Type "C"  Sleep 2s

# Show final state
Sleep 1s

# Quit
Type "q"  Sleep 500ms
