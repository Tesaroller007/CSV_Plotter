import tkinter as tk
from tkinter import filedialog, colorchooser, ttk
import pandas as pd
#import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset
from tkinter import messagebox, simpledialog
import json
import os


# Global variables
df = None
marker_x = None
width_pad_root = 20

# Beispielhafte Marker-Datenstruktur
markers = []
entries = []

zoom_x = (40, 60)
zoom_y = (-0.25, 0.25)

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
    'subplots': {
        1: {
            "x_axis_type": "linear",
            "y_axis_type": "linear",
            "y2_axis_type": "linear",
            "x_min": "",
            "x_max": "",
            "y_min": "",
            "y_max": "",
            "y2_min": "",
            "y2_max": "",
            "invert_x": False,
            "invert_y": False,
            "invert_y2": False,
            "auto_ticks": True
        }
    },
}

subplot_settings = {
    'layout': '1x1',  # Format: 'rows x columns'
    'current': 1,     # Aktiver Subplot
    'subplots': {
        1: {
            'title': '',
            'xlabel': '',
            'ylabel': '',
            'grid': True,
            'legend': True,
            'position': 111  # Format: rows-columns-index
        }
    }
}

grid_settings = {'use_subplot1_for_all': True}

# Neuer globaler Default für Save-Dialog-Werte und Presets-Ordner
save_settings = {
    "format": "PDF",
    "width": 6,
    "height": 4
}

PRESETS_DIR = os.path.join(os.path.dirname(__file__), "presets")
os.makedirs(PRESETS_DIR, exist_ok=True)


#mpl.rcParams.update({
#    "text.usetex": True,
#    "font.family": "serif",
#    "font.serif": ["Computer Modern Roman"],
#    "axes.labelsize": 12,
#    "font.size": 12,
#    "legend.fontsize": 10,
#    "xtick.labelsize": 10,
#    "ytick.labelsize": 10
#})



