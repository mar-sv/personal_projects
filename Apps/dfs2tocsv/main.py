import tkinter as tk
from tkinter import filedialog
import subprocess
from tkinter import ttk
import os
import sys
from functions import dfs2tocsv


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class FileSelectorGUI:
    def __init__(self, master):
        self.master = master
        master.title("File Selector")

        # Define style
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Arial', 12), padding=10)

        # Load and display image
        self.img = tk.PhotoImage(file=resource_path("DHI_logo.png"))

        self.label = tk.Label(master, image=self.img, width=300)
        self.label.pack(pady=10)

        # Create buttons
        self.button1 = ttk.Button(
            master, text="Select DFS2 file", command=self.select_file1)
        self.button1.pack(pady=10)

        self.button2 = ttk.Button(
            master, text="Select Polyline file", command=self.select_file2)
        self.button2.pack(pady=10)

        self.button3 = ttk.Button(
            master, text="Select Output Directory", command=self.select_output_directory)
        self.button3.pack(pady=10)

        self.button4 = ttk.Button(
            master, text="Run Script", command=self.run_script)
        self.button4.pack(pady=10)

        self.button5 = ttk.Button(master, text="About", command=self.show_about)
        self.button5.pack(pady=10)

        #self.button6 = ttk.Button(
        #    master, text="Exit", command=self.exit_window)
        #self.button6.pack(pady=10)

        # Initialize variables
        self.file1 = ""
        self.file2 = ""
        self.output_directory = ""

        # Create text widget for prompt
        self.prompt = tk.Text(master, height=10, width=50, font=('Arial', 12))
        self.prompt.pack(pady=10)

    def select_file1(self):
        self.file1 = filedialog.askopenfilename(filetypes=(
            ("DFS2 files", "*.dfs2"), ("All files", "*.*")))
        self.prompt.insert(
            tk.END, "Selected DFS2-file: {}\n".format(self.file1))

    def select_file2(self):
        self.file2 = filedialog.askopenfilename(
            filetypes=(("SHP files", "*.shp"), ("All files", "*.*")))
        self.prompt.insert(
            tk.END, "Selected shapefile: {}\n".format(self.file2))

    def select_output_directory(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv")
        if file_path:
            self.output_directory = file_path
            self.prompt.insert(
                tk.END, "Selected output directory: {}\n".format(self.output_directory))
        else:
            self.prompt.insert(tk.END, "No file selected for file 3.\n")

    def run_script(self):
        if not self.file1 or not self.file2:
            self.prompt.insert(
                tk.END, "Please select both files before running the script.\n")
            return
        if not self.output_directory:
            self.prompt.insert(
                tk.END, "Please select an output directory and filename before running the script.\n")
            return
        # Redirect stdout and stderr to the prompt
        #python_exe_path = r'C:\Users\masv\AppData\Local\jupyterlabdesktopappserver\python.exe'
        #script_path = r'C:\Github\personal_projects\Apps\dfs2tocsv\dfs2tocsv.py'
        #process = subprocess.Popen([python_exe_path, script_path, self.file1, self.file2, self.output_directory],
        #                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dfs2tocsv(self.file1,self.file2,self.output_directory)
      # Read output from the process and append it to the prompt
        #while True:
        #    output = process.stdout.readline()
        #    if not output and process.poll() is not None:
        #        break
        #    if output:
        #        self.prompt.insert(tk.END, output)

        #    error = process.stderr.readline()
        #    if not error and process.poll() is not None:
        #        break
        #    if error:
        #        self.prompt.insert(tk.END, error)

        # Wait for the process to complete and print the return code
        #return_code = process.poll()
        #if return_code == 0:
        #    self.prompt.insert(
        #        tk.END, "Script completed, check the destination folder!")
        #else:
         #   self.prompt.insert(
         #       tk.END, "It seems like there was an issue, please review the prompt or contact MASV")

    def show_about(self):
        about_text = """This app was created by Markus Svensson and is used for extracting results from a dfs2 using pre defined cross sections.  
        
        The extraction tool takes the dfs2 and a shapefile (where polylines are the only valied geometry of the shapefile).  
        
        The user is then defining a output directory where the result will be stored as a csv.  
        
        If there are multiple polylines in the shapefile, the results will be presented with the shapefiles index. 
        
        For further information or suggestions on improvements, please reach out to masv"""
        about_window = tk.Toplevel(self.master)
        about_window.title("About")
        about_label = tk.Label(about_window, text=about_text, font=("Arial", 12), anchor="w")
        about_label.pack()

    def exit_window(self):
        self.master.destroy()


root = tk.Tk()
gui = FileSelectorGUI(root)
root.geometry("500x700")
root.configure(bg="#F0F0F0")

# Set window icon
icon = tk.PhotoImage(file=resource_path("DHI_logo.png"))
root.iconphoto(False, icon)

root.mainloop()
