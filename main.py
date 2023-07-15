import re
import tkinter as tk
from datetime import datetime
import json

import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from customtkinter import CTkToplevel

from customjsonencoder import CustomEncoder


class App:
    def __init__(self, master):
        self.master = master
        self.master.title("TaskFlow")
        self.master.geometry("980x640")
        self.master.iconbitmap(default="icons/TaskFlow.ico")

        self.mode = tk.StringVar()
        self.mode_label = ctk.CTkLabel(master=master, textvariable=self.mode)
        self.mode_label.configure(font=("Yu Gothic UI", 15))
        self.mode_label.pack(anchor="nw", padx=60, pady=10)
        self.mode.set("Type a command to get started!")

        self.frame = ctk.CTkScrollableFrame(master=master)
        self.frame.pack(pady=0, padx=60, fill="both", expand=True)

        self.entry_widget = ctk.CTkEntry(self.master)
        self.entry_widget.configure(placeholder_text="Enter command...", font=("Lucida Console", 15), height=50)
        self.entry_widget.pack(side="bottom", fill="x", padx=15, pady=15)
        self.entry_widget.bind("<Tab>", self.autocomplete)
        self.entry_widget.bind("<Return>", self.parse)

        self.events = []

        # Mapping of command keywords to command functions
        self.command_keyword_mapping = {
            "addevent": self.addevent,
            "removeevent": self.removeevent,
            "removeall": self.removeall,
            "editevent": self.editevent,
            "view": self.view,
            "tagged": self.tagged,
            "search": self.search,
            "help": self.help,
            "exit": self.exit
        }

        self.load_data()

    def autocomplete(self, event):
        command_text = self.entry_widget.get()

        command_pattern = r"/(\w+)"  # Matches word after '/'

        match = re.match(command_pattern, command_text)
        if match:
            command_keyword = match.group(1)

            # Filter available command keywords based on the entered text
            filtered_commands = [command for command in self.command_keyword_mapping.keys() if
                                 command.startswith(command_keyword)]

            if filtered_commands:
                # Get the first filtered command as suggestion
                suggestion = filtered_commands[0]

                # Update the text in the Entry widget with the suggestion
                self.entry_widget.delete(0, tk.END)
                self.entry_widget.insert(tk.END, f"/{suggestion} ")

        # Prevent the default Tab behavior
        return "break"

    def parse(self, command=None):
        command_text = self.entry_widget.get()

        command_pattern = r"/(\w+)"  # Matches word after '/'
        title_pattern = r"['\"]([^'\"]*)['\"]"  # Matches text enclosed in double quotes
        time_pattern = r"(\d{2}:\d{2}-\d{2}:\d{2})"  # Matches time in the format HH:MM-HH:MM
        tag_pattern = r"#(\w+)"  # Matches tags with '#'

        # Extract event title
        match = re.search(title_pattern, command_text)
        if match:
            event_title = match.group(1)
            print("Event Title:", event_title)
        else:
            event_title = None

        # Extract time
        match = re.search(time_pattern, command_text)
        if match:
            event_time = match.group(1)
            print("Event Time:", event_time)
        else:
            event_time = None

        # Extract tags
        tags = re.findall(tag_pattern, command_text)
        print("Tags:", tags)

        # Extract command keyword
        match = re.match(command_pattern, command_text)
        if match:
            command_keyword = match.group(1)

            # Execute command
            if command_keyword in self.command_keyword_mapping:
                command_function = self.command_keyword_mapping[command_keyword]
                if command_function == self.view:
                    command_function()
                else:
                    command_function(event_title, event_time, tags=tags)
            else:
                CTkMessagebox(title="Invalid command",
                              message="Invalid command. \n\nUse /help to see available commands.",
                              icon="cancel", width=500)
        else:
            CTkMessagebox(title="No command entered",
                          message="Please enter a command using the following format: "
                                  "\n /command_name 'Argument1' Argument2 .."
                                  "\n For example: /addevent 'Take out the trash' 12:00-12:30 #chores"
                                  "\n Use /help to see available commands.",
                          icon="warning", width=500)

        # Clear text box
        self.entry_widget.delete(0, "end")

    def addevent(self, event_title, event_time, tags):
        if not event_time:
            CTkMessagebox(title="Incorrect time format",
                          message="Please include correct time format like this: \n\n /addevent 'Take out dog' "
                                  "13:15-13:45", width=500)
        else:
            # Extract start and end times
            event_start, event_end = event_time.split("-")

            # Convert string to datetime object
            event_datetime = {
                "start": datetime.strptime(event_start.strip(), "%H:%M"),
                "end": datetime.strptime(event_end.strip(), "%H:%M")
            }

            # Add event to the list of events
            self.events.append({
                "title": event_title,
                "datetime": event_datetime,
                "tags": tags
            })

            # Sort events based on datetime
            self.events.sort(key=lambda x: x["datetime"]["start"])

            self.mode.set("Event added")

            # Update UI
            self.update_ui(self.events)
            self.save_data()

    def removeevent(self, event_title, *_, tags=None):
        if not self.events:
            CTkMessagebox(title="No events yet",
                          message="There are no events to remove yet! \n\nUse the /addevent command to add an event.",
                          icon="warning", width=500)
            return

        event_found = False
        for event in self.events:
            if event.get('title').lower() == event_title.lower():
                msg = CTkMessagebox(title="Confirm deletion",
                                    message=f"Are you sure to want to remove '{event_title}'?",
                                    option_1="No", option_2="Yes", icon="warning", width=500)
                if msg.get() == "Yes":
                    self.events.remove(event)
                    event_found = True
                    break
                else:
                    event_found = True

        if not event_found:
            CTkMessagebox(title="Event not found",
                          message="This event was not found in your events. \nPlease check your spelling.",
                          icon="cancel", width=500)

        self.mode.set("Event removed")

        self.update_ui(self.events)
        self.save_data()

    def removeall(self, *_, tags=None):
        msg = CTkMessagebox(title="Remove all events?",
                            message="Are you sure you want to remove all events?",
                            icon="question", option_1="No", option_2="Yes", width=500)
        if msg.get() == "Yes":
            # Clear events and update UI
            self.events = []
            self.update_ui(self.events)

            # Clear JSON file
            with open('saved_events.json', 'w') as file:
                json.dump([], file)
            self.mode.set("All events removed")
        else:
            pass

    def editevent(self, *_):
        self.mode.set("Event removed")
        self.update_ui(self.events)

    def view(self, *_):
        self.mode.set("All events")
        self.update_ui(self.events)

    def tagged(self, *_, tags):
        # Filter events list based on tag
        tag_filtered_events = [event for event in self.events if
                               event.get("tags") and any(tag in event.get("tags", []) for tag in tags)]

        formatted_tags = ", ".join(tags)
        self.mode.set(f"Events with tag(s): {formatted_tags}                      \nEnter /view to display all events.")
        self.update_ui(tag_filtered_events)

    def search(self, *_):
        print("Search function")

    def help(self, *_):
        help_window = CTkToplevel(self.master)
        help_window.transient()
        help_window.grab_set()
        help_window.title("Help")
        help_window.geometry("475x650")

        help_label = ctk.CTkLabel(help_window, text="Help", font=("Helvetica", 25))
        help_label.pack(pady=10)

        option_menu = ctk.CTkOptionMenu(help_window, values=["General"])
        option_menu.pack()

        frame = ctk.CTkScrollableFrame(help_window)
        frame.pack(pady=5, padx=30, fill="both", expand=True)

        # THIS IS SHIT VERZIN EEN NIEUW SYSTEEM
        # tabel idee met grote en kleine labels

        def show_help_content(choice):
            for widget in frame.winfo_children():
                widget.destroy()

            if choice == "Commands":
                # Display help content for commands
                command_help_text = """
                Available Commands:

                /addevent 'Event Title' HH:MM-HH:MM #tag1 #tag2 ...
                    Add a new event with a title, start time, and optional tags.

                /removeevent 'Event Title'
                    Remove an event with the specified title.

                /editevent 'Event Title'
                    Edit an existing event with the specified title.

                /tagged '#tag'
                    Show events tagged with the specified tag.

                /search 'Keyword'
                    Search for events containing the specified keyword.

                /help
                    Show this help menu.
                """
                command_help_label = ctk.CTkLabel(frame, text=command_help_text, font=("Helvetica", 12))
                command_help_label.pack(padx=10, pady=10)

            elif choice == "General":
                # Display general help content
                general_help_text = """
                Welcome to TaskFlow Help!

                This application allows you to manage and track your tasks and events.
                Here are some general instructions to get started:

                1. Use the input field at the bottom to enter commands.

                2. Available commands:
                   - /addevent: Add a new event.
                   - /removeevent: Remove an existing event.
                   - /editevent: Edit an existing event.
                   - /tagged: Show events with a specific tag.
                   - /search: Search for events based on keywords.
                   - /help: Display this help menu.

                3. To add a new event, use the /addevent command followed by the event details.
                   For example: /addevent 'Meeting' 14:00-15:30 #work #meeting

                4. To remove an event, use the /removeevent command followed by the event title.

                5. To edit an event, use the /editevent command followed by the event title.

                6. To show events with a specific tag, use the /tagged command followed by the tag name.

                7. To search for events based on keywords, use the /search command followed by the keyword.

                8. Use the /help command to display this help menu at any time.

                Feel free to explore and manage your events with TaskFlow!
                """
                general_help_label = ctk.CTkLabel(frame, text=general_help_text, font=("Helvetica", 12))
                general_help_label.pack(padx=10, pady=10)

        # Initialize the help content based on the default option menu choice
        show_help_content(option_menu.get())

        # Bind the show_help_content function to the option menu selection
        option_menu.bind("<<OptionMenuSelected>>", lambda event: show_help_content(option_menu.get()))

    def exit(self, *_, tags=None):
        msg = CTkMessagebox(title="Exit TaskFlow?",
                            message="Are you sure you want to exit TaskFlow? \n Your data is saved automatically.",
                            icon="question", option_1="No", option_2="Yes", width=500)
        if msg.get() == "Yes":
            # Close program
            self.master.destroy()
        else:
            pass

    def update_ui(self, event_list):
        for widget in self.frame.winfo_children():
            widget.destroy()

        # Add events to the frame in sorted order
        for event in event_list:
            event_info = event["title"]
            if event["datetime"]:
                event_info += f"\n{event['datetime']['start'].strftime('%H:%M')}-{event['datetime']['end'].strftime('%H:%M')}"
            if event["tags"]:
                event_info += "\n" + " ".join(event["tags"])
            label = ctk.CTkButton(self.frame, text=event_info)
            label.configure(width=500, height=60, corner_radius=17, font=("Yu Gothic UI", 15))
            label.pack(anchor="center", padx=15, pady=5)

    def save_data(self):
        with open('saved_events.json', 'w') as file:
            json.dump(self.events, file, cls=CustomEncoder)

    def load_data(self):
        try:
            with open('saved_events.json', 'r') as file:
                try:
                    events_data = json.load(file)
                    self.events = []
                    for event in events_data:
                        event_datetime = {
                            "start": datetime.strptime(event['datetime']['start'], "%Y-%m-%dT%H:%M:%S"),
                            "end": datetime.strptime(event['datetime']['end'], "%Y-%m-%dT%H:%M:%S")
                        }

                        event['datetime'] = event_datetime
                        self.events.append(event)
                except (json.JSONDecodeError, ValueError):
                    # Handle JSON decoding error or value conversion error
                    self.events = []
        except IOError:
            print("io error")

            # Handle file reading error
            self.events = []
        self.update_ui(self.events)


def main():
    root = ctk.CTk()
    app = App(master=root)
    root.mainloop()


if __name__ == "__main__":
    main()