def reload_plot():
    global zoom_regions, legend_settings, axis_settings, fig, canvas, subplot_settings
    if entries is None:
        return

    print(f"Subplot_settings: {subplot_settings}\n")
    print(f"Grid_settings: {grid_settings}\n")
    print(f"Axis_settings: {axis_settings}\n")
    print(f"Legend_settings: {legend_settings}\n")
    print(f"Zoom_regions: {zoom_regions}\n")
    print(f"Entries: {entries}\n")

    # Clear existing figure (reuse fig so canvas stays valid)
    fig.clf()
    fig.suptitle(title_entry.get(), fontsize=16)

    # Get layout settings
    rows, cols = map(int, subplot_settings['layout'].split('x'))
    fig.set_size_inches(6 * cols, 4 * rows)  # Adjust figure size based on layout

    # Ensure canvas widget matches figure pixel size so it can display all subplots
    try:
        dpi = fig.get_dpi()
        width_px = int(fig.get_size_inches()[0] * dpi)
        height_px = int(fig.get_size_inches()[1] * dpi)
        canvas.get_tk_widget().configure(width=width_px, height=height_px)
    except Exception:
        pass

    # Create grid of axes (always 2D array to simplify indexing)
    axes_arr = fig.subplots(rows, cols, squeeze=False)
    axes = {}
    secondary_axes = {}

    # Ensure all subplot settings exist (add ylabel_secondary default)
    for i in range(1, rows * cols + 1):
        if i not in subplot_settings['subplots']:
            subplot_settings['subplots'][i] = {
                'title': '',
                'xlabel': '',
                'ylabel': '',
                'ylabel_secondary': '',
                'grid': True,
                'legend': True,
                'position': int(f"{rows}{cols}{i}")
            }

    # Map 1..N -> axes[row][col] and apply per-subplot settings
    idx = 1
    for r in range(rows):
        for c in range(cols):
            ax = axes_arr[r][c]
            axes[idx] = ax
            subcfg = subplot_settings['subplots'].get(idx, {})

            # Detect if any plot uses secondary y-axis for this subplot (driven by entries)
            has_secondary = any(int(e.get('subplot', 1)) == idx and e.get('y_axis', 'primary') == 'secondary' for e in entries)

            # Create secondary y-axis if there are plots that require it
            if has_secondary:
                secondary_axes[idx] = ax.twinx()
            else:
                secondary_axes[idx] = None

            # Apply subplot specific settings
            ax.set_title(subcfg.get('title', ''))
            ax.set_xlabel(subcfg.get('xlabel', ''))
            ax.set_ylabel(subcfg.get('ylabel', ''))

            # Grid: respect per-subplot flag but use global appearance settings (color, linewidth, ticks)
            # If user selected "use subplot 1 for all", use subplot 1's grid visibility as override here.
            if grid_settings.get('use_subplot1_for_all', False):
                appearance_source = subplot_settings['subplots'].get(1, {})
            else:
                appearance_source = subcfg

            visible = subcfg.get('grid', grid_settings.get('grid', True))
            # per-subplot overrides (fallback to global)
            color = appearance_source.get('grid_color', grid_settings.get('color', 'gray'))
            linewidth = appearance_source.get('grid_linewidth', grid_settings.get('linewidth', 0.5))

            # Show grid according to selected checkbox:
            # - if "use_subplot1_for_all" is active, use subplot 1's 'grid' value as override for visibility
            if grid_settings.get('use_subplot1_for_all', False):
                vis_source = subplot_settings['subplots'].get(1, {})
                visible = vis_source.get('grid', grid_settings.get('visible', True))
            else:
                visible = subcfg.get('grid', grid_settings.get('visible', True))

            # Apply grid to primary axis only (secondary shares ticks/labels)
            try:
                if visible:
                    ax.grid(True, color=color, linewidth=linewidth)
                else:
                    # call grid(False) without line properties to avoid the UserWarning
                    ax.grid(False)
            except Exception:
                pass
            
            # Handle tick visibility per axis
            if grid_settings.get('use_subplot1_for_all', False):
                appearance_source = subplot_settings['subplots'].get(1, {})
            else:
                appearance_source = subcfg

            print(f"grid_settings for subplot {idx}: {appearance_source}")

            ticks_left = appearance_source.get('ticks_left', grid_settings.get('ticks_left', True))
            ticks_bottom = appearance_source.get('ticks_bottom', grid_settings.get('ticks_bottom', True))
            ticks_right = appearance_source.get('ticks_right', grid_settings.get('ticks_right', True))

            print(f"ticks_left: {ticks_left}, ticks_bottom: {ticks_bottom}, ticks_right: {ticks_right}")

            # Primary Y-axis (left)
            ax.tick_params(left=ticks_left, labelleft=ticks_left)
            
            # X-axis (bottom)
            ax.tick_params(bottom=ticks_bottom, labelbottom=ticks_bottom)

            # If secondary axis exists, handle its ticks
            if secondary_axes[idx] is not None:
                secondary_axes[idx].tick_params(right=ticks_right, labelright=ticks_right)

            # If a secondary axis exists, set its ylabel from stored settings and sync tick visibility
            if secondary_axes[idx] is not None:
                sec_ylabel = subcfg.get('ylabel_secondary', '') or ''
                try:
                    secondary_axes[idx].set_ylabel(sec_ylabel)
                except Exception:
                    pass

            idx += 1

    # Apply axis settings for each subplot (per-subplot axis_settings stored under axis_settings['subplots'])
    for subplot_num, ax in axes.items():
        if ax:
            subplot_axis_settings = axis_settings.get('subplots', {}).get(subplot_num, {})
            ax.set_xscale(subplot_axis_settings.get("x_axis_type", "linear"))
            ax.set_yscale(subplot_axis_settings.get("y_axis_type", "linear"))
            
            if subplot_axis_settings.get("auto_ticks", True):
                # Automatische Ticks: Major + Minor anzeigen
                ax.minorticks_on()
                ax.grid(True, which='minor')
            else:
                # Nur Hauptlinien anzeigen
                ax.minorticks_off()

            try:
                x_min = subplot_axis_settings.get("x_min", "")
                x_max = subplot_axis_settings.get("x_max", "")
                y_min = subplot_axis_settings.get("y_min", "")
                y_max = subplot_axis_settings.get("y_max", "")
                if x_min and x_max:
                    ax.set_xlim(float(x_min), float(x_max))
                if y_min and y_max:
                    ax.set_ylim(float(y_min), float(y_max))
                if subplot_axis_settings.get("invert_x", False):
                    ax.invert_xaxis()
                if subplot_axis_settings.get("invert_y", False):
                    ax.invert_yaxis()
            except ValueError:
                print(f"Ungültige Werte für Achsenskalierung in Subplot {subplot_num}")
            
            # Sekundäre Achse (falls vorhanden)
            sec_ax = secondary_axes.get(subplot_num)
            if sec_ax is not None:
                sec_ax.set_yscale(subplot_axis_settings.get("y2_axis_type", "linear"))
                try:
                    y2_min = subplot_axis_settings.get("y2_min", "")
                    y2_max = subplot_axis_settings.get("y2_max", "")
                    invert_y2 = subplot_axis_settings.get("invert_y2", False)

                    if y2_min and y2_max:
                        sec_ax.set_ylim(float(y2_min), float(y2_max))
                    if invert_y2:
                        sec_ax.invert_yaxis()
                except ValueError:
                    print(f"Ungültige Werte für sekundäre Achse in Subplot {subplot_num}")


    # Plot data in appropriate subplots (each entry has 'subplot' and 'y_axis')
    for entry in entries:
        subplot_num = int(entry.get('subplot', 1))
        y_axis_choice = entry.get('y_axis', 'primary')
        ax = axes.get(subplot_num)
        if ax is None:
            print(f"Warning: subplot {subplot_num} doesn't exist, skipping {entry.get('file_path')}")
            continue

        # ensure secondary axis exists if requested for the plot
        if y_axis_choice != 'primary':
            if secondary_axes.get(subplot_num) is None:
                secondary_axes[subplot_num] = ax.twinx()
                # set label from settings if present
                sec_label = subplot_settings['subplots'].get(subplot_num, {}).get('ylabel_secondary', '')
                if sec_label:
                    try:
                        secondary_axes[subplot_num].set_ylabel(sec_label)
                    except Exception:
                        pass
            plot_ax = secondary_axes[subplot_num]
        else:
            plot_ax = ax

        try:
            df = pd.read_csv(entry['file_path'])
            x = df.iloc[:, 0]
            y = df.iloc[:, 1]
            plot_ax.plot(x, y, color=entry.get('color', '#000000'), label=entry.get('label', ''))
        except Exception as e:
            print(f"Error plotting {entry.get('file_path')}: {e}")

    # Markers: try to draw markers on the appropriate axis if marker specifies a subplot
    for marker in markers:
        target_subplot = int(marker.get('subplot', 1))
        target_yaxis = marker.get('y-axis', 'primary')
        axis_for_marker = axes.get(target_subplot)
        show_markers = legend_settings.get('show_markers', True)
        if target_yaxis == 'secondary':
            if secondary_axes.get(target_subplot) is None and axis_for_marker is not None:
                secondary_axes[target_subplot] = axis_for_marker.twinx()
            axis_for_marker = secondary_axes.get(target_subplot, axis_for_marker)
        if axis_for_marker is None:
            continue
        try:
            if marker['type'] == 'horizontal' and 'y' in marker:
                label = f"y={marker['y']}" if legend_settings.get('show_markers', True) else ""
                axis_for_marker.axhline(y=marker['y'], color=marker['color'], linestyle='--', label=label)
            elif marker['type'] == 'vertical' and 'x' in marker:
                label = f"x={marker['x']}" if legend_settings.get('show_markers', True) else ""
                axis_for_marker.axvline(x=marker['x'], color=marker['color'], linestyle='--', label=label)
            elif marker['type'] == 'point' and 'x' in marker and 'y' in marker:
                label = f"({marker['x']}, {marker['y']})" if legend_settings.get('show_markers', True) else ""
                axis_for_marker.plot(marker['x'], marker['y'], marker='o', color=marker['color'], label=label)
            elif marker['type'] in ('xpoint', 'ypoint') and 'x' in marker and 'y' in marker:
                label = f"({marker['x']:.2e}, {marker['y']:.2e})" if legend_settings.get('show_markers', True) else ""
                axis_for_marker.plot(marker['x'], marker['y'], marker='o', color=marker['color'], label=label)
        except Exception:
            print("failed to set marker")

    if legend_settings.get('visible', True):
            legend_fontsize = legend_settings.get('fontsize', '10')
            legend_loc = legend_settings.get('loc', 'upper right')
            legend_frame = legend_settings.get('frameon', True)
            legend_alpha = legend_settings.get('alpha', 1.0)
            legend_ncol = int(legend_settings.get('ncol', 1))
            all_in_subplot1 = legend_settings.get('all_in_subplot1', False)

            if all_in_subplot1:
                # Sammle alle handles/labels über alle Subplots
                all_handles = []
                all_labels = []
                for i in range(1, rows * cols + 1):
                    ax_i = axes.get(i)
                    sec_i = secondary_axes.get(i)
                    # Sammle erst die handles/labels von der primären Achse
                    if ax_i:
                        h, l = ax_i.get_legend_handles_labels()
                        all_handles.extend(h)
                        all_labels.extend(l)
                    # Dann von der sekundären Achse, falls vorhanden
                    if sec_i:
                        h2, l2 = sec_i.get_legend_handles_labels()
                        all_handles.extend(h2)
                        all_labels.extend(l2)

                # Erstelle eine gemeinsame Legende in Subplot 1
                if all_handles:
                    # Wähle sekundäre Achse falls vorhanden, sonst primäre
                    attach_ax = secondary_axes.get(1) or axes.get(1) or next(iter(axes.values()))
                    legend = attach_ax.legend(all_handles, all_labels, 
                                            loc=legend_loc, frameon=legend_frame,
                                            fontsize=legend_fontsize, ncol=legend_ncol)
                    legend.get_frame().set_alpha(legend_alpha)
            else:
                # Separate Legenden für jeden Subplot
                for i in range(1, rows * cols + 1):
                    ax_i = axes.get(i)
                    sec_i = secondary_axes.get(i)
                    subplot_handles = []
                    subplot_labels = []

                    # Sammle erst handles/labels von primärer Achse
                    if ax_i:
                        h, l = ax_i.get_legend_handles_labels()
                        subplot_handles.extend(h)
                        subplot_labels.extend(l)
                    # Dann von sekundärer Achse falls vorhanden
                    if sec_i:
                        h2, l2 = sec_i.get_legend_handles_labels()
                        subplot_handles.extend(h2)
                        subplot_labels.extend(l2)

                    if subplot_handles:
                        # Hefte Legende an sekundäre Achse falls vorhanden
                        attach_ax = sec_i if sec_i is not None else ax_i
                        legend = attach_ax.legend(subplot_handles, subplot_labels,
                                             loc=legend_loc, frameon=legend_frame,
                                             fontsize=legend_fontsize, ncol=legend_ncol)
                        legend.get_frame().set_alpha(legend_alpha)

    for region in zoom_regions:
            region_subplot = int(region.get('subplot', 1))
            y_axis_choice = region.get('y_axis', 'primary')
            ax_parent = axes.get(region_subplot)
            
            if ax_parent is None:
                print(f"Warning: zoom region references non-existing subplot {region_subplot}")
                continue

            # Determine which axis to use based on y_axis_choice
            if y_axis_choice == 'secondary' and secondary_axes.get(region_subplot) is not None:
                ax_plot = secondary_axes[region_subplot]
            else:
                ax_plot = ax_parent

            width = region.get('width', "30%")
            height = region.get('height', "30%")
            loc = region.get('loc', 'upper right')
            borderpad = float(region.get('border_pad', 1.5))

            # Create inset axes
            axins = inset_axes(ax_parent, width=width, height=height, loc=loc, borderpad=borderpad)

            # Plot only entries that match both subplot and y-axis choice
            plotted_any = False
            for entry in entries:
                try:
                    if int(entry.get('subplot', 1)) != region_subplot:
                        continue
                    # Only plot if entry's y_axis matches the zoom region's y_axis_choice
                    if entry.get('y_axis', 'primary') != y_axis_choice:
                        continue
                    
                    df = pd.read_csv(entry['file_path'])
                    x = df.iloc[:, 0]
                    y = df.iloc[:, 1]
                    axins.plot(x, y, color=entry.get('color', '#000000'), label=entry.get('label', ''))
                    plotted_any = True
                except Exception as e:
                    print(f"Fehler beim Laden der Datei {entry.get('file_path','?')}: {e}")
                    continue

            # Set limits and grid for inset
            try:
                axins.set_xlim(region['x'])
                axins.set_ylim(region['y'])
                
                if region.get('show_grid', True):
                    c = grid_settings.get('color', 'gray')
                    lw = grid_settings.get('linewidth', 0.5)
                    axins.grid(True, color=c, linewidth=lw)
                else:
                    axins.grid(False)
                    
                # Handle ticks visibility
                if region.get('ticks', True):
                    axins.tick_params(left=True, bottom=True, labelleft=True, labelbottom=True)
                else:
                    axins.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)
            except Exception:
                pass

           # Mark inset with connectors (use ax_plot for correct axis reference)
            try:
                if region.get('loc') in ('upper right', 'lower left'):
                    mark_inset(ax_plot, axins, loc1=2, loc2=4, fc="none", ec="0.5")
                elif region.get('loc') in ('upper left',):
                    mark_inset(ax_plot, axins, loc1=1, loc2=3, fc="none", ec="0.5")
                elif region.get('loc') in ('lower right',):
                    mark_inset(ax_plot, axins, loc1=3, loc2=1, fc="none", ec="0.5")
                elif region.get('loc') in ('center right',):
                    mark_inset(ax_plot, axins, loc1=2, loc2=3, fc="none", ec="0.5")
                elif region.get('loc') in ('center left',):
                    mark_inset(ax_plot, axins, loc1=1, loc2=4, fc="none", ec="0.5")
                elif region.get('loc') in ('lower center',):
                    mark_inset(ax_plot, axins, loc1=1, loc2=2, fc="none", ec="0.5")
                elif region.get('loc') in ('upper center',):
                    mark_inset(ax_plot, axins, loc1=3, loc2=4, fc="none", ec="0.5")
            except Exception:
                pass
    # After layout & legend updates, try to nicely pack subplots
    try:
        fig.tight_layout()
    except Exception:
        try:
            fig.subplots_adjust(hspace=0.35, wspace=0.25)
        except Exception:
            pass

    # Finally update canvas
    try:
        canvas.draw_idle()
    except Exception:
        canvas.draw()


