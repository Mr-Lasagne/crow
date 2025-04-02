"""The CROW1 pairwise script.

This module is part of the CROW1 clerical review application, a
Tkinter-based tool for comparing linked data. It provides a graphical
interface for the user to navigate through the linked data and make
clerical decisions. It also provides functionality for saving and
loading matches from a CSV file. The script uses a configuration file
to determine the behaviour of the application, including the names of
the linked data files and the order in which they should be displayed.

Configuration:
    The application is configured via the `crow1_pairwise_config.ini`
    file. This configuration file should be located in the same
    directory as this script and contains settings that determine the
    behaviour of the review interface.

Usage:
    Run the application using the `python crow1_pairwise.py` command.

Repository:
    If there are any issues with the application, please open an issue
    on GitHub: https://github.com/Mr-Lasagne/crow
"""

import configparser
import getpass
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd


class IntroWindow:
    """Prompt the user to choose a file to review."""

    def __init__(self, root: tk.Tk, initial_directory: str) -> None:
        """Initialse the IntroWindow class."""
        self.root = root
        self.initial_directory = initial_directory

        self.root.geometry("300x170")
        self.root.title("CROW")

        self.intro_text = ttk.Label(
            self.root,
            text=(
                "Welcome to the Clerical Matching Application.\n"
                'Please click "Choose File" to select your file\n'
                "and begin matching."
            ),
            font="Helvetica 10",
        )
        self.intro_text.pack(pady=25)

        self.choose_file_button = ttk.Button(
            self.root, text="Choose File", command=self.open_file_dialog
        )
        self.choose_file_button.pack(ipadx=30, pady=10)

    def open_file_dialog(self) -> None:
        """Open a file dialog and close the window after selection."""
        self.fileselect = filedialog.askopenfilename(
            initialdir=self.initial_directory,
            filetypes=[("CSV Files", "*.csv")],
        )
        self.root.destroy()


