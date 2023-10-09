import tkinter as tk
from tkinter import messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
from tkinter import filedialog
import time

class MyGUI:
    """GUI application for Transcribing Audio to Text."""

    def __init__(self, callback=None):
        """Initialize the main GUI window."""
        self.root = TkinterDnD.Tk()

        # GUI Window Configuration
        self.root.geometry("822x590")
        self.root.title("AudioScribe")
        self.stop_loading = False
        self.transcribing = False # To check if a transcription is ongoing


        # Setting up Main Menu
        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Open...", command=self.browse_file)
        self.filemenu.add_command(label="Save As...", command=self.save_as)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Close", command=self.on_closing)
        self.menubar.add_cascade(menu=self.filemenu, label="File")
        self.root.config(menu=self.menubar)

        # Configure grid layout
        self.root.grid_columnconfigure(0, minsize=120)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Create and place a label instructing the user
        self.label = tk.Label(self.root, text="AudioScribe - Your Audio Transcriber ", font=('Arial', 18))
        self.label.grid(row=0, column=0, columnspan=3, padx=10, pady=20, sticky=tk.E + tk.W)

        # MAIN TEXTBOX - To input file name or URL
        self.textbox = tk.Entry(self.root, font=('Arial', 16), width=110)
        self.textbox.grid(row=1, column=1, padx=10, sticky=tk.W)
        self.textbox.insert(0, "Drop a file, enter its name (.mp3, .wav, .mp4, .MOV) or a YouTube URL")
        # Add a "Browse" button next to the main textbox
        self.browse_button = tk.Button(self.root, text="Browse", command=self.browse_file)
        self.browse_button.grid(row=1, column=2)
        # Initial placeholder setting
        self.textbox.config(fg="grey")
        # Bind focus events to handle placeholder text
        self.textbox.bind("<FocusIn>", self._on_focus_in)
        self.textbox.bind("<FocusOut>", self._on_focus_out)
        # Configure drag and drop for the textbox
        self.textbox.drop_target_register(DND_FILES)
        self.textbox.dnd_bind('<<Drop>>', self._on_drop)

        # SOURCE LABEL & TEXTBOX - To display selected file path
        self.source_label = tk.Label(self.root, text="Source:", font=('Arial', 16))
        self.source_label.grid(row=2, column=0, padx=(30, 0), pady=(0, 25), sticky=tk.E)
        # Display the full file path or URL of the audio/video file being transcribed.
        self.result_textbox = tk.Text(self.root, height=1, font=('Arial', 16))
        self.result_textbox.grid(row=2, column=1, padx=10, pady=(0, 20), sticky=tk.W)  # Replacing pack with grid
        self.result_textbox.config(state=tk.DISABLED)

        # CONTROL BUTTONS
        # Storing the provided callback function, to be executed when the "Transcribe" button is pressed.
        self.callback = callback
        # Transcribe button initiates the transcription process.
        self.transcribe_button = tk.Button(self.root, text="Transcribe", command=self.retrieve_input)
        self.transcribe_button.grid(row=3, column=0, columnspan=2, pady=(20, 5), sticky=tk.N)  # Replacing pack with grid
        # Clear button to clear the textboxes
        self.clear_button = tk.Button(self.root, text="Clear/Stop", command=self.clear_all_textboxes)
        self.clear_button.grid(row=4, column=0, columnspan=2, pady=(5, 20), sticky=tk.N)  # Replacing pack with grid

        # TRANSCRIPTION TEXTBOX
        # Textbox displays the resulting transcribed text from the audio/video source.
        self.transcription_textbox = tk.Text(self.root, height=15, width=100, font=('Arial', 16), wrap=tk.WORD)
        self.transcription_textbox.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W + tk.E + tk.N + tk.S)
        self.transcription_textbox.config(fg="grey")
        self.transcription_textbox.config(state=tk.DISABLED)
        # Event bindings for the transcription textbox to handle placeholder behavior.
        self.transcription_textbox.bind("<FocusIn>", self._on_transcription_focus_in)
        self.transcription_textbox.bind("<FocusOut>", self._on_transcription_focus_out)

        # Save button allows the user to save the transcribed text to a file.
        self.save_button = tk.Button(self.root, text="Save", command=self.save_as)
        self.save_button.grid(row=6, column=2, sticky=tk.NW, pady=(10, 0))

        # Placeholder text is inserted in the center of the transcription textbox.
        self.align_text_in_textbox(self.transcription_textbox, "Transcribed Text")

    def retrieve_input(self):
        """
        Retrieve text from the textbox and, if a callback function was provided,
        call it with the retrieved text as its argument.
        """
        if self.transcribing:  # Check if transcription is ongoing
            return  # Do nothing and exit the method

        # Fetch the content of the textbox
        self.user_input = self.textbox.get()

        # If a callback function was provided, call it
        if self.callback:
            self.callback(self.user_input)

        self.root.focus()

    def display_result(self, message):
        """Display a message in the result textbox."""
        # Enable the textbox for editing
        self.result_textbox.config(state=tk.NORMAL)
        # Clear previous content
        self.result_textbox.delete("1.0", tk.END)
        # Insert the new message
        self.result_textbox.insert(tk.END, message)
        # Disable the textbox to make it read-only
        self.result_textbox.config(state=tk.DISABLED)


    def display_transcription(self, transcription):
        """ Displays the given transcription in the transcription textbox. """
        # Enable the textbox for editing
        self.transcription_textbox.config(state=tk.NORMAL, fg="black")
        # Clear any previous content
        self.transcription_textbox.delete("1.0", tk.END)
        # Insert the transcribed text
        self.transcription_textbox.insert(tk.END, transcription)
        # Disable the textbox to make it read-only
        self.transcription_textbox.config(state=tk.DISABLED)

    def clear_all_textboxes(self):
        """ Clear content of all textboxes. """
        self.stop_loading = True  # This stops the loading animation
        self.transcribing = False  # Reset the transcribing flag
        self.stop_loading = True  # This stops the loading animation

        # Clearing textbox...
        self.textbox.delete(0, tk.END)
        self.textbox.insert(0, "Drop a file, enter its name (.mp3, .wav, .mp4, .MOV) or a YouTube URL")
        self.textbox.config(fg="grey")

        # Clearing result_textbox...
        self.result_textbox.config(state=tk.NORMAL)
        self.result_textbox.delete("1.0", tk.END)
        self.result_textbox.config(state=tk.DISABLED)

        # Clearing transcription_textbox...
        self.transcription_textbox.config(state=tk.NORMAL)
        self.transcription_textbox.delete("1.0", tk.END)
        self.transcription_textbox.insert("1.0", "Transcribed Text")
        self.transcription_textbox.config(fg="grey", state=tk.DISABLED)

        self.root.focus()

    def clear_result_textbox(self):
        """Clear the content of the result textbox."""
        self.result_textbox.config(state=tk.NORMAL)
        self.result_textbox.delete("1.0", tk.END)
        self.result_textbox.config(state=tk.DISABLED)

    def _on_focus_in(self, event):
        """Function to be called when the textbox is focused on."""
        # Retrieve the current text in the textbox
        current_text = self.textbox.get()

        # If the current text is the placeholder
        if current_text == "Drop a file, enter its name (.mp3, .wav, .mp4, .MOV) or a YouTube URL":
            # Clear the textbox
            self.textbox.delete(0, tk.END)
            # Change the text color to black
            self.textbox.config(fg="black")

    def _on_focus_out(self, event):
        """Function to be called when the textbox loses focus."""
        # Retrieve the current text in the textbox
        current_text = self.textbox.get()

        # If the textbox is empty
        if not current_text:
            # Insert the placeholder at the beginning (for Text widget, if needed)
            self.textbox.insert("1.0", "Drop a file, enter its name (.mp3, .wav, .mp4, .MOV) or a YouTube URL")
            # Insert the placeholder at the beginning (for Entry widget)
            self.textbox.insert(0, "Drop a file, enter its name (.mp3, .wav, .mp4, .MOV) or a YouTube URL")
            # Change the color of the text to grey to indicate it's a placeholder
            self.textbox.config(fg="grey")

    def _on_transcription_focus_in(self, event):
        """Function to be called when the transcription textbox is focused on."""
        # Retrieve the current text in the transcription textbox
        current_text = self.transcription_textbox.get("1.0", "end-1c")

        # Check if the current text matches the placeholder
        if current_text == "Transcribed Text":
            # Clear the transcription textbox
            self.transcription_textbox.delete("1.0", tk.END)
            # Set the text color to grey
            self.transcription_textbox.config(fg="grey")

    def _on_transcription_focus_out(self, event):
        """Function to be called when the transcription textbox loses focus."""
        # Retrieve the current text in the transcription textbox
        current_text = self.transcription_textbox.get("1.0", "end-1c")

        # Check if the textbox is empty
        if not current_text:
            # Insert the placeholder text "Transcribed Text" into the textbox
            self.transcription_textbox.insert("1.0", "Transcribed Text")
            # Set the text color to grey to indicate placeholder text
            self.transcription_textbox.config(fg="grey")

    def align_text_in_textbox(self, textbox, text):
        """Left-aligns text in a Text widget."""
        textbox.insert("1.0", text)  # Simply insert the text without adding any spaces

    def _on_drop(self, event):
        """Handle the event when a file is dragged and dropped onto the application."""
        # Extract the file path of the dropped file and remove any extra spaces
        file_path = event.data.strip()
        # Extract the name of the file from the file path
        file_name = os.path.basename(file_path)

        # Clear any previous content in the main textbox
        self.textbox.delete(0, tk.END)
        # Insert the file name into the main textbox
        self.textbox.insert(0, file_name)
        # Change the text color to black to distinguish it from placeholder text
        self.textbox.config(fg="black")
        # Prepare the result textbox for content modification by setting its state to 'NORMAL'
        self.result_textbox.config(state=tk.NORMAL)
        # Clear any previous content in the result textbox
        self.result_textbox.delete("1.0", tk.END)
        # Insert the full file path into the result textbox
        self.result_textbox.insert("1.0", file_path)
        # Set the result textbox to read-only mode by changing its state to 'DISABLED'
        self.result_textbox.config(state=tk.DISABLED)

    def browse_file(self):
        """Open a file dialog to let the user manually select an audio/video file."""
        # Open a file dialog that restricts users to select audio/video file types or any type of files
        file_path = filedialog.askopenfilename(
            filetypes=[('Audio/Video Files', ('.mp3', '.mp4', '.MOV')), ('All Files', '*.*')])

        # Check if the user selected a file and didn't click cancel
        if file_path:
            # Extract just the filename from the full file path
            file_name = os.path.basename(file_path)
            # Clear any existing content from the main textbox
            self.textbox.delete(0, tk.END)
            # Display the filename in the main textbox
            self.textbox.insert(0, file_name)
            # Change the text color to black to distinguish from placeholder text
            self.textbox.config(fg="black")
            # Prepare the result textbox for content modification by setting its state to 'NORMAL'
            self.result_textbox.config(state=tk.NORMAL)
            # Clear any previous content from the result textbox
            self.result_textbox.delete("1.0", tk.END)
            # Display the full file path in the result textbox
            self.result_textbox.insert("1.0", file_path)
            # Change the result textbox back to read-only mode
            self.result_textbox.config(state=tk.DISABLED)

    def on_closing(self):
        """
        Callback method to display a confirmation messagebox to the user
        asking if they are sure about quitting the application.
        """
        # Ask the user if they are sure about closing the application
        if messagebox.askyesno(title="Quit?", message="Are you sure that you want to quit?"):
            self.root.destroy()

    def save_as(self):
        """Save the transcribed text to a specified location."""
        # Extract filename from the path provided in the textbox
        file_name_with_extension = os.path.basename(self.textbox.get())
        # Get the name of the file without its extension, for use as a default name in the save dialog.
        default_name, _ = os.path.splitext(file_name_with_extension)
        # Open a file dialog to get the location and name for saving the text
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[('Text files', '.txt'), ('All files', '*.*')],
                                                 title="Save As",
                                                 initialfile=default_name)  # Set the default filename

        # If the user selects a location (doesn't click cancel)
        if file_path:
            # Retrieve the transcribed text
            transcribed_text = self.transcription_textbox.get("1.0", "end-1c")

            # Save the text to the specified file
            with open(file_path, 'w') as file:
                file.write(transcribed_text)

            # Inform the user
            messagebox.showinfo("Success", f"File saved at: {file_path}")

    def show_loading_animation(self):
        """Display a loading animation in the transcription textbox."""
        # Flag indicating that the transcription process has started.
        self.transcribing = True
        # Flag to control the animation loop.
        # It starts as False to allow the animation to run.
        self.stop_loading = False

        # Continue the animation until `stop_loading` is set to True.
        while not self.stop_loading:
            for dots in range(1, 4):  # From "Transcribing." to "Transcribing..."
                # If the `stop_loading` flag is set to True, exit the loop.
                if self.stop_loading:
                    break
                self.transcription_textbox.config(state=tk.NORMAL)
                self.transcription_textbox.delete("1.0", tk.END)
                self.transcription_textbox.insert(tk.END, "Transcribing" + "." * dots)
                self.transcription_textbox.config(state=tk.DISABLED)
                self.root.update()  # Force the GUI to update
                time.sleep(0.5)  # Pause for a short duration before the next animation frame.

        self.transcribing = False  # Indicate that transcription has ended

    def run(self):
        """Start the main event loop of the GUI."""
        # Start the main loop for the GUI to keep it running and responsive
        self.root.mainloop()



