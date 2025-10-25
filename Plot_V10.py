import tkinter as tk
from tkinter import filedialog, colorchooser, ttk
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from tkinter import messagebox, simpledialog
import json
import os


# Global variables
df = None
marker_x = None
grid_settings = {'visible': True, 'color': 'gray', 'linewidth': 0.5, 'ticks': True}

width_pad_root = 20

# Beispielhafte Marker-Datenstruktur
markers = []
entries = []

zoom_x = (50000, 70000)
zoom_y = (3.5e-7, 4.5e-7)

zoom_regions = [
]

legend_settings = {
    'fontsize': '10',
    'loc': 'upper right',
    'frameon': True,
    'alpha': 0.8,
    'ncol': '1',
    'visible': True
}

axis_settings = {
    "x_axis_type": "linear",
    "y_axis_type": "linear",
    "x_min": "",
    "x_max": "",
    "y_min": "",
    "y_max": "",
    "invert_x": False,
    "invert_y": False,
    "auto_ticks": True
}



mpl.rcParams.update({
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    "axes.labelsize": 12,
    "font.size": 12,
    "legend.fontsize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10
})



def reload_plot():
    global zoom_regions
    global legend_settings
    global axis_settings
    if entries is None:
        return
    
    # Entferne alle zusätzlichen Achsen außer der Hauptachse
    for extra_ax in fig.axes[1:]:
        fig.delaxes(extra_ax)

    ax.clear()
    secondary_ax = None



    entry_axes = {}  # Dictionary zur Zuordnung: entry → axis
    
    for entry in entries:
        try:
            df = pd.read_csv(entry['file_path'])
            x = df.iloc[:, 0]
            y = df.iloc[:, 1]
    
            if entry.get("y_axis", "primary") == "secondary":
                if secondary_ax is None:
                    secondary_ax = ax.twinx()
                secondary_ax.plot(x, y, color=entry['color'], label=entry['label'])
                entry_axes[entry['label']] = secondary_ax
            else:
                ax.plot(x, y, color=entry['color'], label=entry['label'])
                entry_axes[entry['label']] = ax
    
        except Exception as e:
            print(f"Fehler beim Laden der Datei {entry['file_path']}: {e}")
            continue


    
    title = title_entry.get()
    xlabel = xlabel_entry.get()
    ylabel = ylabel_entry.get()
    
    # Achsentypen   
    ax.set_xscale(axis_settings.get("x_axis_type"))
    ax.set_yscale(axis_settings.get("y_axis_type"))
    
    # Skalierung 
    try:
        if axis_settings.get("x_min") != "" and axis_settings.get("x_max") != "":
            ax.set_xlim(float(axis_settings["x_min"]), float(axis_settings["x_max"]))
        if axis_settings.get("y_min") != "" and axis_settings.get("y_max") != "":
            ax.set_ylim(float(axis_settings["y_min"]), float(axis_settings["y_max"]))
    except ValueError:
        print("Ungültige Werte für Achsenskalierung.")

    # invert Achsen
    if axis_settings.get("invert_x"):
        ax.invert_xaxis()
    if axis_settings.get("invert_y"):
        ax.invert_yaxis()
        
    print(markers)

    # Marker
    if marker_x is not None:
        ax.plot(marker_x, df.iloc[(df.iloc[:, 0] - marker_x).abs().idxmin(), 1], 'ro', label="Marker")

    for marker in markers:
        if marker['y-axis'] == 'primary':
            axis = ax
        elif marker['y-axis'] == 'secondary':            
            if 'secondary_ax' in locals() or 'secondary_ax' in globals():
                axis = secondary_ax
            else:
                print("Warnung: sekundäre Achse nicht vorhanden – Marker wird ignoriert oder auf Hauptachse gesetzt.")
                axis = ax  # Optional: Fallback auf Hauptachse
        else:
            continue  # oder Fehlerbehandlung  
        try:
            if marker['type'] == 'horizontal' and 'y' in marker:
                axis.axhline(y=marker['y'], color=marker['color'], linestyle='--', label=f"y={marker['y']}")
            elif marker['type'] == 'vertical' and 'x' in marker:
                axis.axvline(x=marker['x'], color=marker['color'], linestyle='--', label=f"x={marker['x']}")
            elif marker['type'] == 'point' and 'x' in marker and 'y' in marker:
                axis.plot(marker['x'], marker['y'], marker='o', color=marker['color'], label=f"({marker['x']}, {marker['y']})")
            elif marker['type'] in ('xpoint', 'ypoint') and 'x' in marker and 'y' in marker:
                axis.plot(marker['x'], marker['y'], marker='o', color=marker['color'], label=f"({marker['x']:.2e}, {marker['y']:.2e})")
        except:
            print("failed to set marker")
    
    # Achsentitel und Grid
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    secondary_ax.set_ylabel(ylabel)

    
    if grid_settings.get('visible') and grid_settings.get('ticks'):
        ax.grid(True, which='both', color=grid_settings.get('color', 'gray'), linewidth=grid_settings.get('linewidth', 1))
    elif grid_settings.get('visible'):
        ax.grid(True, color=grid_settings.get('color', 'gray'), linewidth=grid_settings.get('linewidth', 1))
    else:
        ax.grid(False)



    # Handles und Labels von beiden Achsen holen
    handles, labels = ax.get_legend_handles_labels()
    if secondary_ax is not None:
        handles1, labels1 = secondary_ax.get_legend_handles_labels()
        handles = handles + handles1
        labels = labels + labels1
    
 
    #print(legend_settings)
    if legend_settings.get('visible', True):
        legend_fontsize = legend_settings.get('fontsize', '10')
        legend_loc = legend_settings.get('loc', 'upper right')
        legend_frame = legend_settings.get('frameon', True)
        legend_alpha = legend_settings.get('alpha', 1.0)
        legend_ncol = int(legend_settings.get('ncol', 1))
        
        if secondary_ax is not None:    
            legend = secondary_ax.legend(
                handles, 
                labels,
                loc=legend_loc,
                frameon=legend_frame,
                fontsize=legend_fontsize,
                ncol=legend_ncol
            )
        else:
            legend = ax.legend(
                handles, 
                labels,
                loc=legend_loc,
                frameon=legend_frame,
                fontsize=legend_fontsize,
                ncol=legend_ncol
            )        
            
        legend.get_frame().set_alpha(legend_alpha)
    
        
    # Zoom-Inset(s)       

    print(zoom_regions)

    for region in zoom_regions:
        # Default values if not provided
        width = region.get('width', "30%")
        height = region.get('height', "30%")
        loc = region.get('loc', 'upper right')
        borderpad = float(region.get('border_pad', 1.5))   
        
        axins = inset_axes(ax, width=width, height=height, loc=loc, borderpad=borderpad)  # Abstand zum Rand

              
        #print(entries)
        
        for i, entry in enumerate(entries):
            print(entry['y_axis'])
            if entry['y_axis'] != 'primary':
                continue
            try:
                df = pd.read_csv(entry['file_path'])
                x = df.iloc[:, 0]
                y = df.iloc[:, 1]
                axins.plot(x, y, color=entry['color'])
            except Exception as e:
                print(f"Fehler beim Laden der Datei {entry['file_path']}: {e}")
                continue

    
        # Grid        
        if region.get('show_grid', True):
            axins.grid(True)
        else:
            axins.grid(False)
            
        # Achsen
        if region.get('ticks', True):  
            axins.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
        else:
            axins.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)


        # Marker im Zoom-Inset
        for marker in markers:
            if marker['type'] == 'horizontal' and region['y'][0] <= marker['y'] <= region['y'][1]:
                axins.axhline(y=marker['y'], color=marker['color'], linestyle='--')
            elif marker['type'] == 'vertical' and region['x'][0] <= marker['x'] <= region['x'][1]:
                axins.axvline(x=marker['x'], color=marker['color'], linestyle='--')
            elif marker['type'] in ('point', 'xpoint', 'ypoint') and region['x'][0] <= marker['x'] <= region['x'][1] and region['y'][0] <= marker['y'] <= region['y'][1]:
                axins.plot(marker['x'], marker['y'], marker='o', color=marker['color'])
                   

        axins.set_xlim(region['x'])
        axins.set_ylim(region['y'])
        
        if region.get('loc') in ('upper right', 'lower left'):
            mark_inset(ax, axins, loc1=2, loc2=4, fc="none", ec="0.5")
        
        elif region.get('loc') in ('upper left'):
            mark_inset(ax, axins, loc1=1, loc2=3, fc="none", ec="0.5")
            
        elif region.get('loc') in ('lower right'):
            mark_inset(ax, axins, loc1=3, loc2=1, fc="none", ec="0.5")
            
        elif region.get('loc') in ('center right'):
            mark_inset(ax, axins, loc1=2, loc2=3, fc="none", ec="0.5")            

        elif region.get('loc') in ('center left'):
            mark_inset(ax, axins, loc1=1, loc2=4, fc="none", ec="0.5") 

        elif region.get('loc') in ('lower center'):
            mark_inset(ax, axins, loc1=1, loc2=2, fc="none", ec="0.5")      
    
        elif region.get('loc') in ('upper center'):
            mark_inset(ax, axins, loc1=3, loc2=4, fc="none", ec="0.5")        
               

    canvas.draw()