def open_subplot_settings():
    subplot_window = tk.Toplevel(root)
    subplot_window.title("Subplot Settings")
    subplot_window.geometry("500x600")

    widgets = {}  # store widget refs per subplot so we can read values on Apply

    # initialize rows/cols from current settings
    cur_rows, cur_cols = map(int, subplot_settings.get('layout', '1x1').split('x'))

    def update_subplot_entries():
        # recreate the scrollable content according to rows/cols spinbox
        try:
            rows = int(rows_var.get())
            cols = int(cols_var.get())
        except Exception:
            rows, cols = 1, 1

        # ensure subplots dict has required keys (don't overwrite existing values)
        for i in range(1, rows * cols + 1):
            if i not in subplot_settings['subplots']:
                subplot_settings['subplots'][i] = {
                    'title': '',
                    'xlabel': '',
                    'ylabel': '',
                    'ylabel_secondary': '',
                    'grid': True,
                    'legend': True,
                    'position': int(f"{rows}{cols}{i}")
                }

        # clear UI
        for widget in subplot_frame.winfo_children():
            widget.destroy()
        widgets.clear()

        # create UI for each subplot, filling from subplot_settings if available
        for i in range(1, rows * cols + 1):
            subcfg = subplot_settings['subplots'].get(i, {})
            subplot_label = ttk.LabelFrame(subplot_frame, text=f"Subplot {i}")
            subplot_label.pack(fill="x", padx=5, pady=5)

            ttk.Label(subplot_label, text="Title:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
            title_entry = ttk.Entry(subplot_label)
            title_entry.insert(0, subcfg.get('title', ''))
            title_entry.grid(row=0, column=1, padx=5, pady=2, sticky="ew")

            ttk.Label(subplot_label, text="X Label:").grid(row=1, column=0, padx=5, pady=2, sticky="w")
            xlabel_entry = ttk.Entry(subplot_label)
            xlabel_entry.insert(0, subcfg.get('xlabel', ''))
            xlabel_entry.grid(row=1, column=1, padx=5, pady=2, sticky="ew")

            ttk.Label(subplot_label, text="Y Label:").grid(row=2, column=0, padx=5, pady=2, sticky="w")
            ylabel_entry = ttk.Entry(subplot_label)
            ylabel_entry.insert(0, subcfg.get('ylabel', ''))
            ylabel_entry.grid(row=2, column=1, padx=5, pady=2, sticky="ew")

            # detect if any plot assigned to this subplot uses the secondary y-axis (driven by entries)
            has_secondary = any(int(e.get('subplot', 1)) == i and e.get('y_axis', 'primary') == 'secondary' for e in entries)

            # if secondary y-axis exists for this subplot, show an input for its ylabel
            if has_secondary:
                ttk.Label(subplot_label, text="Y Label (secondary):").grid(row=3, column=0, padx=5, pady=2, sticky="w")
                ylabel2_entry = ttk.Entry(subplot_label)
                ylabel2_entry.insert(0, subcfg.get('ylabel_secondary', ''))
                ylabel2_entry.grid(row=3, column=1, padx=5, pady=2, sticky="ew")
                next_row = 4
            else:
                ylabel2_entry = None
                next_row = 3

            # store refs (exclude grid and legend widgets)
            widgets[i] = {
                'title': title_entry,
                'xlabel': xlabel_entry,
                'ylabel': ylabel_entry,
                'ylabel_secondary': ylabel2_entry
            }

            # allow the entry to expand horizontally
            subplot_label.grid_columnconfigure(1, weight=1)

    # Layout selection
    layout_frame = ttk.LabelFrame(subplot_window, text="Layout Settings")
    layout_frame.pack(fill="x", padx=5, pady=5)

    ttk.Label(layout_frame, text="Rows:").grid(row=0, column=0, padx=5, pady=5)
    rows_var = ttk.Spinbox(layout_frame, from_=1, to=8, width=5)
    rows_var.set(str(cur_rows))
    rows_var.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(layout_frame, text="Columns:").grid(row=0, column=2, padx=5, pady=5)
    cols_var = ttk.Spinbox(layout_frame, from_=1, to=8, width=5)
    cols_var.set(str(cur_cols))
    cols_var.grid(row=0, column=3, padx=5, pady=5)

    ttk.Button(layout_frame, text="Update Layout", command=update_subplot_entries).grid(row=0, column=4, padx=5, pady=5)

    # Scrollable frame for subplot settings
    canvas = tk.Canvas(subplot_window)
    scrollbar = ttk.Scrollbar(subplot_window, orient="vertical", command=canvas.yview)
    subplot_frame = ttk.Frame(canvas)

    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
    scrollbar.pack(side="right", fill="y")
    canvas.create_window((0, 0), window=subplot_frame, anchor="nw")
    subplot_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    # initial population
    update_subplot_entries()

    def apply_settings():
        # read rows/cols and widget values back into subplot_settings
        try:
            rows = int(rows_var.get())
            cols = int(cols_var.get())
        except Exception:
            rows, cols = 1, 1
        subplot_settings['layout'] = f"{rows}x{cols}"

        # update each configured subplot from widgets
        for i, w in widgets.items():
            # preserve existing grid/legend flags if present in config (do not overwrite from UI)
            existing = subplot_settings['subplots'].get(i, {})
            subplot_settings['subplots'][i] = {
                'title': w['title'].get(),
                'xlabel': w['xlabel'].get(),
                'ylabel': w['ylabel'].get(),
                # save secondary ylabel if widget present
                'ylabel_secondary': w['ylabel_secondary'].get() if w.get('ylabel_secondary') else '',
                'grid': existing.get('grid', True),
                'grid_color': existing.get('grid_color', 'gray'),
                'grid_linewidth': existing.get('grid_linewidth', 0.5),
                'ticks_left': existing.get('ticks_left', True),
                'ticks_bottom': existing.get('ticks_bottom', True),
                'ticks_right': existing.get('ticks_right', True),
                'legend': existing.get('legend', True),
                'position': int(f"{rows}{cols}{i}")
            }

        # remove any leftover subplot configs beyond new size
        max_idx = rows * cols
        keys_to_remove = [k for k in list(subplot_settings['subplots'].keys()) 
                         if isinstance(k, (int, str)) and int(k) > max_idx]
        for k in keys_to_remove:
            del subplot_settings['subplots'][k]

        reload_plot()

    ttk.Button(subplot_window, text="Apply", command=apply_settings).pack(pady=10)

def plot_manager():
    
    def ask_y_axis_and_subplot(parent, default_y_axis="primary", default_subplot=1):
        dialog = tk.Toplevel(parent)
        dialog.title("Plot-Settings")
        dialog.geometry("300x200")
        dialog.grab_set()  # Modal
        dialog.transient(parent) # Abhängigkeit zum Parent-Fenster

        selected_y_axis = tk.StringVar(value=default_y_axis)
        selected_subplot = tk.IntVar(value=default_subplot)

        tk.Label(dialog, text="Choose Y-Axis:").pack(pady=5)
        tk.OptionMenu(dialog, selected_y_axis, "primary", "secondary").pack()

        
        # Layout auslesen und Anzahl der Subplots berechnen
        layout = subplot_settings.get('layout', '1x1')
        rows, cols = map(int, layout.split('x'))
        num_subplots = rows * cols

        # Standardwerte: 1 bis 4, dynamisch erweitern falls nötig
        subplot_choices = list(range(1, max(4, num_subplots) + 1))

        tk.Label(dialog, text=f"Select Subplot (1-{len(subplot_choices)}):").pack(pady=5)
        tk.OptionMenu(dialog, selected_subplot, *subplot_choices).pack()

        result = {"y_axis": default_y_axis, "subplot": default_subplot, "cancelled": True}

        def confirm():
            result["y_axis"] = selected_y_axis.get()
            result["subplot"] = selected_subplot.get()
            result["cancelled"] = False
            dialog.destroy()

        def cancel():
            dialog.destroy()

        tk.Button(dialog, text="OK", command=confirm).pack(side=tk.LEFT, padx=10, pady=10)
        tk.Button(dialog, text="Cancle", command=cancel).pack(side=tk.RIGHT, padx=10, pady=10)
        dialog.wait_window()

        return result


    def edit_plot_window(parent_window, initial_data):
        edit_window = tk.Toplevel(parent_window)
        edit_window.title(f"Edit Plot: {initial_data['label']}")
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
        tk.Label(edit_window, text="Plot Color:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        color_display = tk.Label(edit_window, bg=color_var.get(), relief="sunken", width=10)
        color_display.grid(row=row_idx, column=1, padx=5, pady=5, sticky="w")

        def pick_color():
            color_code = colorchooser.askcolor(title="Select Color")[1]
            if color_code:
                color_var.set(color_code)
                color_display.config(bg=color_code)

        tk.Button(edit_window, text="Select Color", command=pick_color).grid(row=row_idx, column=2, padx=5, pady=5)
        row_idx += 1

        # Y-Achse
        tk.Label(edit_window, text="Y-Axis:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        tk.OptionMenu(edit_window, y_axis_var, "primary", "secondary").grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
        row_idx += 1

        # Calculate Suplot choices based on current layout
        layout = subplot_settings.get('layout', '1x1')
        rows, cols = map(int, layout.split('x'))
        num_subplots = rows * cols
        subplot_choices = list(range(1, max(4, num_subplots) + 1))

        # Subplot
        tk.Label(edit_window, text="Subplot:").grid(row=row_idx, column=0, padx=5, pady=5, sticky="w")
        tk.OptionMenu(edit_window, subplot_var, *subplot_choices).grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
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
        tk.Button(edit_window, text="Save changes!", command=save_changes).grid(row=row_idx, column=0, columnspan=2, padx=5, pady=10)
        tk.Button(edit_window, text="Cancle", command=cancel_edit).grid(row=row_idx, column=2, padx=5, pady=10)

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
    subplot_button.config(state=tk.NORMAL)

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

        label = simpledialog.askstring("Label", "Enter a label for the plot:", parent=manager_window)
        if not label:
            return

        color = colorchooser.askcolor(title="choose a color", parent=manager_window)[1]
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
    tk.Button(manager_window, text="Add CSV-File", command=add_entry).grid(row=1, column=0, padx=5, pady=5)
    tk.Button(manager_window, text="Edit Entry", command=edit_entry).grid(row=1, column=1, padx=5, pady=5)
    tk.Button(manager_window, text="Delete Entry", command=delete_entry).grid(row=1, column=2, padx=5, pady=5)
    tk.Button(manager_window, text="Save Config", command=save_config).grid(row=2, column=0, padx=5, pady=5)
    tk.Button(manager_window, text="Load Config", command=load_config).grid(row=2, column=1, padx=5, pady=5)
    tk.Button(manager_window, text="Close", command=manager_window.destroy).grid(row=2, column=2, padx=5, pady=5)

    update_listbox()

def save_plot():
    def apply_save_settings():
        try:
            width = float(width_entry.get())
            height = float(height_entry.get())
            selected_format = format_var.get().lower()
            
            # Einstellungen speichern
            save_settings["format"] = selected_format
            save_settings["width"] = width
            save_settings["height"] = height            

            file_types = {
                "pdf": [('PDF file', '*.pdf')],
                "svg": [('SVG file', '*.svg')],
                "eps": [('EPS file', '*.eps')]
            }

            file_path = filedialog.asksaveasfilename(
                defaultextension=f".{selected_format}",
                filetypes=file_types.get(selected_format, [('All Files', '*.*')])
            )
            
            if file_path:
                fig.set_size_inches(width, height)
                fig.savefig(file_path, format=selected_format.lower())
                messagebox.showinfo("Success", f"Plot saved as {file_path}")
                save_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for width and height")
            
    save_window = tk.Toplevel(root)
    save_window.title("Save Plot Settings")
    save_window.geometry("300x200")
    
    # Format selection
    tk.Label(save_window, text="Format:").grid(row=0, column=0, padx=5, pady=5)
    format_var = tk.StringVar(value=save_settings["format"])
    format_menu = ttk.Combobox(save_window, textvariable=format_var, 
                              values=["PDF", "SVG", "EPS"], 
                              state="readonly")
    format_menu.grid(row=0, column=1, padx=5, pady=5)
    
    # Width
    tk.Label(save_window, text="Width (inches):").grid(row=1, column=0, padx=5, pady=5)
    width_entry = tk.Entry(save_window)
    width_entry.insert(0, save_settings["width"])
    width_entry.grid(row=1, column=1, padx=5, pady=5)
    
    # Height
    tk.Label(save_window, text="Height (inches):").grid(row=2, column=0, padx=5, pady=5)
    height_entry = tk.Entry(save_window)
    height_entry.insert(0, save_settings["height"])
    height_entry.grid(row=2, column=1, padx=5, pady=5)
    
    # Save button
    tk.Button(save_window, text="Save", command=apply_save_settings).grid(row=3, column=0, columnspan=2, pady=20)


def open_grid_settings():

    def choose_color():
        color_code = colorchooser.askcolor(title="Choose Grid Color", parent=grid_window)
        if color_code[1]:  # color_code[1] is the hex string
            grid_color_display.config(bg=color_code[1])
        grid_window.lift()
        grid_window.focus_force()

    def update_fields_grid(*args):
        target = target_var.get()
        try:
            si = int(target)
            subcfg = subplot_settings['subplots'].get(si, {})
            # Update all fields including individual tick settings
            grid_var.set(subcfg.get('grid', grid_settings.get('visible', True)))
            grid_color_display.config(bg=subcfg.get('grid_color', grid_settings.get('color', 'gray')))
            grid_width_slider.set(subcfg.get('grid_linewidth', grid_settings.get('linewidth', 0.5)))
            ticks_left_var.set(subcfg.get('ticks_left', grid_settings.get('ticks_left', True)))
            ticks_bottom_var.set(subcfg.get('ticks_bottom', grid_settings.get('ticks_bottom', True)))
            ticks_right_var.set(subcfg.get('ticks_right', grid_settings.get('ticks_right', True)))
        except Exception:
            grid_var.set(grid_settings.get('visible', True))
            grid_color_display.config(bg=grid_settings.get('color', 'gray'))
            grid_width_slider.set(grid_settings.get('linewidth', 0.5))
            ticks_left_var.set(grid_settings.get('ticks_left', True))
            ticks_bottom_var.set(grid_settings.get('ticks_bottom', True))
            ticks_right_var.set(grid_settings.get('ticks_right', True))

        if target == "1":
            use_for_all_chk.grid(row=7, column=0, columnspan=3, sticky="w", padx=5, pady=2)
            use_for_all_var.set(grid_settings.get('use_subplot1_for_all', False))
        else:
            use_for_all_chk.grid_remove()

    def apply_grid_settings():
        target = target_var.get()
        visible = grid_var.get()
        color = grid_color_display.cget("bg")
        linewidth = grid_width_slider.get()
        ticks_left = ticks_left_var.get()
        ticks_bottom = ticks_bottom_var.get()
        ticks_right = ticks_right_var.get()

        try:
            si = int(target)
            if si not in subplot_settings['subplots']:
                rows, cols = map(int, subplot_settings['layout'].split('x'))
                subplot_settings['subplots'][si] = {
                    'title': '',
                    'xlabel': '',
                    'ylabel': '',
                    'ylabel_secondary': '',
                    'grid': True,
                    'legend': True,
                    'position': int(f"{rows}{cols}{si}")
                }

            subcfg = subplot_settings['subplots'][si]
            subcfg['grid'] = visible
            subcfg['grid_color'] = color
            subcfg['grid_linewidth'] = float(linewidth)
            subcfg['ticks_left'] = bool(ticks_left)
            subcfg['ticks_bottom'] = bool(ticks_bottom)
            subcfg['ticks_right'] = bool(ticks_right)
        except Exception:
            grid_settings['visible'] = visible
            grid_settings['color'] = color
            grid_settings['linewidth'] = float(linewidth)
            grid_settings['ticks_left'] = bool(ticks_left)
            grid_settings['ticks_bottom'] = bool(ticks_bottom)
            grid_settings['ticks_right'] = bool(ticks_right)

        if target == "1":
            grid_settings['use_subplot1_for_all'] = bool(use_for_all_var.get())

        reload_plot()

    def reset_grid_defaults():
        # define defaults
        defaults = {
            'visible': True,
            'color': 'gray',
            'linewidth': 0.5,
            'ticks_left': True,
            'ticks_bottom': True,
            'ticks_right': True,
            'use_subplot1_for_all': False
        }

        # update global grid_settings
        grid_settings.update(defaults)

        # update per-subplot settings to defaults (preserve unrelated keys)
        rows, cols = map(int, subplot_settings['layout'].split('x'))
        for si in range(1, rows * cols + 1):
            subcfg = subplot_settings['subplots'].setdefault(si, {})
            subcfg['grid'] = defaults['visible']
            subcfg['grid_color'] = defaults['color']
            subcfg['grid_linewidth'] = float(defaults['linewidth'])
            subcfg['ticks_left'] = defaults['ticks_left']
            subcfg['ticks_bottom'] = defaults['ticks_bottom']
            subcfg['ticks_right'] = defaults['ticks_right']

        # update UI controls to reflect defaults for currently selected target
        grid_var.set(defaults['visible'])
        grid_color_display.config(bg=defaults['color'])
        grid_width_slider.set(defaults['linewidth'])
        ticks_left_var.set(defaults['ticks_left'])
        ticks_bottom_var.set(defaults['ticks_bottom'])
        ticks_right_var.set(defaults['ticks_right'])
        use_for_all_var.set(defaults['use_subplot1_for_all'])

        # refresh fields and redraw plot
        update_fields_grid()
        reload_plot()

    grid_window = tk.Toplevel(root)
    grid_window.title("Grid Settings")

    # Target selection: individual subplot numbers only (no "all" option)
    rows, cols = map(int, subplot_settings['layout'].split('x'))
    options = [str(i) for i in range(1, rows * cols + 1)]
    tk.Label(grid_window, text="Apply to Subplot:").grid(row=0, column=0, sticky="w")
    # default to current active subplot if available, otherwise 1
    current_target = str(subplot_settings.get('current', 1)) if 'current' in subplot_settings else "1"
    target_var = tk.StringVar(value=current_target)
    target_menu = ttk.Combobox(grid_window, values=options, textvariable=target_var, state="readonly")
    target_menu.grid(row=0, column=1, columnspan=2, sticky="w")
    # update fields whenever selection changes
    target_var.trace_add("write", update_fields_grid)

    tk.Label(grid_window, text="Show Grid:").grid(row=1, column=0, sticky="w")
    grid_var = tk.BooleanVar(value=grid_settings.get('visible', True))
    tk.Checkbutton(grid_window, variable=grid_var).grid(row=1, column=1, columnspan=2, sticky="w")

    tk.Label(grid_window, text="Grid Color:").grid(row=2, column=0, sticky="w")
    grid_color_display = tk.Label(grid_window, bg=grid_settings.get('color', 'gray'), width=10)
    grid_color_display.grid(row=2, column=1)
    tk.Button(grid_window, text="Choose Color", command=choose_color).grid(row=2, column=2)

    tk.Label(grid_window, text="Grid Line Width:").grid(row=3, column=0, sticky="w")
    grid_width_slider = tk.Scale(grid_window, from_=0.1, to=5.0, resolution=0.1, orient="horizontal")
    grid_width_slider.set(grid_settings.get('linewidth', 0.5))
    grid_width_slider.grid(row=3, column=1, columnspan=2, sticky="we")

    # Replace single ticks checkbox with three separate controls
    tk.Label(grid_window, text="Ticks:").grid(row=4, column=0, sticky="w")
    
    ticks_left_var = tk.BooleanVar(value=grid_settings.get('ticks_left', True))
    tk.Checkbutton(grid_window, text="Left (Primary Y)", variable=ticks_left_var).grid(row=4, column=1, padx=5, sticky="w")
    
    ticks_bottom_var = tk.BooleanVar(value=grid_settings.get('ticks_bottom', True))
    tk.Checkbutton(grid_window, text="Bottom (X)", variable=ticks_bottom_var).grid(row=5, column=1, padx=5, sticky="w")
    
    ticks_right_var = tk.BooleanVar(value=grid_settings.get('ticks_right', True))
    tk.Checkbutton(grid_window, text="Right (Secondary Y)", variable=ticks_right_var).grid(row=6, column=1, padx=5, sticky="w")


    # "Use Subplot 1 for all" checkbox (created once, shown only when Subplot 1 selected)
    use_for_all_var = tk.BooleanVar(value=grid_settings.get('use_subplot1_for_all', False))
    use_for_all_chk = tk.Checkbutton(grid_window, text="Use Subplot 1 for all", variable=use_for_all_var)

    # Buttons: Reset + Apply
    tk.Button(grid_window, text="Reset", command=reset_grid_defaults).grid(row=8, column=0, padx=5, pady=10)
    tk.Button(grid_window, text="Apply", command=apply_grid_settings).grid(row=8, column=1, columnspan=2, pady=10)

    # initialize fields according to current selection
    update_fields_grid()

    
def set_marker():
    def update_fields():
        marker_type = marker_type_var.get()
        selected_subplot = subplot_select_var.get()
    
        # Hide all fields first
        x_entry.grid_remove()
        y_entry.grid_remove()
        plot_select_menu.grid_remove()
        source_type_menu.grid_remove()
    
        # Show fields based on marker type
        if marker_type in ["vertical", "xpoint"]:
            x_entry.grid(row=2, column=1)
        if marker_type in ["horizontal", "ypoint"]:
            y_entry.grid(row=3, column=1)
        if marker_type == "point":
            x_entry.grid(row=2, column=1)
            y_entry.grid(row=3, column=1)
    
        # Update plot selection for xpoint/ypoint
        if marker_type in ["xpoint", "ypoint"]:
            # Filter plots for selected subplot
            subplot_plots = [f"{i}: {os.path.basename(e['file_path'])}" 
                           for i, e in enumerate(entries) 
                           if str(e.get('subplot', '1')) == selected_subplot]
            
            menu = plot_select_menu["menu"]
            menu.delete(0, "end")
            for plot in subplot_plots:
                menu.add_command(label=plot, 
                               command=lambda p=plot: plot_select_var.set(p))
            
            if subplot_plots:
                plot_select_var.set(subplot_plots[0])
                plot_select_menu.grid(row=1, column=2)
                source_type_menu.grid(row=2, column=2)
            else:
                plot_select_var.set("No plots in subplot")

    marker_window = tk.Toplevel(root)
    marker_window.title("Marker Settings")

    # Get available subplots from current layout
    rows, cols = map(int, subplot_settings['layout'].split('x'))
    subplot_options = [str(i) for i in range(1, rows * cols + 1)]

    # Subplot selection
    tk.Label(marker_window, text="Target Subplot:").grid(row=0, column=0, sticky="w")
    subplot_select_var = tk.StringVar(value="1")
    subplot_select_menu = tk.OptionMenu(marker_window, subplot_select_var, 
                                      *subplot_options,
                                      command=lambda _: update_fields())
    subplot_select_menu.grid(row=0, column=1)

    # Marker type selection
    tk.Label(marker_window, text="Marker Type:").grid(row=1, column=0, sticky="w")
    marker_type_var = tk.StringVar(value="vertical")
    marker_type_menu = tk.OptionMenu(marker_window, marker_type_var,
                                   "horizontal", "vertical", "point", "xpoint", "ypoint",
                                   command=lambda _: update_fields())
    marker_type_menu.grid(row=1, column=1)

    # Plot selection (will be populated based on subplot)
    plot_select_var = tk.StringVar(value='')
    plot_select_menu = tk.OptionMenu(marker_window, plot_select_var, '')
    plot_select_menu.grid(row=1, column=2)
    plot_select_menu.grid_remove()

    # Y-axis type selection
    source_type_var = tk.StringVar(value="primary")
    source_type_menu = tk.OptionMenu(marker_window, source_type_var, 
                                   "primary", "secondary")
    source_type_menu.grid(row=2, column=2)
    source_type_menu.grid_remove()

    # Coordinate fields
    tk.Label(marker_window, text="X:").grid(row=2, column=0, sticky="w")
    x_entry = tk.Entry(marker_window)
    x_entry.grid(row=2, column=1)

    tk.Label(marker_window, text="Y:").grid(row=3, column=0, sticky="w")
    y_entry = tk.Entry(marker_window)
    y_entry.grid(row=3, column=1)

    # Color selection
    tk.Label(marker_window, text="Color:").grid(row=4, column=0, sticky="w")
    color_display = tk.Label(marker_window, bg="#000000", width=10)
    color_display.grid(row=4, column=1)
    tk.Button(marker_window, text="Choose Color", 
             command=lambda: color_display.config(
                 bg=colorchooser.askcolor(title="Choose Marker Color", 
                                        parent=marker_window)[1] or color_display.cget("bg")
             )).grid(row=4, column=2)

    
    def edit_selected_marker(event):
        selection = marker_list.curselection()
        if selection:
            index = selection[0]
            marker = markers[index]

            # set marker type and update visible fields
            marker_type_var.set(marker.get('type', 'vertical'))
            update_fields()

            # populate X field
            if marker.get('x') is not None:
                x_entry.delete(0, tk.END)
                x_entry.insert(0, f"{marker['x']}")
            else:
                x_entry.delete(0, tk.END)

            # populate Y field
            if marker.get('y') is not None:
                y_entry.delete(0, tk.END)
                y_entry.insert(0, f"{marker['y']}")
            else:
                y_entry.delete(0, tk.END)

            # color
            color_display.config(bg=marker.get('color', '#000000'))

            # set subplot and source (y-axis) selections if present
            try:
                subplot_select_var.set(str(marker.get('subplot', 1)))
            except Exception:
                pass
            try:
                source_type_var.set(marker.get('y-axis', 'primary'))
            except Exception:
                pass

            # remember index for overwrite on save
            marker_window.selected_index = index
            status_label.config(text=f"Bearbeite Eintrag #{index + 1}")
    
    def add_marker():
        marker_type = marker_type_var.get()
        subplot_num = int(subplot_select_var.get())
        axis = source_type_var.get()
        color = color_display.cget("bg")

        try:
            if marker_type in ["xpoint", "ypoint"]:
                if not plot_select_var.get() or plot_select_var.get() == "No plots in subplot":
                    messagebox.showerror("Error", "Please select a plot first.")
                    return
                    
                plot_index = int(plot_select_var.get().split(":")[0])
                selected_entry = entries[plot_index]
                
                if str(selected_entry.get('subplot', '1')) != str(subplot_num):
                    messagebox.showerror("Error", "Selected plot is not in the chosen subplot.")
                    return
                    
                df = pd.read_csv(selected_entry['file_path'])
                
                if marker_type == "xpoint":
                    x = float(x_entry.get())
                    y = df.iloc[(df.iloc[:, 0] - x).abs().idxmin(), 1]
                else:  # ypoint
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
                'y-axis': axis,
                'subplot': subplot_num,
                'source_plot': plot_select_var.get() if marker_type in ["xpoint", "ypoint"] else None
            }

            if hasattr(marker_window, 'selected_index'):
                markers[marker_window.selected_index] = new_marker
                del marker_window.selected_index
            else:
                markers.append(new_marker)

            update_marker_list()
            status_label.config(text="Kein Eintrag ausgewählt")
            reload_plot()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add marker: {str(e)}")

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
            desc += f" (subplot {m['subplot']})"
            marker_list.insert(tk.END, desc)

    # Marker list
    tk.Label(marker_window, text="Current Markers:").grid(row=6, column=0, columnspan=2, sticky="w")
    marker_list = tk.Listbox(marker_window, width=50, height=10)
    marker_list.grid(row=7, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
    marker_list.bind("<Double-Button-1>", edit_selected_marker)

    
    # Initiales Laden der Marker-Liste
    update_marker_list()


    # Buttons
    tk.Button(marker_window, text="Add Marker", command=add_marker).grid(row=8, column=0, pady=10)
    tk.Button(marker_window, text="Delete Selected", 
             command=lambda: delete_selected_marker(marker_list)).grid(row=8, column=1)

    status_label = tk.Label(marker_window, text="Kein Eintrag ausgewählt", fg="blue")
    status_label.grid(row=9, column=0, columnspan=3, sticky="w", pady=(5, 0))
    
    def delete_selected_marker(listbox):
        selection = listbox.curselection()
        if not selection:
            messagebox.showwarning("No selection", "Please select a marker to delete.")
            return
        index = selection[0]
        del markers[index]
        update_marker_list()
        status_label.config(text="Kein Eintrag ausgewählt")
        reload_plot()

    # Initialize UI
    update_fields()

def open_zoom_settings():
    global zoom_regions
    global subplot_settings
    def apply_zoom():
        try:
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
            subplot_num = int(subplot_var.get())
            y_axis_choice = y_axis_var.get()

            new_region = {
                'x': (x_min, x_max),
                'y': (y_min, y_max),
                'width': width if width else "30%",
                'height': height if height else "30%",
                'loc': loc if loc else "upper right",
                'show_grid': show_grid if show_grid else False,
                'ticks': plot_ticks if plot_ticks else False,
                'border_pad': borderpad if borderpad else 1.5,
                'subplot': subplot_num,
                'y_axis': y_axis_choice
            }

            # Wenn ein Index gespeichert ist, ersetze den Eintrag
            try:
                if hasattr(zoom_window, 'selected_index'):
                    zoom_regions[zoom_window.selected_index] = new_region
                    del zoom_window.selected_index
                else:
                    zoom_regions.append(new_region)
            except Exception:
                print("index out of range")
            update_listbox()
            status_label.config(text="Kein Eintrag ausgewählt")
            reload_plot()
        except ValueError:
            messagebox.showerror("Fehler", "Bitte gültige numerische Werte eingeben.", parent=zoom_window)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Anwenden des Zooms:\n{e}", parent=zoom_window)

    def update_listbox():
        zoom_listbox.delete(0, tk.END)
        for i, region in enumerate(zoom_regions):
            zoom_listbox.insert(tk.END, f"{i+1}: subplot={region.get('subplot',1)}, y-axis={region.get('y_axis','primary')}, x={region['x']}, y={region['y']}, grid={region.get('show_grid','')}, ticks={region.get('ticks','')}, size=({region.get('width','')}, {region.get('height','')}), loc={region.get('loc','')}, space={region.get('border_pad', '')}")

    def delete_selected_region():
        selection = zoom_listbox.curselection()
        if not selection:
            messagebox.showwarning("No selection", "Please select a zoom region to delete.")
            return
        index = selection[0]
        del zoom_regions[index]
        update_listbox()
        status_label.config(text="Kein Eintrag ausgewählt")
        reload_plot()

    def edit_selected_region(event):
        selection = zoom_listbox.curselection()
        if selection:
            index = selection[0]
            region = zoom_regions[index]
            subplot_var.set(str(region.get('subplot', 1)))
            # update y-axis menu according to selected subplot
            update_yaxis_menu()
            y_axis_var.set(region.get('y_axis', 'primary'))

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

    # Get available subplots
    rows, cols = map(int, subplot_settings['layout'].split('x'))
    subplot_options = [str(i) for i in range(1, rows * cols + 1)]

    # Subplot selection
    tk.Label(zoom_window, text="Target Subplot:").grid(row=0, column=0, sticky="w")
    subplot_var = tk.StringVar(value="1")
    subplot_menu = tk.OptionMenu(zoom_window, subplot_var, *subplot_options, command=lambda _: update_yaxis_menu())
    subplot_menu.grid(row=0, column=1)

    # Y-axis selection (will be adapted dynamically)
    tk.Label(zoom_window, text="Y-Axis:").grid(row=0, column=2, sticky="w")
    y_axis_var = tk.StringVar(value="primary")
    # replaced OptionMenu by readonly Combobox for reliable dynamic updates
    y_axis_combo = ttk.Combobox(zoom_window, textvariable=y_axis_var, state="readonly", values=["primary"])
    y_axis_combo.grid(row=0, column=3)

    def update_yaxis_menu():
        # determine selected subplot
        try:
            sel = int(subplot_var.get())
        except Exception:
            sel = 1

        # check entries list: if any entry belongs to this subplot and uses secondary axis -> allow "secondary"
        has_secondary = any(int(e.get('subplot', 1)) == sel and e.get('y_axis', 'primary') == 'secondary' for e in entries)

        vals = ["primary"]
        if has_secondary:
            vals.append("secondary")

        # update combobox options and ensure a valid selection
        y_axis_combo['values'] = vals
        if y_axis_var.get() not in vals:
            y_axis_var.set(vals[0])

    # coordinate inputs
    tk.Label(zoom_window, text="Zoom X Min:").grid(row=1, column=0, sticky="w")
    x_min_entry = tk.Entry(zoom_window)
    x_min_entry.insert(0, str(zoom_x[0]))
    x_min_entry.grid(row=1, column=1)

    tk.Label(zoom_window, text="Zoom X Max:").grid(row=1, column=2, sticky="w")
    x_max_entry = tk.Entry(zoom_window)
    x_max_entry.insert(0, str(zoom_x[1]))
    x_max_entry.grid(row=1, column=3)

    tk.Label(zoom_window, text="Zoom Y Min:").grid(row=2, column=0, sticky="w")
    y_min_entry = tk.Entry(zoom_window)
    y_min_entry.insert(0, str(zoom_y[0]))
    y_min_entry.grid(row=2, column=1)

    tk.Label(zoom_window, text="Zoom Y Max:").grid(row=2, column=2, sticky="w")
    y_max_entry = tk.Entry(zoom_window)
    y_max_entry.insert(0, str(zoom_y[1]))
    y_max_entry.grid(row=2, column=3)

    # Grid
    tk.Label(zoom_window, text="Show Grid in Zoom:").grid(row=3, column=0, sticky="w")
    zoom_grid_var = tk.BooleanVar(value=True)
    tk.Checkbutton(zoom_window, variable=zoom_grid_var).grid(row=3, column=1)

    # Ticks
    tk.Label(zoom_window, text="Show Ticks in Zoom:").grid(row=3, column=2, sticky="w")
    plot_ticks_var = tk.BooleanVar(value=True)
    tk.Checkbutton(zoom_window, variable=plot_ticks_var).grid(row=3, column=3)

    # Size and Position
    tk.Label(zoom_window, text="Inset Width (%):").grid(row=4, column=0, sticky="w")
    width_entry = tk.Entry(zoom_window)
    width_entry.insert(0, "30%")
    width_entry.grid(row=4, column=1)

    tk.Label(zoom_window, text="Inset Height (%):").grid(row=4, column=2, sticky="w")
    height_entry = tk.Entry(zoom_window)
    height_entry.insert(0, "30%")
    height_entry.grid(row=4, column=3)

    tk.Label(zoom_window, text="Inset Position:").grid(row=5, column=0, sticky="w")
    loc_entry = tk.StringVar(value="upper right")
    loc_options = ["upper right", "upper left", "lower right", "lower left", "center", "right", "center right", "center left", "lower center", "upper center"]
    loc_menu = tk.OptionMenu(zoom_window, loc_entry, *loc_options)
    loc_menu.grid(row=5, column=1)

    tk.Label(zoom_window, text="Distance to plot edge:").grid(row=5, column=2, sticky="w")
    space_entry = tk.Entry(zoom_window)
    space_entry.insert(0, 1.5)
    space_entry.grid(row=5, column=3)

    tk.Button(zoom_window, text="Apply Zoom", command=apply_zoom).grid(row=6, column=0, columnspan=2, pady=10)
    tk.Button(zoom_window, text="Delete Selected", command=delete_selected_region).grid(row=6, column=2, columnspan=2, pady=10)

    tk.Label(zoom_window, text="Zoom Regions:").grid(row=7, column=0, columnspan=4, sticky="w")
    zoom_listbox = tk.Listbox(zoom_window, width=120)
    zoom_listbox.grid(row=8, column=0, columnspan=4, sticky="w")
    zoom_listbox.bind("<Double-Button-1>", edit_selected_region)

    status_label = tk.Label(zoom_window, text="Kein Eintrag ausgewählt", fg="blue")
    status_label.grid(row=9, column=0, columnspan=4, sticky="w", pady=(5, 0))

    # initialize y-axis menu according to current subplot selection
    update_yaxis_menu()
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
            'visible': visible_var.get(),
            'all_in_subplot1': all_in_subplot1_var.get(),
            'show_markers': show_markers_var.get()
        }
        reload_plot()

    legend_window = tk.Toplevel(root)
    legend_window.title("Legend-Settings")

    # Schriftgröße
    tk.Label(legend_window, text="Font Size:").grid(row=0, column=0, sticky="w")
    fontsize_entry = tk.Entry(legend_window)
    fontsize_entry.insert(0, legend_settings.get('fontsize'))
    fontsize_entry.grid(row=0, column=1)

    # Position
    tk.Label(legend_window, text="Position:").grid(row=1, column=0, sticky="w")
    loc_var = tk.StringVar(value=legend_settings.get('loc'))
    loc_menu = tk.OptionMenu(legend_window, loc_var, "best", "upper right", "upper left", 
                            "lower right", "lower left", "center", "center right", 
                            "center left", "lower center", "upper center")
    loc_menu.grid(row=1, column=1)

    # Rahmen
    tk.Label(legend_window, text="Show Frame:").grid(row=2, column=0, sticky="w")
    frame_var = tk.BooleanVar(value=legend_settings.get('frameon'))
    tk.Checkbutton(legend_window, variable=frame_var).grid(row=2, column=1)

    # Transparenz
    tk.Label(legend_window, text="Transparency (0-1):").grid(row=3, column=0, sticky="w")
    alpha_scale = tk.Scale(legend_window, from_=0.0, to=1.0, resolution=0.1, orient="horizontal")
    alpha_scale.set(legend_settings.get('alpha'))
    alpha_scale.grid(row=3, column=1)

    # Spaltenanzahl
    tk.Label(legend_window, text="Columns:").grid(row=4, column=0, sticky="w")
    ncol_entry = tk.Entry(legend_window)
    ncol_entry.insert(0, legend_settings.get('ncol'))
    ncol_entry.grid(row=4, column=1)

    # Sichtbarkeit
    tk.Label(legend_window, text="Show Legend:").grid(row=5, column=0, sticky="w")
    visible_var = tk.BooleanVar(value=legend_settings.get('visible'))
    tk.Checkbutton(legend_window, variable=visible_var).grid(row=5, column=1)

    # Neue Option: Alle Legenden in Subplot 1
    all_in_subplot1_var = tk.BooleanVar(value=legend_settings.get('all_in_subplot1', False))
    tk.Checkbutton(legend_window, text="All in subplot 1", 
                   variable=all_in_subplot1_var).grid(row=6, column=0, columnspan=2, sticky="w")

    # Neue Option: Marker in Legende anzeigen
    show_markers_var = tk.BooleanVar(value=legend_settings.get('show_markers', True))
    tk.Checkbutton(legend_window, text="Show marker in legend", 
                   variable=show_markers_var).grid(row=7, column=0, columnspan=2, sticky="w")

    # Button
    tk.Button(legend_window, text="Apply", 
              command=apply_legend_settings).grid(row=8, column=0, columnspan=2, pady=10)

def open_axis_settings():
    axis_window = tk.Toplevel(root)
    axis_window.title("Axis-Settings")

    # Get available subplots from current layout
    rows, cols = map(int, subplot_settings['layout'].split('x'))
    subplot_options = [str(i) for i in range(1, rows * cols + 1)]

    # Subplot selection
    ttk.Label(axis_window, text="Target Subplot:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
    subplot_var = ttk.Combobox(axis_window, values=subplot_options, state="readonly")
    subplot_var.set("1")  # Default to first subplot
    subplot_var.grid(row=0, column=1, padx=5, pady=5)

    # Achsentyp Auswahl
    ttk.Label(axis_window, text="X-Axis:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
    x_axis_type = ttk.Combobox(axis_window, values=["linear", "log"], state="readonly")
    x_axis_type.set(axis_settings['subplots'][1].get('x_axis_type', 'linear'))
    x_axis_type.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(axis_window, text="Y-Axis:").grid(row=1, column=2, padx=5, pady=5, sticky="e")
    y_axis_type = ttk.Combobox(axis_window, values=["linear", "log"], state="readonly")
    x_axis_type.set(axis_settings['subplots'][1].get('y_axis_type', 'linear'))
    y_axis_type.grid(row=1, column=3, padx=5, pady=5)

    # Skalierung
    ttk.Label(axis_window, text="X-Min:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
    x_min_entry = ttk.Entry(axis_window)
    x_min_entry.grid(row=2, column=1, padx=5, pady=5)

    ttk.Label(axis_window, text="X-Max:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
    x_max_entry = ttk.Entry(axis_window)
    x_max_entry.grid(row=3, column=1, padx=5, pady=5)

    ttk.Label(axis_window, text="Y-Min:").grid(row=2, column=2, padx=5, pady=5, sticky="e")
    y_min_entry = ttk.Entry(axis_window)
    y_min_entry.grid(row=2, column=3, padx=5, pady=5)

    ttk.Label(axis_window, text="Y-Max:").grid(row=3, column=2, padx=5, pady=5, sticky="e")
    y_max_entry = ttk.Entry(axis_window)
    y_max_entry.grid(row=3, column=3, padx=5, pady=5)


    # Invertieren
    invert_x = tk.BooleanVar()
    invert_y = tk.BooleanVar()
    
    # Sekundäre Y-Achse Felder (werden dynamisch ergänzt)
    y2_axis_type_label = ttk.Label(axis_window, text="Y2-Axis:")
    y2_axis_type = ttk.Combobox(axis_window, values=["linear", "log"], state="readonly")
    y2_axis_type.set("linear")  # Standardwert setzen

    y2_min_label = ttk.Label(axis_window, text="Y2-Min:")
    y2_min_entry = ttk.Entry(axis_window)
    y2_max_label = ttk.Label(axis_window, text="Y2-Min:")
    y2_max_entry = ttk.Entry(axis_window)
    invert_y2_check = ttk.Checkbutton(axis_window, text="invert Y2-Axis")
    invert_y2 = tk.BooleanVar()

    ttk.Checkbutton(axis_window, text="invert X-Axis", variable=invert_x).grid(row=4, column=0, columnspan=2, padx=5)
    ttk.Checkbutton(axis_window, text="invert Y-Axis", variable=invert_y).grid(row=4, column=2, columnspan=2, padx=5)

    # Ticks automatisch
    auto_ticks = tk.BooleanVar(value=True)
    ttk.Checkbutton(axis_window, text="set ticks automatic", variable=auto_ticks).grid(row=5, column=0, columnspan=4, padx=5)

    def apply_settings():
        subplot_num = int(subplot_var.get())
        
        # Ensure axis_settings has a subplots dict
        if 'subplots' not in axis_settings:
            axis_settings['subplots'] = {}
        
        # Update or create settings for selected subplot
        axis_settings['subplots'][subplot_num] = {
            "x_axis_type": x_axis_type.get(),
            "y_axis_type": y_axis_type.get(),
            "y2_axis_type": y2_axis_type.get(),
            "x_min": x_min_entry.get(),
            "x_max": x_max_entry.get(),
            "y_min": y_min_entry.get(),
            "y_max": y_max_entry.get(),
            "y2_min": y2_min_entry.get(),
            "y2_max": y2_max_entry.get(),
            "invert_x": invert_x.get(),
            "invert_y": invert_y.get(),
            "invert_y2": invert_y2.get(),
            "auto_ticks": auto_ticks.get()
        }
        
        reload_plot()

    def update_fields(*args):
        print(f"Updating fields for subplot")
        # Load settings for selected subplot
        subplot_num = int(subplot_var.get())
        subplot_settings = axis_settings.get('subplots', {}).get(subplot_num, {})

        has_secondary_y_axis = False
        for e in entries:
            if int(e.get('subplot')) == int(subplot_num):
                if e.get('y_axis') == 'secondary':
                    has_secondary_y_axis = True
        
        print(f"Has secondary Y axis: {has_secondary_y_axis}")

        x_axis_type.set(subplot_settings.get('x_axis_type', 'linear'))
        y_axis_type.set(subplot_settings.get('y_axis_type', 'linear'))
        x_min_entry.delete(0, tk.END)
        x_min_entry.insert(0, subplot_settings.get('x_min', ''))
        x_max_entry.delete(0, tk.END)
        x_max_entry.insert(0, subplot_settings.get('x_max', ''))
        y_min_entry.delete(0, tk.END)
        y_min_entry.insert(0, subplot_settings.get('y_min', ''))
        y_max_entry.delete(0, tk.END)
        y_max_entry.insert(0, subplot_settings.get('y_max', ''))
        invert_x.set(subplot_settings.get('invert_x', False))
        invert_y.set(subplot_settings.get('invert_y', False))
        auto_ticks.set(subplot_settings.get('auto_ticks', True))

        
        # Sekundäre Y-Achse anzeigen, wenn vorhanden
        if has_secondary_y_axis:
            print(f"ytype {subplot_settings.get('y2_axis_type')}")
            y2_axis_type_label.config(text="Y2-Axis:")
            y2_axis_type_label.grid(row=1, column=4, padx=5, pady=5, sticky="e")
            y2_axis_type.grid(row=1, column=5, padx=5, pady=5)
            y2_axis_type.delete(0, tk.END)
            y2_axis_type.insert(0, subplot_settings.get('y2_axis_type', 'linear'))

            y2_min_label.config(text="Y2-Min:")
            y2_min_label.grid(row=2, column=4, padx=5, pady=5, sticky="e")
            y2_min_entry.grid(row=2, column=5, padx=5, pady=5)
            y2_min_entry.delete(0, tk.END)
            y2_min_entry.insert(0, subplot_settings.get('y2_min', ''))

            y2_max_label.config(text="Y2-Max:")
            y2_max_label.grid(row=3, column=4, padx=5, pady=5, sticky="e")
            y2_max_entry.grid(row=3, column=5, padx=5, pady=5)
            y2_max_entry.delete(0, tk.END)
            y2_max_entry.insert(0, subplot_settings.get('y2_max', ''))

            invert_y2_check.config(text="invert Y2-Axis", variable=invert_y2)
            invert_y2_check.grid(row=4, column=4, columnspan=2, padx=5)
            invert_y2.set(subplot_settings.get('invert_y2', False))
        else:
            y2_axis_type_label.grid_remove()
            y2_axis_type.grid_remove()
            y2_min_label.grid_remove()
            y2_min_entry.grid_remove()
            y2_max_label.grid_remove()
            y2_max_entry.grid_remove()
            invert_y2_check.grid_remove()



    # Bind the update function to subplot selection
    subplot_var.bind('<<ComboboxSelected>>', update_fields)
    
    # Initial update of fields
    update_fields()

    ttk.Button(axis_window, text="Apply", command=apply_settings).grid(row=6, column=0, columnspan=4, pady=10)


def open_presets_manager():
    """
    Presets manager:
    - save current settings as preset (JSON in PRESETS_DIR)
    - load preset (apply to application state)
    - delete / import / export presets
    Stored keys in preset JSON:
     - subplot_settings
     - grid_settings
     - legend_settings
     - zoom_regions
     - markers
     - axis_settings
     - plot_title
     - save_settings
    """
    def list_presets():
        files = []
        try:
            for fn in os.listdir(PRESETS_DIR):
                if fn.lower().endswith(".json"):
                    files.append(fn)
        except Exception:
            pass
        return sorted(files)

    def refresh_list():
        preset_list.delete(0, tk.END)
        for fn in list_presets():
            preset_list.insert(tk.END, fn)

    def apply_preset_data(preset):
        # Apply preset dict to global state and UI
        global subplot_settings, grid_settings, legend_settings, zoom_regions, markers, axis_settings, save_settings
        try:
            if 'subplot_settings' in preset:
                # Convert string subplot keys to integers
                if 'subplots' in preset['subplot_settings']:
                    subplots = {}
                    for key, value in preset['subplot_settings']['subplots'].items():
                        # Convert string key to integer
                        try:
                            int_key = int(key)
                            subplots[int_key] = value
                        except ValueError:
                            continue
                    preset['subplot_settings']['subplots'] = subplots
                subplot_settings = preset['subplot_settings']
            if 'grid_settings' in preset:
                grid_settings = preset['grid_settings']
            if 'legend_settings' in preset:
                legend_settings = preset['legend_settings']
            if 'zoom_regions' in preset:
                zoom_regions.clear()
                zoom_regions.extend(preset.get('zoom_regions', []))
            if 'markers' in preset:
                markers.clear()
                markers.extend(preset.get('markers', []))
            if 'axis_settings' in preset:
                subplots = {}
                if 'subplots' in preset['axis_settings']:
                    for key, value in preset['axis_settings']['subplots'].items():
                        try:
                            int_key = int(key)
                            subplots[int_key] = value
                        except ValueError:
                            continue
                    preset['axis_settings']['subplots'] = subplots
                axis_settings = preset['axis_settings']
            if 'plot_title' in preset and title_entry is not None:
                try:
                    title_entry.delete(0, tk.END)
                    title_entry.insert(0, preset.get('plot_title', ''))
                except Exception:
                    pass
            if 'save_settings' in preset:
                save_settings.update(preset.get('save_settings', {}))
        except Exception as e:
            messagebox.showerror("Preset Fehler", f"Fehler beim Anwenden des Presets:\n{e}", parent=preset_win)
            return
        reload_plot()
        messagebox.showinfo("Preset geladen", "Preset erfolgreich angewendet.", parent=preset_win)

        print(f"subplot-settings: {subplot_settings}")

    def save_current_preset():
        name = simpledialog.askstring("Preset Name", "Name für das Preset:", parent=preset_win)
        if not name:
            return
        filename = f"{name}.json"
        path = os.path.join(PRESETS_DIR, filename)
        preset = {
            "subplot_settings": subplot_settings,
            "grid_settings": grid_settings,
            "legend_settings": legend_settings,
            "zoom_regions": zoom_regions,
            "markers": markers,
            "axis_settings": axis_settings,
            "plot_title": title_entry.get() if title_entry else "",
            "save_settings": save_settings
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(preset, f, indent=2, ensure_ascii=False)
            refresh_list()
            messagebox.showinfo("Gespeichert", f"Preset gespeichert: {filename}", parent=preset_win)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Speichern des Presets:\n{e}", parent=preset_win)

    def load_selected_preset():
        sel = preset_list.curselection()
        if not sel:
            messagebox.showwarning("Auswahl", "Bitte ein Preset auswählen.", parent=preset_win)
            return
        filename = preset_list.get(sel[0])
        path = os.path.join(PRESETS_DIR, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                preset = json.load(f)
            apply_preset_data(preset)
        except Exception as e:
            messagebox.showerror("Fehler", f"Fehler beim Laden des Presets:\n{e}", parent=preset_win)

    def delete_selected_preset():
        sel = preset_list.curselection()
        if not sel:
            messagebox.showwarning("Auswahl", "Bitte ein Preset auswählen.", parent=preset_win)
            return
        filename = preset_list.get(sel[0])
        path = os.path.join(PRESETS_DIR, filename)
        if messagebox.askyesno("Löschen bestätigen", f"Möchtest du '{filename}' löschen?", parent=preset_win):
            try:
                os.remove(path)
            except Exception as e:
                messagebox.showerror("Fehler", f"Fehler beim Löschen:\n{e}", parent=preset_win)
            refresh_list()

    def import_preset():
        fp = filedialog.askopenfilename(parent=preset_win, filetypes=[("JSON files", "*.json")])
        if not fp:
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                preset = json.load(f)
            # ask for name under presets dir
            name = simpledialog.askstring("Importieren als", "Name für das Preset:", parent=preset_win)
            if not name:
                return
            out = os.path.join(PRESETS_DIR, f"{name}.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(preset, f, indent=2, ensure_ascii=False)
            refresh_list()
            messagebox.showinfo("Importiert", f"Preset importiert als {name}.json", parent=preset_win)
        except Exception as e:
            messagebox.showerror("Fehler", f"Import fehlgeschlagen:\n{e}", parent=preset_win)

    def export_selected_preset():
        sel = preset_list.curselection()
        if not sel:
            messagebox.showwarning("Auswahl", "Bitte ein Preset auswählen.", parent=preset_win)
            return
        filename = preset_list.get(sel[0])
        src = os.path.join(PRESETS_DIR, filename)
        dest = filedialog.asksaveasfilename(parent=preset_win, defaultextension=".json", initialfile=filename, filetypes=[("JSON files", "*.json")])
        if not dest:
            return
        try:
            with open(src, "r", encoding="utf-8") as fsrc, open(dest, "w", encoding="utf-8") as fdst:
                fdst.write(fsrc.read())
            messagebox.showinfo("Exportiert", f"Preset exportiert nach:\n{dest}", parent=preset_win)
        except Exception as e:
            messagebox.showerror("Fehler", f"Export fehlgeschlagen:\n{e}", parent=preset_win)

    preset_win = tk.Toplevel(root)
    preset_win.title("Presets Manager")
    preset_win.geometry("520x340")

    preset_list = tk.Listbox(preset_win, width=60, height=12)
    preset_list.grid(row=0, column=0, columnspan=4, padx=8, pady=8, sticky="nsew")

    tk.Button(preset_win, text="Save Current as Preset", command=save_current_preset).grid(row=1, column=0, padx=5, pady=5, sticky="we")
    tk.Button(preset_win, text="Load Selected", command=load_selected_preset).grid(row=1, column=1, padx=5, pady=5, sticky="we")
    tk.Button(preset_win, text="Delete Selected", command=delete_selected_preset).grid(row=1, column=2, padx=5, pady=5, sticky="we")
    tk.Button(preset_win, text="Import Preset...", command=import_preset).grid(row=2, column=0, padx=5, pady=5, sticky="we")
    tk.Button(preset_win, text="Export Selected...", command=export_selected_preset).grid(row=2, column=1, padx=5, pady=5, sticky="we")
    tk.Button(preset_win, text="Close", command=preset_win.destroy).grid(row=2, column=3, padx=5, pady=5, sticky="we")

    refresh_list()

root = tk.Tk()
root.title("CSV Plotter")

preset_button = None
# Root window layout
tk.Label(root, text="Plot Title:").grid(row=0, column=0)
title_entry = tk.Entry(root)
title_entry.insert(0, "Output Noise Plot")
title_entry.grid(row=0, column=1)


# New Presets button (disabled initially; enabled by plot_manager)
presets_button = tk.Button(root, text="Presets", command=open_presets_manager, state=tk.NORMAL, padx=width_pad_root)
presets_button.grid(row=1, column=1)

tk.Button(root, text="Plot Manager", command=plot_manager, padx=width_pad_root).grid(row=2, column=0)
reload_button = tk.Button(root, text="Reload Plot", command=reload_plot, state=tk.DISABLED, padx=width_pad_root)
reload_button.grid(row=2, column=1)

save_button = tk.Button(root, text="Save Plot", command=save_plot, state=tk.DISABLED, padx=width_pad_root)
save_button.grid(row=2, column=2)

grid_button = tk.Button(root, text="Grid Settings", command=open_grid_settings, state=tk.DISABLED, padx=width_pad_root)
grid_button.grid(row=3, column=0)

legend_button = tk.Button(root, text="Legend Settings", command=open_legend_settings, state=tk.DISABLED, padx=width_pad_root)
legend_button.grid(row=3, column=1)

zoom_button = tk.Button(root, text="Zoom Settings", command=open_zoom_settings, state=tk.DISABLED, padx=width_pad_root)
zoom_button.grid(row=3, column=2)

marker_button = tk.Button(root, text="Set Marker", command=set_marker, state=tk.DISABLED, padx=width_pad_root)
marker_button.grid(row=4, column=0)

axis_button = tk.Button(root, text="Axis", command=open_axis_settings, state=tk.DISABLED, padx=width_pad_root)
axis_button.grid(row=4, column=1)

# Button zum Layout Manager im Hauptfenster hinzufügen:
subplot_button = tk.Button(root, text="Layout Settings", command=open_subplot_settings, state=tk.DISABLED, padx=width_pad_root)
subplot_button.grid(row=4, column=2)

plot_label = tk.Label(root, text="Plot").grid(row=5, column=0, columnspan=3)



fig, ax = plt.subplots(figsize=(6, 4))
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().grid(row=12, column=0, columnspan=3)

root.mainloop()