class ClericalApp:
    """Open a window that allows users to clerically review records."""

    def __init__(self, root, working_file, filename_done, filename_old, config) -> None:
        # Create a title.
        root.title("Clerical Matching")

        # Create the separate frames:
        # 1 - Tool frame.
        self.toolFrame = ttk.LabelFrame(root, text="Tools:")
        self.toolFrame.grid(
            row=0, column=0, columnspan=1, sticky="ew", padx=10, pady=10
        )

        # 2 - Record frame.
        self.record_frame = ttk.LabelFrame(root, text="Current Record")
        self.record_frame.grid(row=2, column=0, columnspan=1, padx=10, pady=3)

        # 3 - Button frame.
        self.button_frame = ttk.LabelFrame(root)
        self.button_frame.grid(row=3, column=0, columnspan=1, padx=10, pady=3)

        # Initalise the file name variables.
        self.filename_done = filename_done
        self.filename_old = filename_old

        # Create a protocol for if a user presses the 'X' (top right).
        root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Create a match column if one doesn't exist and replace any
        # missing values (NA) with blank spaces.
        if {"Match"}.issubset(working_file.columns):
            # Convert all columns apart, from Match and Comments (if
            # specified), to string.
            for col_header in working_file.columns:
                if col_header in ("Match", "Comments"):
                    pass
                else:
                    # Convert to string.
                    working_file[col_header] = working_file[col_header].astype(str)
                    # Remove nan values.
                    for i in range(len(working_file)):
                        if working_file[col_header][i] == "nan":
                            working_file.at[i, col_header] = ""

            working_file.fillna("", inplace=True)

            # Variable indicates whether user has returned to this file
            # or not.
            self.matching_previously_began = 1
        else:
            working_file["Match"] = ""
            # Create the comment box column if column header is
            # specified.
            if int(config["custom_settings"]["commentbox"]):
                working_file["Comments"] = ""

            # Convert all columns, apart from Match and Comments (if
            # specified), to string.
            for col_header in working_file.columns:
                if col_header in ("Match", "Comments"):
                    pass
                else:
                    # Convert to string.
                    working_file[col_header] = working_file[col_header].astype(str)
                    # Remove nan values.
                    for i in range(len(working_file)):
                        if working_file[col_header][i] == "nan":
                            working_file.at[i, col_header] = ""

            working_file.fillna("", inplace=True)

            self.matching_previously_began = 0

        # Count how many records are in the clerical matching file.
        self.num_records = len(working_file)

        # A counter of the number of checkpoint saves.
        self.checkpointcounter = 0

        # Initiate the starting record_index so that it will go from
        # latest record counter variable for iterating through the
        # clerical matching file.
        self.record_index = self.get_starting_index()

        self.records_per_checkpoint = int(
            config["custom_settings"]["num_records_checkpoint"]
        )

        # Create the text size component.
        self.text_size = 10
        self.text_bold_boolean = 0
        self.text_bold = ""

        # Show or hide differences boolean.
        self.show_hide_diff = 0
        self.difference_col_label_names = {}

        # Create the record_index matches.
        self.counter_matches = ttk.Label(
            self.record_frame,
            text=f"{self.record_index + 1} / {self.num_records} Records",
            font="Helvetica 9",
        )
        self.counter_matches.grid(
            row=0,
            column=len(config.options("column_headers_and_order")),
            columnspan=1,
            padx=10,
            sticky="e",
        )

        # Create empty lists of labels.
        self.non_iterated_labels = []
        self.iterated_labels = []

        self.draw_button_frame()
        self.draw_record_frame()
        self.draw_tool_frame()

    def draw_record_frame(self) -> None:
        row_adder = 0
        separator_adder = 2

        self.counter_matches = ttk.Label(
            self.record_frame,
            text=f"{self.record_index + 1} / {self.num_records} Records",
            font="Helvetica 9",
        )
        self.counter_matches.grid(
            row=0,
            column=len(config.options("column_headers_and_order")),
            columnspan=1,
            padx=10,
            sticky="e",
        )

        for iterator, name_of_dataset in enumerate(config.options("dataset_names")):
            exec(
                f'self.{name_of_dataset} = ttk.Label(self.record_frame, text=config["dataset_names"]["{name_of_dataset}"]+":", font=f"Helvetica {self.text_size} bold")'
            )

            exec(
                f'self.{name_of_dataset}.grid(row=3+{row_adder}, column=0, columnspan=1, padx=10, pady=3, sticky="w")'
            )

            exec(
                f'self.separator{iterator} = ttk.Separator(self.record_frame, orient="horizontal")'
            )

            exec(
                f'self.separator{iterator}.grid(row={separator_adder}, column=0, columnspan=len(config.options("column_headers_and_order"))+2, sticky="ew")'
            )

            # Update row_adder and separator_adder variables.
            row_adder += 2
            separator_adder += 2

            # Add the executed self.labels to the non_iterated_labels
            # list.
            self.non_iterated_labels.append(name_of_dataset)

        # Create column header widgets.
        self.datasource_label = ttk.Label(
            self.record_frame,
            text="Datasource",
            font=f"Helvetica {self.text_size} bold",
        )
        self.datasource_label.grid(row=1, column=0, columnspan=1, padx=10, pady=3)

        # Create column header labels and place all them on row 1.
        for column_title in config.options("column_headers_and_order"):
            # Remove spaces from the user input and split them into
            # different components.
            col_header = (
                config["column_headers_and_order"][column_title]
                .replace(" ", "")
                .split(",")
            )

            exec(
                f'self.{column_title} = ttk.Label(self.record_frame, text="{col_header[0]}", font=f"Helvetica {self.text_size} bold")'
            )

            exec(
                f"self.{column_title}.grid(row=1, column=col_header[1], columnspan=1, sticky=tk.W, padx=10, pady=3)"
            )

            # Add the executed self.labels for the column headers to the
            # non_iterated_labels list.
            self.non_iterated_labels.append(column_title)

        # Create main labels that will contain all the data:
        # Step 1 - Work out which rows will contain each dataset.
        row_adder = 1
        dataset_row_num = []

        for i in range(len(config.options("dataset_names"))):
            row_adder += 2
            dataset_row_num.append(row_adder)

        # Step 2 - Create a list of the dataset names and differentiate
        # the first from the rest.
        name_of_datasets = [
            config["dataset_names"][dset] for dset in config.options("dataset_names")
        ]

        # Grab the dataset names that need to be highlighted if the
        # button is clicked.
        dataset_names_to_highlight = []
        # Collect the dataset names entered.
        for dataset_names in config.options("dataset_names"):
            dataset_names_to_highlight.append(config["dataset_names"][dataset_names])

        # Remove the first dataset as this is the highlighted one.
        dataset_names_to_highlight.pop(0)

        # Create some dictionary variables to hold the highlighter and
        # comparitor rows.
        self.datarow_to_compare = {}
        self.datarows_to_highlight = {}

        # Step 3 - Create each row label and position them in the
        # record_frame.
        i = 0

        for columnfile_title in config.options("columnfile_info_and_order"):
            # Remove spaces from the user input and split them into
            # different components.
            col_header = (
                config["columnfile_info_and_order"][columnfile_title]
                .replace(" ", "")
                .split(",")
            )

            # Create a text label.
            exec(
                f'self.{col_header[0]} = tk.Text(self.record_frame, height=1, relief="flat", bg="gray93")'
            )
            # Enter in the text from the df.
            exec(
                f'self.{col_header[0]}.insert("1.0", working_file["{col_header[0]}"][self.record_index])'
            )
            # Configure text so that it is a specified width, font and
            # cannot be interacted with.
            exec(
                f'self.{col_header[0]}.config(width=len(working_file["{col_header[0]}"][self.record_index])+10, font=f"Helvetica {self.text_size} {self.text_bold}", state=tk.DISABLED)'
            )

            # Cycle through each dataset name to know which row to put
            # the label on.
            for name in name_of_datasets:
                if col_header[1] == name:
                    # If col_header has matched: position it on the
                    # screen.
                    exec(
                        f'self.{col_header[0]}.grid(row=dataset_row_num[i], column=col_header[2], columnspan=1, padx=10, pady=3, sticky="w")'
                    )

                    # Check whether it is a dataset row to highlight or
                    # not.
                    if col_header[1] in dataset_names_to_highlight:
                        if col_header[2] in self.datarows_to_highlight:
                            self.datarows_to_highlight[col_header[2]].append(
                                col_header[0]
                            )

                        else:
                            self.datarows_to_highlight[col_header[2]] = [col_header[0]]

                    else:
                        self.datarow_to_compare[col_header[2]] = [col_header[0]]
                    # Break the for loop if name has been resolved.
                    break

                else:
                    # If col_header has not matched: move to the next
                    # row.
                    i += 1

            # Reset the iterator variable.
            i = 0

            self.iterated_labels.append(col_header[0])

        if not self.show_hide_diff:
            self.show_hide_diff = 1

            self.show_hide_differences()
        else:
            self.show_hide_diff = 0

            self.show_hide_differences()

    def draw_button_frame(self) -> None:
        # Match/Non-Match buttons.
        self.match_button = tk.Button(
            self.button_frame,
            text="Match",
            font=f"Helvetica {self.text_size}",
            command=lambda: self.update_index(1),
            bg="DarkSeaGreen1",
        )
        self.match_button.grid(row=0, column=0, columnspan=1, padx=15, pady=10)
        self.non_match_button = tk.Button(
            self.button_frame,
            text="Non-Match",
            font=f"Helvetica {self.text_size}",
            command=lambda: self.update_index(0),
            bg="light salmon",
        )
        self.non_match_button.grid(row=0, column=1, columnspan=1, padx=15, pady=10)

        # Add in the comment widget based on config option.
        if int(config["custom_settings"]["commentbox"]):
            # Create comments column if one does not exist.
            if "Comments" not in working_file:
                working_file["Comments"] = ""

            # Get the position info from button 1.
            info_button = self.match_button.grid_info()

            self.comment_label = ttk.Label(
                self.button_frame,
                text="Comment:",
                font=f"Helvetica {self.text_size} bold",
            )
            self.comment_label.grid(
                row=info_button["row"] + 1, column=0, columnspan=1, sticky="e"
            )

            self.comment_entry = ttk.Combobox(self.button_frame)
            self.comment_entry.grid(
                row=info_button["row"] + 1,
                column=1,
                columnspan=3,
                sticky="sew",
                padx=5,
                pady=5,
            )

            if (config["custom_settings"]["comment_values"]) is not None:
                self.comment_entry["values"] = (
                    config["custom_settings"]["comment_values"]
                ).split(",")

    def draw_tool_frame(self) -> None:
        # Create labels for tools bar.
        self.separator_tf_1 = ttk.Separator(self.toolFrame, orient="vertical")
        self.separator_tf_1.grid(
            row=0, column=3, rowspan=1, sticky="ns", padx=10, pady=5
        )
        self.separator_tf_2 = ttk.Separator(self.toolFrame, orient="vertical")
        self.separator_tf_2.grid(
            row=0, column=7, rowspan=1, sticky="ns", padx=10, pady=5
        )

        # Back button.
        back_symbol = "\u23ce"
        self.back_button = tk.Button(
            self.button_frame,
            text=f"Back {back_symbol}",
            font=f"Helvetica {self.text_size}",
            command=lambda: self.go_back(),
        )
        self.back_button.grid(row=0, column=2, columnspan=1, padx=15, pady=10)
        # Show hide differences.
        self.showhidediff = tk.Button(
            self.toolFrame,
            text="Show/Hide Differences",
            font=f"Helvetica {self.text_size}",
            command=lambda: self.show_hide_differences(),
        )
        self.showhidediff.grid(row=0, column=2, columnspan=1, padx=5, pady=5)
        # Change text size buttons.
        increase_text_size_symbol = "\U0001f5da"
        decrease_text_size_symbol = "\U0001f5db"

        self.text_smaller_button = tk.Button(
            self.toolFrame,
            text=f"{decrease_text_size_symbol}-",
            font=f"Helvetica {self.text_size + 3}",
            height=1,
            width=3,
            command=lambda: self.change_text_size(0),
        )
        self.text_smaller_button.grid(row=0, column=4, sticky="e", pady=5)
        self.text_bigger_button = tk.Button(
            self.toolFrame,
            text=f"{increase_text_size_symbol}+",
            height=1,
            width=3,
            font=f"Helvetica {self.text_size + 3}",
            command=lambda: self.change_text_size(1),
        )
        self.text_bigger_button.grid(row=0, column=5, sticky="w", pady=5, padx=2)
        # Make text bold button.
        bold_symbol = "\U0001d5d5"
        self.bold_button = tk.Button(
            self.toolFrame,
            text=f"{bold_symbol}",
            font=f"Helvetica {self.text_size + 3}",
            height=1,
            width=3,
            command=lambda: self.make_text_bold(),
        )
        self.bold_button.grid(row=0, column=6, sticky="w", pady=5)
        # Save and close button.
        save_symbol = "\U0001f4be"
        self.save_button = tk.Button(
            self.toolFrame,
            text=f"Save and Close {save_symbol}",
            font=f"Helvetica {self.text_size}",
            command=lambda: self.save_and_close(),
        )
        self.save_button.grid(row=0, column=8, columnspan=1, sticky="e", padx=5, pady=5)

    def show_hide_differences(self) -> None:
        if not self.show_hide_diff:
            # Make show show diff variable 1 so that next time this
            # function is called it will remove tags.
            self.show_hide_diff = 1
            # Create a dictionary variable of the columns with
            # differences and their label names.
            self.difference_col_label_names = {}

            # For key in data rows that need to be highlighted.
            for key in self.datarows_to_highlight:
                # For the values in data rows that need to be
                # highlighted.
                for vals in self.datarows_to_highlight[key]:
                    # Some empty variables to control the flow of the
                    # difference indicator.
                    char_consistent = []
                    container = []
                    string_start = 1
                    string_end = 0
                    count = 0

                    # For each character between the first row label and
                    # the rows underneath it.
                    for char_comparison, char_highlight in zip(
                        working_file[self.datarow_to_compare[key][0]][
                            self.record_index
                        ],
                        working_file[f"{vals}"][self.record_index],
                    ):
                        # If the comparison character is not the same as
                        # the highlighter character.
                        if char_comparison != char_highlight:
                            # If this is the first diff then remove
                            # them.
                            if string_start:
                                # Start the container values.
                                container.append(count)

                                string_start = 0

                            # If we are at the end of string comparison.
                            if count == min(
                                len(
                                    working_file[self.datarow_to_compare[key][0]][
                                        self.record_index
                                    ]
                                )
                                - 1,
                                len(working_file[f"{vals}"][self.record_index]) - 1,
                            ):
                                container.append(count + 1)
                                # Pass this start and end values to the
                                # overall container.
                                char_consistent.append(container)

                        else:
                            # If string end == string start.
                            if string_end == string_start:
                                # Add it to the container to complete
                                # the character number differences.
                                container.append(count)

                                # Restart this variable.
                                string_start = 1

                                # Pass this start and end values to the
                                # overall container.
                                char_consistent.append(container)

                                container = []
                        # Increase the count.
                        count += 1

                    # If length of the comparator is less highlighter
                    # make it yellow as well.
                    if len(
                        working_file[self.datarow_to_compare[key][0]][self.record_index]
                    ) < len(working_file[f"{vals}"][self.record_index]):
                        char_consistent.append(
                            [
                                len(
                                    working_file[self.datarow_to_compare[key][0]][
                                        self.record_index
                                    ]
                                ),
                                len(working_file[f"{vals}"][self.record_index]),
                            ]
                        )

                        count = 0

                    # For each tag number in char_consistent: create the
                    # tag and save the tag name information.
                    for tag_adder in range(len(char_consistent)):
                        if vals in self.difference_col_label_names:
                            self.difference_col_label_names[vals].append(
                                f"{vals}_diff{str(tag_adder)}"
                            )

                        else:
                            self.difference_col_label_names[vals] = [
                                f"{vals}_diff{str(tag_adder)}"
                            ]

                        exec(
                            f'self.{vals}.tag_add(f"{vals}_diff{str(tag_adder)}", f"1.{char_consistent[tag_adder][0]}", f"1.{char_consistent[tag_adder][-1]}")'
                        )

                        exec(
                            f'self.{vals}.tag_config(f"{vals}_diff{str(tag_adder)}", background="yellow", foreground="black")'
                        )

        else:
            # Reset this variable.
            self.show_hide_diff = 0
            # For all variable labels with differences - remove the tag
            # labels.
            for key in self.difference_col_label_names:
                for vals in self.difference_col_label_names[key]:
                    exec(f"self.{key}.tag_remove('{vals}', '1.0', 'end')")

    def make_text_bold(self) -> None:
        """Make the text bold or not bold."""
        if not self.text_bold_boolean:
            self.text_bold_boolean = 1
            self.text_bold = "bold"

        else:
            self.text_bold_boolean = 0
            self.text_bold = ""

        self.update_gui()

    def get_starting_index(self):
        """Get the first row index that has a value not equal to 0 or 1.

        Returns
        -------
        i : int
            Index number that relates to the next record to be matched.

        """
        # Get a list of index_values.
        index_values = list(range(0, len(working_file)))

        # Cycle through the working_file dataset to determine the next
        # avaliable record: Choose which one to cycle through.
        if int(config["custom_settings"]["commentbox"]):
            for i in index_values:
                if working_file.iloc[i, -2] != 1 and working_file.iloc[i, -2] != 0:
                    return i
                elif i == self.num_records - 1:
                    return i
                elif working_file.iloc[i, -2] == 1 or working_file.iloc[i, -2] == 0:
                    pass

        else:
            for i in index_values:
                if working_file.iloc[i, -1] != 1 and working_file.iloc[i, -1] != 0:
                    return i
                elif i == self.num_records - 1:
                    return i
                elif working_file.iloc[i, -1] == 1 or working_file.iloc[i, -1] == 0:
                    pass

    def update_gui(self) -> None:
        """Update the different GUI labels based on the records."""
        if self.check_matching_done() == 0:
            # Configure the non-iterable labels.
            for non_iter_columns in self.non_iterated_labels:
                exec(
                    f'self.{non_iter_columns}.config(font=f"Helvetica {self.text_size} bold")'
                )

            for widget in self.record_frame.winfo_children():
                widget.destroy()

            for widget in self.toolFrame.winfo_children():
                widget.destroy()

            for widget in self.button_frame.winfo_children():
                widget.destroy()
            self.draw_record_frame()
            self.draw_button_frame()
            self.draw_tool_frame()
            if not self.show_hide_diff:
                self.show_hide_diff = 1

                self.show_hide_differences()
            else:
                self.show_hide_diff = 0

                self.show_hide_differences()
            if self.record_index == 0:
                self.back_button.config(state=tk.DISABLED)
            else:
                self.back_button.config(state="normal")
        elif self.check_matching_done() == 1:
            messagebox.showinfo(
                "Matching Finished",
                "Matching Finished: Press save and close or use the\n"
                "back button to return to the previous record",
            )

    def update_df(self, match_res) -> None:
        """Update the DataFrame with the review outcome.

        1 == Match, 0 == Non-match

        Parameters
        ----------
        match_res : int - boolean.
            Adds a 1 or a 0 in the column.

        """
        # Update df.
        working_file.at[self.record_index, "Match"] = match_res

        if int(config["custom_settings"]["commentbox"]):
            working_file.at[self.record_index, "Comments"] = self.comment_entry.get()

    def save_at_checkpoint(self) -> None:
        """Save the data at an interval defined in the config file.

        This back up the data to that point.
        """
        # Check whether the record_index is a multiple of
        # records_per_checkpoint and record_index is less than total num
        # records.
        if (self.record_index % self.records_per_checkpoint == 0) & (
            self.record_index < self.num_records
        ):
            # Checkpoint it by saving it.
            working_file.to_csv(self.filename_old, index=False)
            # Increase checkpoint counter.
            self.checkpointcounter += 1

        # Check if record_index is a multiple of 5 and record_index ==
        # num records.
        elif (self.record_index % self.records_per_checkpoint == 0) & (
            self.record_index == self.num_records
        ):
            # Save it as DONE.
            os.rename(self.filename_old, self.filename_done)
            working_file.to_csv(self.filename_done, index=False)
            self.checkpointcounter += 1

        elif self.record_index % self.records_per_checkpoint != 0:
            pass

    def check_matching_done(self):
        """Check if the review process is finished.

        Returns
        -------
        Boolean value, this dictates whether to stop displaying any more
        records and close the app or continue updating the app:
        1 = Stop the GUI, 0 = Continue updating the GUI.

        """
        # Query whether the current record matches the total number of
        # records (end of the terminal).
        if self.record_index > (self.num_records - 1):
            # Disable the match and non-match buttons.
            self.match_button.configure(state=tk.DISABLED)
            self.non_match_button.configure(state=tk.DISABLED)
            # Present a message on the screen informing the user that
            # matching is finished.
            self.matchdone = ttk.Label(
                root, text="Matching Finished. Press save and close.", foreground="red"
            )
            self.matchdone.grid(row=1, column=0, columnspan=1)

            return 1
        else:
            return 0

    def save_and_close(self) -> None:
        """Save the working_file and close the GUI."""
        # Check whether matching has now finished (i.e. they have
        # completed all records).
        if self.record_index == (self.num_records):
            # If matching is now complete rename the file.
            if self.num_records % self.records_per_checkpoint != 0:
                os.rename(self.filename_old, self.filename_done)
                working_file.to_csv(self.filename_done, index=False)
            elif self.num_records % self.records_per_checkpoint == 0:
                working_file.to_csv(self.filename_done, index=False)

        else:
            # If not it yet finshed save it using the old file name.
            working_file.to_csv(self.filename_old, index=False)

        # Close down the app.
        root.destroy()

    def update_index(self, event) -> None:
        """Update the overall index which cycles through the file.

        Additional functonality is directing to other functions to
        update the clerical matching file and finally updating the GUI
        the next record to be clerically matched.

        Parameters
        ----------
        event : int - boolean
            This determines where to add a 1 or a 0 to the df.

        """
        # Update the Match column with the matchers choice.
        self.update_df(event)

        # Update the record_index.
        self.record_index += 1

        # Check if at checkpoint.
        self.save_at_checkpoint()

        stp_gui = self.check_matching_done()

        # Check if reached the end of the script.
        if stp_gui:
            pass
            # Could add in additional functionality here to do with
            # saving the working_file file.
        else:
            # Update the GUI labels.
            self.update_gui()

    def go_back(self) -> None:
        """Go back through records."""
        # If they have reached the end of matching.
        if self.record_index == len(working_file):
            # Take away the matching is finished message.
            self.matchdone.grid_forget()
            # Reactivate the buttons.
            self.match_button.configure(state="normal")
            self.non_match_button.configure(state="normal")
            # Update the record_index.
            self.record_index = self.record_index - 1
            # Update the overall GUI.
            self.update_gui()
            # Rename the file back to in progress.
            if len(working_file) % self.records_per_checkpoint == 0:
                os.rename(self.filename_done, self.filename_old)
        # If they are part way through matching.
        elif self.record_index > 0:
            # Update the record_index.
            self.record_index = self.record_index - 1
            # Update the GUI.
            self.update_gui()
        elif self.record_index == 0:
            pass

    def change_text_size(self, size_change) -> None:
        """Change the size of the text.

        Also change the size of the window to fit the text.

        Parameters
        ----------
        size_change : int - boolean
            Will change the text size based on argument passed.

        """
        # Depending on the argument passed - increase or decrease the
        # text size/geometry paramaters.
        if size_change:
            self.text_size += 1

        else:
            self.text_size -= 1
            # If commentbox specified in config.

        # Clear recordframe.
        self.update_gui()

    def on_exit(self) -> None:
        """Close the app after asking if they want to save or not."""
        # If they click yes.
        if messagebox.askyesno("Exit", "Are you sure you want to exit WITHOUT saving?"):
            # Check if this is the first time they are accessing it.
            if not self.matching_previously_began & self.checkpointcounter != 0:
                # Then rename the file removing their intial and
                # 'inProgress' tag.
                os.rename(
                    self.filename_old,
                    "_".join(self.filename_old.split("_")[0:-2]) + ".csv",
                )

            # Close down the application.
            root.destroy()


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read("crow1_pairwise_config.ini")

    initial_directory = config["matching_files_details"]["file_pathway"]

    user = getpass.getuser()

    root = tk.Tk()
    intro_window = IntroWindow(root, initial_directory)
    root.mainloop()

    # ------
    # Step 2:
    # ------

    # --- Create filepath variables, load in the selected data and
    # specify column variables.

    # Check if the user running it has selected this file before (this
    # means they have done some of the matching already and are coming
    # back to it).
    if "inProgress" in intro_window.fileselect.split("/")[-1]:
        # If it is the same user.
        if user in intro_window.fileselect.split("/")[-1]:
            # Do not rename the file.
            renamed_file = intro_window.fileselect

            # Create the filepath name for when the file is finished.
            filepath_done = f"{'/'.join(renamed_file.split('/')[:-1])}/{renamed_file.split('/')[-1][0:-15]}_DONE.{renamed_file.split('/')[-1].split('.')[-1]}"

        else:
            # Rename the file to contain the additional user.
            renamed_file = f"{'/'.join(intro_window.fileselect.split('/')[:-1])}/{intro_window.fileselect.split('/')[-1].split('.')[0][0:-11]}_{user}_inProgress.{intro_window.fileselect.split('/')[-1].split('.')[-1]}"
            os.rename(rf"{intro_window.fileselect}", rf"{renamed_file}")

            # Create the filepath name for when the file is finished.
            filepath_done = f"{'/'.join(renamed_file.split('/')[:-1])}/{renamed_file.split('/')[-1][0:-15]}_DONE.{renamed_file.split('/')[-1].split('.')[-1]}"

    # If a user is picking this file again and its done.

    elif "DONE" in intro_window.fileselect.split("/")[-1]:
        # If it is the same user.
        if user in intro_window.fileselect.split("/")[-1]:
            # Do not change filepath done - keep it as it is.
            filepath_done = intro_window.fileselect

            # Rename the file.
            renamed_file = f"{'/'.join(intro_window.fileselect.split('/')[:-1])}/{intro_window.fileselect.split('/')[-1][0:-9]}_inProgress.{intro_window.fileselect.split('/')[-1].split('.')[-1]}"
            os.rename(rf"{intro_window.fileselect}", rf"{renamed_file}")
        else:
            # If it is a different user: rename the file to include the
            # additional user.
            renamed_file = f"{'/'.join(intro_window.fileselect.split('/')[:-1])}/{intro_window.fileselect.split('/')[-1].split('.')[0][0:-5]}_{user}_inProgress.{intro_window.fileselect.split('/')[-1].split('.')[-1]}"
            os.rename(rf"{intro_window.fileselect}", rf"{renamed_file}")

            # Create the filepath done.
            filepath_done = f"{'/'.join(renamed_file.split('/')[:-1])}/{renamed_file.split('/')[-1][0:-15]}_DONE.{renamed_file.split('/')[-1].split('.')[-1]}"

    else:
        # Resave this file with the user ID at the end so no one else
        # selects it rename it with '_inProgress' and their entered
        # initials.
        renamed_file = f"{'/'.join(intro_window.fileselect.split('/')[:-1])}/{intro_window.fileselect.split('/')[-1].split('.')[0]}_{user}_inProgress.{intro_window.fileselect.split('/')[-1].split('.')[-1]}"
        os.rename(rf"{intro_window.fileselect}", rf"{renamed_file}")

        # Create the filepath name for when the file is finished.
        filepath_done = f"{'/'.join(renamed_file.split('/')[:-1])}/{renamed_file.split('/')[-1][0:-15]}_DONE.{renamed_file.split('/')[-1].split('.')[-1]}"

    # --- Load in the required csv file as a pandas dataframe (can also
    # do this for excel docs).
    working_file = pd.read_csv(renamed_file)

    # END OF STEP 2

    # ------
    # Step 3:
    # ------

    # --- Run the clerical matching application.
    root = tk.Tk()
    main_window = ClericalApp(root, working_file, filepath_done, renamed_file, config)
    root.mainloop()

    print(
        "\n Number of records matched:",
        str(len(working_file[working_file.Match != ""])),
    )