def plot_manager():
    
    def ask_y_axis_and_subplot(parent, default_y_axis="primary", default_subplot=1):
        dialog = tk.Toplevel(parent)
        dialog.title("Plot-Einstellungen")
        dialog.geometry("300x200")
        dialog.grab_set()  # Modal
        dialog.transient(parent) # Abhängigkeit zum Parent-Fenster

        selected_y_axis = tk.StringVar(value=default_y_axis)
        selected_subplot = tk.IntVar(value=default_subplot)

        tk.Label(dialog, text="Y-Achse wählen:").pack(pady=5)
        tk.OptionMenu(dialog, selected_y_axis, "primary", "secondary").pack()

        tk.Label(dialog, text="Subplot wählen (1-4):").pack(pady=5)
        tk.OptionMenu(dialog, selected_subplot, 1, 2, 3, 4).pack()

        result = {"y_axis": default_y_axis, "subplot": default_subplot, "cancelled": True}

        def confirm():
            result["y_axis"] = selected_y_axis.get()
            result["subplot"] = selected_subplot.get()
            result["cancelled"] = False
            dialog.destroy()

        def cancel():
            dialog.destroy()

        tk.Button(dialog, text="OK", command=confirm).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(dialog, text="Abbrechen", command=cancel).pack(side=tk.RIGHT, padx=10, pady=10)
        dialog.wait_window()

        return result


    def edit_plot_window(parent_window, initial_data):
        edit_window = tk.Toplevel(parent_window)
        edit_window.title(f"Plot bearbeiten: {initial_data['label']}")
        edit_window.geometry("400x350")
        edit_window.grab_set()  # Modal
        edit_window.transient(parent_window) # Abhängigkeit zum Parent-Fenster

        # Variablen für die GUI-Elemente
        label_var = tk.StringVar(value=initial_data.get("label", ""))
        color_var = tk.StringVar(value=initial_data.get("color", "#000000"))
        y_axis_var = tk.StringVar(value=initial_data.get("y_axis", "primary"))
        subplot_var = tk.IntVar(value=initial_data.get("subplot", 1))

        # Ergebnis-Dictionary
        edited_data = None

        # --- GUI-Elemente erstellen ---
        row_idx = 0

        # Label
        tk.Label(edit_window, text="Plot Label:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        label_entry = tk.Entry(edit_window, textvariable=label_var, width=30)
        label_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Farbe
        tk.Label(edit_window, text="Plot Farbe:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        color_display = tk.Label(edit_window, bg=color_var.get(), relief="sunken", width=10)
        color_display.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")

        def pick_color():
            color_code = colorchooser.askcolor(title="Farbe auswählen")[1]
            if color_code:
                color_var.set(color_code)
                color_display.config(bg=color_code)

        tk.Button(edit_window, text="Farbe wählen", command=pick_color).grid(row=row_idx, column=2, padx=5, pady=5)
        row_idx += 1

        # Y-Achse
        tk.Label(edit_window, text="Y-Achse:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        tk.OptionMenu(edit_window, y_axis_var, "primary", "secondary").grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Subplot
        tk.Label(edit_window, text="Subplot (1-4):").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        tk.OptionMenu(edit_window, subplot_var, 1, 2, 3, 4).grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Sonstige Features (Beispiel: Checkbox für 'Is Dotted')
        # is_dotted_var = tk.BooleanVar(value=initial_data.get("is_dotted", False))
        # tk.Checkbutton(edit_window, text="Gepunktete Linie", variable=is_dotted_var).grid(row=row_idx, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        # row_idx += 1


        def save_changes():
            nonlocal edited_data
            edited_data = {
                "label": label_var.get(),
                "color": color_var.get(),
                "y_axis": y_axis_var.get(),
                "subplot": subplot_var.get(),
                # "is_dotted": is_dotted_var.get(), # Wenn du es hinzufügst
            }
            edit_window.destroy()

        def cancel_edit():
            edit_window.destroy()

        # Buttons
        tk.Button(edit_window, text="Änderungen speichern", command=save_changes).grid(row=row_idx, column=0, columnspan=2, padx=5, pady=10)
        tk.Button(edit_window, text="Abbrechen", command=cancel_edit).grid(row=row_idx, column=2, padx=5, pady=10)

        edit_window.grid_columnconfigure(1, weight=1) # Erlaubt der Label-Entry-Box, sich auszudehnen

        edit_window.wait_window() # Wartet, bis das Fenster geschlossen wird
        return edited_data
    
    manager_window = tk.Toplevel(root)
    manager_window.title("Plotmanager")
    manager_window.transient(root) # Macht das Manager-Fenster abhängig vom Hauptfenster

    listbox = tk.Listbox(manager_window, width=80)
    listbox.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

    # Diese Buttons sind außerhalb des plot_manager definiert, daher werden sie hier aktiviert
    save_button.config(state=tk.NORMAL)
    reload_button.config(state=tk.NORMAL)
    marker_button.config(state=tk.NORMAL)
    grid_button.config(state=tk.NORMAL)
    zoom_button.config(state=tk.NORMAL)
    legend_button.config(state=tk.NORMAL)
    axis_button.config(state=tk.NORMAL)

    def update_listbox():
        listbox.delete(0, tk.END)
        for entry in entries:
            filename = os.path.basename(entry['file_path'])
            y_axis = entry.get("y_axis", "primary")
            subplot = entry.get("subplot", 1) # Standardwert für subplot
            listbox.insert(tk.END, f"{entry['label']} ({entry['color']}) - {filename} [Y-Achse: {y_axis}, Subplot: {subplot}]")


    def add_entry():
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        label = simpledialog.askstring("Label", "Gib ein Label für den Plot ein:", parent=manager_window)
        if not label:
            return

        color = colorchooser.askcolor(title="Wähle eine Farbe", parent=manager_window)[1]
        if not color:
            return "#000000" # Standardfarbe, falls abgebrochen

        settings = ask_y_axis_and_subplot(manager_window)
        if settings["cancelled"]:
            return

        entries.append({
            "file_path": file_path,
            "label": label,
            "color": color,
            "y_axis": settings["y_axis"],
            "subplot": settings["subplot"]
        })
        update_listbox()

    def edit_entry():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("Hinweis", "Bitte wähle einen Eintrag aus.", parent=manager_window)
            return
        index = selected[0]
        current_entry = entries[index]

        # Öffne das separate Bearbeitungsfenster
        updated_data = edit_plot_window(manager_window, current_entry)

        if updated_data:
            # Aktualisiere den Eintrag mit den neuen Daten
            entries[index].update(updated_data)
            messagebox.showinfo("Erfolg", f"Plot '{updated_data['label']}' wurde aktualisiert.", parent=manager_window)
            update_listbox()
        else:
            messagebox.showinfo("Info", "Bearbeitung abgebrochen oder keine Änderungen vorgenommen.", parent=manager_window)

    def delete_entry():
        selected = listbox.curselection()
        if not selected:
            messagebox.showinfo("Hinweis", "Bitte wähle einen Eintrag aus.", parent=manager_window)
            return
        index = selected[0]
        confirm = messagebox.askyesno("Löschen bestätigen", "Möchtest du den ausgewählten Eintrag wirklich löschen?", parent=manager_window)
        if confirm:
            del entries[index]
            update_listbox()

    def save_config():
        file_path = filedialog.asksaveasfilename(parent=manager_window, defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "w") as f:
                    json.dump(entries, f, indent=2)
                messagebox.showinfo("Gespeichert", f"Konfiguration gespeichert unter:\n{file_path}", parent=manager_window)
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Speichern der Datei:\n{e}", parent=manager_window)


    def load_config():
        file_path = filedialog.askopenfilename(parent=manager_window, filetypes=[("JSON files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as f:
                    loaded_entries = json.load(f)
                if isinstance(loaded_entries, list):
                    entries.clear()
                    entries.extend(loaded_entries)
                    update_listbox()
                    messagebox.showinfo("Geladen", f"Konfiguration geladen von:\n{file_path}", parent=manager_window)
                else:
                    messagebox.showerror("Fehler", "Ungültiges Format in der JSON-Datei.", parent=manager_window)
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden der Datei:\n{e}", parent=manager_window)

    # Buttons
    tk.Button(manager_window, text="CSV-Datei hinzufügen", command=add_entry).grid(row=1, column=0, padx=5, pady=5)
    tk.Button(manager_window, text="Eintrag bearbeiten", command=edit_entry).grid(row=1, column=1, padx=5, pady=5)
    tk.Button(manager_window, text="Eintrag löschen", command=delete_entry).grid(row=1, column=2, padx=5, pady=5)
    tk.Button(manager_window, text="Konfig speichern", command=save_config).grid(row=2, column=0, padx=5, pady=5)
    tk.Button(manager_window, text="Konfig laden", command=load_config).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(manager_window, text="Schließen", command=manager_window.destroy).grid(row=2, column=2, padx=5, pady=5)

    update_listbox()

def choose_color():
    color_code = colorchooser.askcolor(title="Choose line color")[1]
    if color_code:
        color_entry.delete(0, tk.END)
        color_entry.insert(0, color_code)

def save_plot():
    filetypes = [('PDF file', '*.pdf'), ('SVG file', '*.svg'), ('EPS file', '*.eps')]
    selected_format = format_var.get()
    extension = selected_format.lower()
    file_path = filedialog.asksaveasfilename(defaultextension=f".{extension}", filetypes=filetypes)
    if file_path:
        try:
            width = float(width_entry.get())
            height = float(height_entry.get())
        except ValueError:
            width, height = 6, 6
        fig.set_size_inches(width, height)
        fig.savefig(file_path, format=extension)

def open_grid_settings():

    def choose_color():
        color_code = colorchooser.askcolor(title="Choose Grid Color", parent=grid_window)
        if color_code[1]:  # color_code[1] is the hex string
            grid_color_display.config(bg=color_code[1])
            grid_settings['color'] = color_code[1]
        grid_window.lift()  # Bringt das Grid-Fenster wieder in den Vordergrund
        grid_window.focus_force()  # Setzt den Fokus zurück auf das Grid-Fenster


    def apply_grid_settings():
        grid_settings['visible'] = grid_var.get()
        grid_settings['color'] = grid_color_display.cget("bg")
        grid_settings['linewidth'] = grid_width_slider.get()
        grid_settings['ticks'] = ticks_var.get()
        reload_plot()
        #grid_window.destroy()

    grid_window = tk.Toplevel(root)
    grid_window.title("Grid Settings")

    tk.Label(grid_window, text="Show Grid:").grid(row=0, column=0, sticky="w")
    grid_var = tk.BooleanVar(value=grid_settings['visible'])
    tk.Checkbutton(grid_window, variable=grid_var).grid(row=0, column=1, columnspan = 2)

    tk.Label(grid_window, text="Grid Color:").grid(row=1, column=0, sticky="w")
    grid_color_display = tk.Label(grid_window, bg=grid_settings['color'], width=10)
    grid_color_display.grid(row=1, column=1)
    tk.Button(grid_window, text="Choose Color", command=choose_color).grid(row=1, column=2)

    tk.Label(grid_window, text="Grid Line Width:").grid(row=2, column=0, sticky="w")
    grid_width_slider = tk.Scale(grid_window, from_=0.1, to=5.0, resolution=0.1, orient="horizontal")
    grid_width_slider.set(grid_settings['linewidth'])
    grid_width_slider.grid(row=2, column=1, columnspan=2)

    tk.Label(grid_window, text="all ticks").grid(row=3, column=0, sticky="w")
    ticks_var = tk.BooleanVar(value=grid_settings['ticks'])
    tk.Checkbutton(grid_window, variable=ticks_var).grid(row=3, column=1, columnspan = 2)

    tk.Button(grid_window, text="Apply", command=apply_grid_settings).grid(row=4, column=0, columnspan=3, pady=10)

def set_marker():
    def update_fields():
        marker_type = marker_type_var.get()
    
        x_entry.grid_remove()
        y_entry.grid_remove()
        plot_select_menu.grid_remove()
        source_type_menu.grid_remove()

    
        if marker_type in ["vertical", "xpoint"]:
            x_entry.grid(row=1, column=1)
        if marker_type in ["horizontal", "ypoint"]:
            y_entry.grid(row=2, column=1)
        if marker_type == "point":
            x_entry.grid(row=1, column=1)
            y_entry.grid(row=2, column=1)
    
        if marker_type in ["xpoint", "ypoint"]:
            plot_select_menu.grid(row=0, column=2)
            source_type_menu.grid(row=1, column=2)

            
    def edit_selected_marker(event):
        selection = marker_list.curselection()
        if selection:
            index = selection[0]
            marker = markers[index]
    
            marker_type_var.set(marker['type'])
            update_fields()
    
            # Formatierte Eingabe
            if marker.get('x') is not None:
                x_entry.delete(0, tk.END)
                x_entry.insert(0, f"{marker['x']}")
            else:
                x_entry.delete(0, tk.END)
    
            if marker.get('y') is not None:
                y_entry.delete(0, tk.END)
                y_entry.insert(0, f"{marker['y']}")
            else:
                y_entry.delete(0, tk.END)
    
            color_display.config(bg=marker.get('color', '#000000'))
    
            # Merke dir den Index für späteres Überschreiben
            marker_window.selected_index = index
            status_label.config(text=f"Bearbeite Eintrag #{index + 1}")
            
    def choose_color():
        color_code = colorchooser.askcolor(title="Choose Marker Color", parent=marker_window)
        if color_code[1]:
            color_display.config(bg=color_code[1])


    def add_marker():
        marker_type = marker_type_var.get()
        axis = source_type_var.get()
        color = color_display.cget("bg")
    
        # Plot-Auswahl auslesen
        selected_plot = plot_select_var.get()
        if not selected_plot:
            messagebox.showerror("Fehler", "Bitte wähle einen Plot aus.")
            return

        if marker_type in ('xpoint', 'ypoint'):
            selected_plot = plot_select_var.get()
            print(selected_plot)
        
            if not selected_plot:
                messagebox.showerror("Fehler", "Bitte wähle einen Plot aus.")
                return
            try:
                plot_index = int(selected_plot.split(":")[0])
                selected_entry = entries[plot_index]
                df = pd.read_csv(selected_entry['file_path'])
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Laden des Plots:\n{e}")
                return

        #try:
        if marker_type == "xpoint":
            x = float(x_entry.get())
            y = df.iloc[(df.iloc[:, 0] - x).abs().idxmin(), 1]

        elif marker_type == "ypoint":
            y = float(y_entry.get())
            x = df.iloc[(df.iloc[:, 1] - y).abs().idxmin(), 0]

        elif marker_type == "point":
            x = float(x_entry.get())
            y = float(y_entry.get())

        elif marker_type == "horizontal":
            x = None
            y = float(y_entry.get())

        elif marker_type == "vertical":
            x = float(x_entry.get())
            y = None

        new_marker = {
            'type': marker_type,
            'x': x,
            'y': y,
            'color': color,
            'source_plot': selected_plot,  # optional zur Nachverfolgung
            'y-axis' : axis
        }

        if hasattr(marker_window, 'selected_index'):
            markers[marker_window.selected_index] = new_marker
            del marker_window.selected_index
        else:
            markers.append(new_marker)

        status_label.config(text="Kein Eintrag ausgewählt")
        reload_plot()
        update_marker_list()
    
        #except Exception as e:
            #messagebox.showerror("Fehler", f"Fehler beim Setzen des Markers:\n{e}")



    def delete_selected_marker():
        selection = marker_list.curselection()
        if selection:
            index = selection[0]
            del markers[index]
            status_label.config(text="Kein Eintrag ausgewählt")
            reload_plot()
            update_marker_list()

    def update_marker_list():
        marker_list.delete(0, tk.END)
        for i, m in enumerate(markers):
            desc = f"{i+1}: {m['type']} "
            if m['type'] == "horizontal":
                desc += f"y={m['y']}"
            elif m['type'] == "vertical":
                desc += f"x={m['x']}"
            elif m['type'] in ("point", "xpoint", "ypoint"):
                desc += f"({m['x']:.2e}, {m['y']:.2e})"
            marker_list.insert(tk.END, desc)
            
    marker_window = tk.Toplevel(root)
    marker_window.title("Marker Settings")

    # Marker-Typ Auswahl
    tk.Label(marker_window, text="Marker Type:").grid(row=0, column=0, sticky="w")
    marker_type_var = tk.StringVar(value="vertical")
    marker_type_menu = tk.OptionMenu(marker_window, marker_type_var, "horizontal", "vertical", "point", "xpoint", "ypoint", command=lambda _: update_fields())
    marker_type_menu.grid(row=0, column=1)
    
    
    plot_select_var = tk.StringVar(value='Plot')
    plot_select_menu = tk.OptionMenu(marker_window, plot_select_var, *[f"{i}: {os.path.basename(e['file_path'])}" for i, e in enumerate(entries)])
    plot_select_menu.grid(row=0, column=2)
    plot_select_menu.grid_remove()

    
    source_type_var = tk.StringVar(value="primary")
    source_type_menu = tk.OptionMenu(marker_window, source_type_var, "primary", "secondary")
    source_type_menu.grid(row=1, column=2)
    source_type_menu.grid_remove()


    # Koordinatenfelder
    tk.Label(marker_window, text="X:").grid(row=1, column=0, sticky="w")
    x_entry = tk.Entry(marker_window)
    x_entry.grid(row=1, column=1)

    tk.Label(marker_window, text="Y:").grid(row=2, column=0, sticky="w")
    y_entry = tk.Entry(marker_window)
    y_entry.grid(row=2, column=1)

    update_fields()  # Initiale Anzeige der Felder

    # Farbwahl
    tk.Label(marker_window, text="Color:").grid(row=3, column=0, sticky="w")
    color_display = tk.Label(marker_window, bg="#000000", width=10)
    color_display.grid(row=3, column=1)
    tk.Button(marker_window, text="Choose Color", command=choose_color).grid(row=3, column=2)

    # Buttons
    tk.Button(marker_window, text="Add Marker", command=add_marker).grid(row=4, column=1, pady=10)
    tk.Button(marker_window, text="Delete Selected", command=delete_selected_marker).grid(row=4, column=2)

    # Marker-Liste
    tk.Label(marker_window, text="Current Markers:").grid(row=5, column=0, columnspan=2, sticky="w")
    marker_list = tk.Listbox(marker_window, width=40)
    marker_list.grid(row=6, column=0, columnspan=3)
    marker_list.bind("<Double-Button-1>", edit_selected_marker)

    status_label = tk.Label(marker_window, text="Kein Eintrag ausgewählt", fg="blue")
    status_label.grid(row=11, column=0, columnspan=3, sticky="w", pady=(5, 0))

    update_marker_list()

def open_zoom_settings():
    global zoom_regions
    def apply_zoom():
        #try:
            x_min = float(x_min_entry.get())
            x_max = float(x_max_entry.get())
            y_min = float(y_min_entry.get())
            y_max = float(y_max_entry.get())           
            width = width_entry.get()
            height = height_entry.get()
            loc = loc_entry.get()
            show_grid = zoom_grid_var.get()
            plot_ticks = plot_ticks_var.get()
            borderpad = space_entry.get()
            new_region = {
                'x': (x_min, x_max),
                'y': (y_min, y_max),
                'width': width if width else "30%",
                'height': height if height else "30%",
                'loc': loc if loc else "upper right",
                'show_grid': show_grid if show_grid else False,
                'ticks': plot_ticks if plot_ticks else False,
                'border_pad' : borderpad if borderpad else 1.5
            }
            
            # Wenn ein Index gespeichert ist, ersetze den Eintrag
            try:
                if hasattr(zoom_window, 'selected_index'):
                    zoom_regions[zoom_window.selected_index] = new_region
                    del zoom_window.selected_index
                else:
                    zoom_regions.append(new_region)
            except:
                print("index out of range")
            update_listbox()
            status_label.config(text="Kein Eintrag ausgewählt")
            reload_plot()
            #zoom_window.destroy()
        #except ValueError:
            #print("Zoom fehlgeschlagen")

    def update_listbox():
        zoom_listbox.delete(0, tk.END)
        for i, region in enumerate(zoom_regions):
            zoom_listbox.insert(tk.END, f"{i+1}: x={region['x']}, y={region['y']}, grid={region.get('show_grid','')}, ticks={region.get('ticks','')}, size=({region.get('width','')}, {region.get('height','')}), loc={region.get('loc','')}, space={region.get('border_pad', '')}")

    def delete_selected_region():
        selection = zoom_listbox.curselection()
        if selection:
            index = selection[0]
            del zoom_regions[index]
            update_listbox()
            status_label.config(text="Kein Eintrag ausgewählt")
            reload_plot()
        else:
            messagebox.showwarning("No selection", "Please select a zoom region to delete.")
            
    
    def edit_selected_region(event):
        print("select")
        selection = zoom_listbox.curselection()
        if selection:
            index = selection[0]
            region = zoom_regions[index]
            x_min_entry.delete(0, tk.END)
            x_min_entry.insert(0, str(region['x'][0]))
            x_max_entry.delete(0, tk.END)
            x_max_entry.insert(0, str(region['x'][1]))
            y_min_entry.delete(0, tk.END)
            y_min_entry.insert(0, str(region['y'][0]))
            y_max_entry.delete(0, tk.END)
            y_max_entry.insert(0, str(region['y'][1]))
            width_entry.delete(0, tk.END)
            width_entry.insert(0, region.get('width', '30%'))
            height_entry.delete(0, tk.END)
            height_entry.insert(0, region.get('height', '30%'))
            loc_entry.set(region.get('loc', 'upper right'))
            zoom_grid_var.set(region.get('show_grid', False))
            plot_ticks_var.set(region.get('ticks', False))
            space_entry.delete(0, tk.END)
            space_entry.insert(0, region.get('border_pad', 1.5))
            
            
            # Merke dir den Index für späteres Überschreiben
            zoom_window.selected_index = index
            status_label.config(text=f"Bearbeite Eintrag #{index + 1}")


    zoom_window = tk.Toplevel(root)
    zoom_window.title("Zoom Settings")

    tk.Label(zoom_window, text="Zoom X Min:").grid(row=0, column=0, sticky="w")
    x_min_entry = tk.Entry(zoom_window)
    x_min_entry.insert(0, str(zoom_x[0]))
    x_min_entry.grid(row=0, column=1)

    tk.Label(zoom_window, text="Zoom X Max:").grid(row=1, column=0, sticky="w")
    x_max_entry = tk.Entry(zoom_window)
    x_max_entry.insert(0, str(zoom_x[1]))
    x_max_entry.grid(row=1, column=1)

    tk.Label(zoom_window, text="Zoom Y Min:").grid(row=2, column=0, sticky="w")
    y_min_entry = tk.Entry(zoom_window)
    y_min_entry.insert(0, str(zoom_y[0]))
    y_min_entry.grid(row=2, column=1)

    tk.Label(zoom_window, text="Zoom Y Max:").grid(row=3, column=0, sticky="w")
    y_max_entry = tk.Entry(zoom_window)
    y_max_entry.insert(0, str(zoom_y[1]))
    y_max_entry.grid(row=3, column=1)
    
    #Grid
    tk.Label(zoom_window, text="Show Grid in Zoom:").grid(row=4, column=0, sticky="w")
    zoom_grid_var = tk.BooleanVar(value=True)
    tk.Checkbutton(zoom_window, variable=zoom_grid_var).grid(row=4, column=1)
    
    #Ticks
    tk.Label(zoom_window, text="Show Ticks in Zoom:").grid(row=5, column=0, sticky="w")
    plot_ticks_var = tk.BooleanVar(value=True)
    tk.Checkbutton(zoom_window, variable=plot_ticks_var).grid(row=5, column=1)
    
    # Größe und Position
    tk.Label(zoom_window, text="Inset Width (%):").grid(row=6, column=0, sticky="w")
    width_entry = tk.Entry(zoom_window)
    width_entry.insert(0, "30%")
    width_entry.grid(row=6, column=1)

    tk.Label(zoom_window, text="Inset Height (%):").grid(row=7, column=0, sticky="w")
    height_entry = tk.Entry(zoom_window)
    height_entry.insert(0, "30%")
    height_entry.grid(row=7, column=1)

    tk.Label(zoom_window, text="Inset Position:").grid(row=8, column=0, sticky="w")
    loc_entry = tk.StringVar(value="upper right")
    loc_options = ["upper right", "upper left", "lower right", "lower left", "center", "right", "center right", "center left", "lower center", "upper center"]
    loc_menu = tk.OptionMenu(zoom_window, loc_entry, *loc_options)
    loc_menu.grid(row=8, column=1)

    tk.Label(zoom_window, text="Distance to plot edge:").grid(row=9, column=0, sticky="w")
    space_entry = tk.Entry(zoom_window)
    space_entry.insert(0, 1.5)
    space_entry.grid(row=9, column=1)
    

    tk.Button(zoom_window, text="Apply Zoom", command=apply_zoom).grid(row=10, column=0, columnspan=2, pady=10)
    
    tk.Button(zoom_window, text="Delete Selected", command=delete_selected_region).grid(row=11, column=0, columnspan=2, pady=10)
    
    tk.Label(zoom_window, text="Zoom Regions:").grid(row=12, column=0, columnspan=2, sticky="w")
    zoom_listbox = tk.Listbox(zoom_window, width=120)
    zoom_listbox.grid(row=12, column=0, columnspan=2, sticky="w")
    zoom_listbox.bind("<Double-Button-1>", edit_selected_region)
    
    
    status_label = tk.Label(zoom_window, text="Kein Eintrag ausgewählt", fg="blue")
    status_label.grid(row=13, column=0, columnspan=2, sticky="w", pady=(5, 0))

    update_listbox()

def open_legend_settings():
    def apply_legend_settings():
        global legend_settings
        legend_settings = {
            'fontsize': fontsize_entry.get(),
            'loc': loc_var.get(),
            'frameon': frame_var.get(),
            'alpha': alpha_scale.get(),
            'ncol': ncol_entry.get(),
            'visible': visible_var.get()
        }
        # Hier kannst du die Einstellungen speichern oder direkt anwenden
        print("Legenden-Einstellungen:", legend_settings)
        #legend_window.destroy()
        reload_plot()  # Optional: Plot neu laden mit neuen Einstellungen

    legend_window = tk.Toplevel(root)
    legend_window.title("Legenden-Einstellungen")

    # Schriftgröße
    tk.Label(legend_window, text="Schriftgröße:").grid(row=0, column=0, sticky="w")
    fontsize_entry = tk.Entry(legend_window)
    fontsize_entry.insert(0, legend_settings.get('fontsize'))
    fontsize_entry.grid(row=0, column=1)

    # Position
    tk.Label(legend_window, text="Position:").grid(row=1, column=0, sticky="w")
    loc_var = tk.StringVar(value=legend_settings.get('loc'))
    loc_menu = tk.OptionMenu(legend_window, loc_var, "best", "upper right", "upper left", "lower right", "lower left", "center", "center right", "center left", "lower center", "upper center")
    loc_menu.grid(row=1, column=1)

    # Rahmen
    tk.Label(legend_window, text="Rahmen anzeigen:").grid(row=2, column=0, sticky="w")
    frame_var = tk.BooleanVar(value=legend_settings.get('frameon'))
    tk.Checkbutton(legend_window, variable=frame_var).grid(row=2, column=1)

    # Transparenz
    tk.Label(legend_window, text="Transparenz (0-1):").grid(row=3, column=0, sticky="w")
    alpha_scale = tk.Scale(legend_window, from_=0.0, to=1.0, resolution=0.1, orient="horizontal")
    alpha_scale.set(legend_settings.get('alpha'))
    alpha_scale.grid(row=3, column=1)

    # Spaltenanzahl
    tk.Label(legend_window, text="Spaltenanzahl:").grid(row=4, column=0, sticky="w")
    ncol_entry = tk.Entry(legend_window)
    ncol_entry.insert(0, legend_settings.get('ncol'))
    ncol_entry.grid(row=4, column=1)

    # Sichtbarkeit
    tk.Label(legend_window, text="Legende anzeigen:").grid(row=5, column=0, sticky="w")
    visible_var = tk.BooleanVar(value=legend_settings.get('visible'))
    tk.Checkbutton(legend_window, variable=visible_var).grid(row=5, column=1)

    # Button
    tk.Button(legend_window, text="Übernehmen", command=apply_legend_settings).grid(row=6, column=0, columnspan=2, pady=10)

def open_axis_settings():
    # Neues Subwindow
    axis_window = tk.Toplevel(root)
    axis_window.title("Achsen-Einstellungen")

    # Achsentyp Auswahl
    ttk.Label(axis_window, text="X-Achse:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    x_axis_type = ttk.Combobox(axis_window, values=["linear", "log"], state="readonly")
    x_axis_type.set(axis_settings.get('x_axis_type'))
    x_axis_type.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(axis_window, text="Y-Achse:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    y_axis_type = ttk.Combobox(axis_window, values=["linear", "log"], state="readonly")
    y_axis_type.set(axis_settings.get('y_axis_type'))
    y_axis_type.grid(row=0, column=3, padx=5, pady=5)

    # Skalierung
    ttk.Label(axis_window, text="X-Min:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    x_min_entry = ttk.Entry(axis_window)
    x_min_entry.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(axis_window, text="X-Max:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    x_max_entry = ttk.Entry(axis_window)
    x_max_entry.grid(row=2, column=1, padx=5, pady=5)

    ttk.Label(axis_window, text="Y-Min:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
    y_min_entry = ttk.Entry(axis_window)
    y_min_entry.grid(row=1, column=3, padx=5, pady=5)

    ttk.Label(axis_window, text="Y-Max:").grid(row=2, column=2, padx=5, pady=5, sticky="e")
    y_max_entry = ttk.Entry(axis_window)
    y_max_entry.grid(row=2, column=3, padx=5, pady=5)

 
    # Invertieren
    invert_x = tk.BooleanVar()
    invert_y = tk.BooleanVar()
    ttk.Checkbutton(axis_window, text="X-Achse invertieren", variable=invert_x).grid(row=3, column=0, columnspan=2, padx=5)
    ttk.Checkbutton(axis_window, text="Y-Achse invertieren", variable=invert_y).grid(row=3, column=2, columnspan=2, padx=5)


    # Ticks automatisch
    auto_ticks = tk.BooleanVar(value=True)
    ttk.Checkbutton(axis_window, text="Ticks automatisch setzen", variable=auto_ticks).grid(row=4, column=0, columnspan=4, padx=5)

    # Übernehmen
    def apply_settings():#
        global axis_settings
        axis_settings = {
            "x_axis_type": x_axis_type.get(),
            "y_axis_type": y_axis_type.get(),
            "x_min": x_min_entry.get(),
            "x_max": x_max_entry.get(),
            "y_min": y_min_entry.get(),
            "y_max": y_max_entry.get(),
            "invert_x": invert_x.get(),
            "invert_y": invert_y.get(),
            "auto_ticks": auto_ticks.get()
        }
        print("Einstellungen übernommen:", axis_settings)
        reload_plot()
        #axis_window.destroy()

    ttk.Button(axis_window, text="Übernehmen", command=apply_settings).grid(row=5, column=0, columnspan=4, pady=10)


root = tk.Tk()
root.title("CSV Plotter")

tk.Label(root, text="Plot Title:").grid(row=0, column=0)
title_entry = tk.Entry(root)
title_entry.insert(0, "Output Noise Plot")
title_entry.grid(row=0, column=1)

tk.Label(root, text="X-axis Label:").grid(row=1, column=0)
xlabel_entry = tk.Entry(root)
xlabel_entry.insert(0, "Frequency (Hz)")
xlabel_entry.grid(row=1, column=1)

tk.Label(root, text="Y-axis Label:").grid(row=2, column=0)
ylabel_entry = tk.Entry(root)
ylabel_entry.insert(0, "Noise (V/sqrt(Hz))")
ylabel_entry.grid(row=2, column=1)

tk.Label(root, text="Line Color:").grid(row=3, column=0)
color_entry = tk.Entry(root)
color_entry.insert(0, "blue")
color_entry.grid(row=3, column=1)
tk.Button(root, text="Choose Color", command=choose_color).grid(row=3, column=2)

tk.Label(root, text="Width (inches):").grid(row=4, column=0)
width_entry = tk.Entry(root)
width_entry.insert(0, "6")
width_entry.grid(row=4, column=1)

tk.Label(root, text="Height (inches):").grid(row=5, column=0)
height_entry = tk.Entry(root)
height_entry.insert(0, "4")
height_entry.grid(row=5, column=1)

tk.Label(root, text="Save Format:").grid(row=6, column=0)
format_var = tk.StringVar(value="PDF")
format_dropdown = ttk.Combobox(root, textvariable=format_var, values=["PDF", "SVG", "EPS"], state="readonly")
format_dropdown.grid(row=6, column=1)

legend_var = tk.BooleanVar(value=True)
tk.Checkbutton(root, text="Show Legend", variable=legend_var, command=reload_plot).grid(row=7, column=1)

tk.Button(root, text="Plot Manager", command=plot_manager, padx=width_pad_root).grid(row=8, column=0)
reload_button = tk.Button(root, text="Plot neu laden", command=reload_plot, state=tk.DISABLED, padx=width_pad_root)
reload_button.grid(row=8, column=1)

save_button = tk.Button(root, text="Save Plot", command=save_plot, state=tk.DISABLED, padx=width_pad_root)
save_button.grid(row=8, column=2)

grid_button = tk.Button(root, text="Grid Settings", command=open_grid_settings, state=tk.DISABLED, padx=width_pad_root)
grid_button.grid(row=9, column=0)

legend_button = tk.Button(root, text="Legend Settings", command=open_legend_settings, state=tk.DISABLED, padx=width_pad_root)
legend_button.grid(row=9, column=1)

zoom_button = tk.Button(root, text="Zoom Settings", command=open_zoom_settings, state=tk.DISABLED, padx=width_pad_root)
zoom_button.grid(row=9, column=2)

marker_button = tk.Button(root, text="Set Marker", command=set_marker, state=tk.DISABLED, padx=width_pad_root)
marker_button.grid(row=10, column=0)

axis_button = tk.Button(root, text="Axis", command=open_axis_settings, state=tk.DISABLED, padx=width_pad_root)
axis_button.grid(row=10, column=1)

plot_label = tk.Label(root, text="Plot").grid(row=11, column=0, columnspan=3)



fig, ax = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=12, column=0, columnspan=3)

root.mainloop()