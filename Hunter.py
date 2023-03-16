import tkinter as tk
from tkinter import ttk
import time
def loading():
    root = tk.Tk()
    root.withdraw()
    loading_window = tk.Toplevel()
    loading_window.withdraw() # Hide the window until positioned
    loading_window.update_idletasks() # Update window dimensions before positioning
    x = (loading_window.winfo_screenwidth() // 2) - (900 // 2)
    y = (loading_window.winfo_screenheight() // 2) - (500 // 2)
    loading_window.geometry('900x500+{}+{}'.format(x, y))
    loading_window.deiconify() # Show the window after positioned
    loading_window.overrideredirect(True)  # Remove window border
    loading_window.attributes("-topmost", True)  # Keep the window on top
    # Load the image sequence
    image_sequence = []
    for i in range(1, 37):  # assuming the image sequence files are named 'image1.png' to 'image20.png'
        image = tk.PhotoImage(file="//vietsap002/projects/ILM/share/Dangvu/Script/DogeToolBox/src/LoadingBG/background_{}.png".format(i))
        image_sequence.append(image)
    # Animate the image sequence
    def animate(index):
        bg_label.configure(image=image_sequence[index])
        bg_label.image = image_sequence[index]
        loading_window.after(30, animate, (index + 1) % len(image_sequence))
    # Display the initial image and start the animation
    bg_label = tk.Label(loading_window, image=image_sequence[0])
    bg_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    animate(1)
    style = ttk.Style()
    style.theme_use("default")
    style.configure("blue.Horizontal.TProgressbar",foreground='#B5C9C8', background='#F28907', thickness=5, bordercolor='#902a05', troughcolor='#902a05',troughrelief='flat',relief='flat',border=0,borderwidth=0,bar='#8DE4AF')
    progress_bar = ttk.Progressbar(loading_window, orient=tk.HORIZONTAL, length=700, mode='determinate', style='blue.Horizontal.TProgressbar')
    progress_bar.place(relx=0.5, rely=0.8, anchor=tk.CENTER)
    progress_bar["maximum"] = 100
    # Update progress bar widget value
    for i in range(101):
        progress_bar["value"] = i
        loading_window.update()
        loading_window.update_idletasks()
        time.sleep(0.02)
    # Close the window
    loading_window.destroy()
loading()