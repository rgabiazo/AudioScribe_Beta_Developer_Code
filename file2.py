from file1 import MyGUI
import whisper
import os
import getpass
import textwrap
from moviepy.editor import VideoFileClip
import subprocess
import threading
from pytube import YouTube, exceptions
from pytube.exceptions import RegexMatchError, VideoUnavailable
from tkinter import messagebox
import tkinter as tk
import socket

# Find username of os
username = getpass.getuser()

# Valid file extensions
valid_extensions = ['.mp4', '.MOV', '.mp3', '.wav']

class AppManager:
    """Manages the application flow, including handling file inputs and starting the GUI."""

    def __init__(self):
        """Initialize the application manager."""
        # Store the path to the file provided by the user
        self.stored_file = ""

        # Create an instance of the GUI without starting its main loop yet
        self.gui_app = MyGUI()
        # Assign a callback function to the GUI.
        # This function will be called when the user provides a file or URL input
        self.gui_app.callback = self.handle_file_input
        # Start the GUI's main loop to make it responsive to user actions
        self.gui_app.run()

    def process_audio_and_transcribe(self, file_path):
        """ Processes the audio file, extracts audio if needed, and transcribes it."""
        # Get the file extension
        ext = os.path.splitext(file_path)[1]

        # Check for valid file extensions
        if ext not in valid_extensions:
            raise ValueError(f"Invalid file extension: {ext}. Supported extensions are .mp3, .wav, .mp4, and .MOV")

        # If the file is a video format, extract audio from it
        if ext in [".mp4", ".MOV"]:
            video = VideoFileClip(file_path)
            audio = video.audio

            # Check if transcription process is stopped by the user
            if self.gui_app.stop_loading:
                return "Transcription cancelled."

            derived_audio_name = os.path.basename(file_path).replace(ext, ".mp3")
            derived_audio_path = os.path.join(self.get_downloads_path(), derived_audio_name)

            # Save the extracted audio
            audio.write_audiofile(derived_audio_path)
            self.processed_file_path = derived_audio_path  # Update the path with the extracted audio's path

        # Load the transcription model and transcribe the audio
        model = whisper.load_model("base")
        result = model.transcribe(self.processed_file_path)  # Use the processed file path here

        # Check again if transcription process is stopped by the user
        if self.gui_app.stop_loading:
            return "Transcription cancelled."

        return result.get("text", "Transcription failed.")

    def create_and_open_text(self, text, filename, width=80):
        """ Create a text file with the transcribed text and open it."""
        # Wrap the text to the specified width for better readability
        wrapped_text = textwrap.fill(text, width=width)

        # Save the wrapped text to the specified file
        with open(filename, "w") as file:
            file.write(wrapped_text)

        # Use subprocess to open the saved text file
        subprocess.Popen(['open', filename])

    def display_and_save_transcription(self, transcription):
        """ Display the transcribed text in the GUI and save it to a text file."""
        # Extract the filename from the provided path and change its extension to .txt
        txt_file_name = os.path.splitext(os.path.basename(self.file_path))[0] + '.txt'
        # Determine the full path for saving the text file
        output_path = os.path.join(self.get_downloads_path(), txt_file_name)

        # Create a text file with the transcribed text and open it
        self.create_and_open_text(transcription, output_path, width=80)

        # Compose a message to inform the user about the saved transcription file
        message_to_show = f"Transcription Complete!\n\nFile Name: \n{os.path.basename(output_path)}\n\nSaved At: \n{self.get_downloads_path()}"
        # Display the message to the user using a messagebox
        messagebox.showinfo("Transcription Saved", message_to_show)

        # Show the transcribed text in the GUI
        self.gui_app.display_transcription(transcription)

    def find_file(self, name, extensions, start_path='/'):
        """Search for a file with a given name and extension starting from a specified path."""
        # Traverse through directories starting from the start
        for root, dirs, files in os.walk(start_path):
            # Check each specified extension
            for ext in extensions:
                # If a file with the specified name and current extension exists
                if f"{name}.{ext}" in files:
                    # Return the full path to the file
                    return os.path.join(root, f"{name}.{ext}")
        # Return None if no file was found with the given name and extensions
        return None

    def get_downloads_path(self):
        """Retrieve the path to the "Downloads" folder for the current user's operating system."""
        # Check if the current OS is Windows
        if os.name == 'nt':
            return os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            # Other OS (e.g., macOS, Linux): Directly retrieve the path to the "Downloads" directory
            return os.path.expanduser("~/Downloads")

    def threaded_transcription_task(self):
        """
        Handle the transcription process in a threaded manner.

        This allows for a responsive GUI while processing the transcription in the background.
        """
        # Reset the flag that checks if the loading animation should stop
        self.gui_app.stop_loading = False

        # Start the loading animation in a separate thread to keep the GUI responsive
        loading_thread = threading.Thread(target=self.gui_app.show_loading_animation)
        loading_thread.start()

        # Process the audio and get the transcription result
        transcription = self.process_audio_and_transcribe(self.file_path)

        # Signal to stop the loading animation after transcription is done
        self.gui_app.stop_loading = True

        # Check if the transcription process was interrupted or cancelled
        if transcription == "Transcription cancelled.":
            self.gui_app.clear_all_textboxes()  # Clear the textboxes immediately upon cancellation
            return

        # Update the transcription textbox with the transcription result or an error message
        self.gui_app.transcription_textbox.config(state=tk.NORMAL)
        self.gui_app.transcription_textbox.delete("1.0", tk.END)

        if transcription:
            self.display_and_save_transcription(transcription)
        else:
            # If there's an error in transcription, display an appropriate message to the user
            self.gui_app.display_transcription("Error in transcription.")
            messagebox.showerror("Error", "Error in transcription.")

    def clean_filename(self, filename):
        """Cleans up a filename by removing any potentially invalid characters."""
        # Define a list of characters that are not allowed in filenames
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']

        # Remove each invalid character from the filename
        for char in invalid_chars:
            filename = filename.replace(char, '')

        # Replace spaces with underscores for better filesystem compatibility
        return filename.replace(' ', '_')

    def is_connected(self):
        """Return True if there's an internet connection, False otherwise."""
        try:
            # connect to the host -- tells us if the host is actually reachable
            socket.create_connection(("www.google.com", 80))
            return True
        except OSError:
            # If any OS error occurs, it indicates that the connection failed
            pass
        return False

    def handle_file_input(self, user_input):
        """
        Handles the input provided by the user. This can be a file path or a YouTube URL.
        The function manages the various stages of audio processing and transcription.
        """

        # Validate if the user's input is the default placeholder or empty
        if user_input == "Drop a file, enter its name (.mp3, .wav, .mp4, .MOV) or a YouTube URL" or user_input == "":
            messagebox.showerror("Error", "Please input a valid file.")
            return  # Exit early

        # Check if there are spaces in the file name
        if " " in user_input:
            messagebox.showerror("Error", "Please ensure there are no spaces in the file name.")
            return  # Exit early

        self.stored_file = user_input

        # Check if the provided input is a potential YouTube URL
        if "youtube.com" in self.stored_file or "youtu.be" in self.stored_file:

            # Clear the result_textbox since you are processing a YouTube URL now
            self.gui_app.clear_result_textbox()

            # Check for an active internet connection
            if not self.is_connected():
                messagebox.showerror("Error",
                                     "No internet connection detected. Please check your connectivity and try again.")
                return  # Exit early

            # Attempt to process the YouTube URL
            try:
                yt = YouTube(user_input)
                video_file_name = self.clean_filename(yt.title)  # Cleaning the filename of any invalid characters
                audio_stream = yt.streams.filter(only_audio=True).first()

                # Validate if an audio stream is present
                if not audio_stream:
                    messagebox.showerror("Error", "No audio stream found for the given URL.")
                    return

                # Define where the audio will be downloaded
                output_path = self.get_downloads_path()
                filename = f"{video_file_name}.mp3"
                self.file_path = os.path.join(output_path, filename)

                # Download the audio stream
                audio_stream.download(output_path=output_path, filename=filename)

                # Update the processed file path for later use
                self.processed_file_path = self.file_path

            # Handle possible exceptions during YouTube URL processing
            except exceptions.RegexMatchError:
                messagebox.showerror("Error", "Invalid YouTube URL.")
                return
            except exceptions.VideoUnavailable:
                messagebox.showerror("Error", "The provided video is unavailable.")
                return

        else:  # If the input is not a YouTube URL

            # Check if the user input contains "http" or "www", suggesting it might be a URL but not a YouTube URL
            if "http" in self.stored_file or "www" in self.stored_file:
                messagebox.showerror("Error", f"'{self.stored_file}' is not a valid YouTube URL or supported file.")
                return

            self.file_name, self.file_ext = os.path.splitext(user_input)

            # Validate the file extension
            if self.file_ext not in valid_extensions:
                message = f"'{self.stored_file}' is not a valid mp3, wav, mp4, or MOV file."
                messagebox.showerror("Error", message)
                return  # Exit early

            # Try to find the file in the user's system
            self.file_path = self.find_file(self.file_name, [self.file_ext.lstrip('.')],
                                            start_path=os.path.expanduser("~"))

            # Update the processed file path
            self.processed_file_path = self.file_path

            # Check if the file was found
            if not self.file_path:
                message = f"File '{self.stored_file}' was not found."
                messagebox.showerror("Error", message)
                return  # Exit early

            # Update the GUI's result_textbox to display the determined file path.
            self.gui_app.display_result(self.file_path)

        # Handle the directory, ensuring its existence
        self.directory_only = os.path.dirname(self.file_path)
        os.makedirs(self.directory_only, exist_ok=True)

        # Start a separate thread for transcription to avoid freezing the GUI
        transcription_thread = threading.Thread(target=self.threaded_transcription_task)
        transcription_thread.start()









