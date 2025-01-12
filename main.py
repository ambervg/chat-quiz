from datetime import datetime

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import streamlit as st
import os
import re

# Utility Functions
def parse_chat(file_path):
    """ 
    Parses from the .txt file into a DataFrame.
    Identifies the sender, message and timestamp.
    """

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
        chat_lines = file.readlines()
    
    # Initialize variables
    parsed_lines = []
    current_sender = None

    for line in chat_lines[2:]:
        # Check if the line contains a sender using regex
        match = re.match(r'(\d{2}/\d{2}/\d{4}, \d{2}:\d{2}) - (.*?): (.*)', line)
        if match:
            # Extract sender and timestamp from line
            timestamp_str = match.group(1)
            date_format = "%d/%m/%Y, %H:%M"
            timestamp = datetime.strptime(timestamp_str, date_format)

            current_sender = match.group(2)
            parsed_lines.append({'sender': current_sender, 'timestamp':timestamp, 'message': match.group(3)})
        else:
            # Append the line to the last sender's message
            if parsed_lines and current_sender:
                parsed_lines[-1]['message'] += line

    # Convert to DataFrame
    df = pd.DataFrame(parsed_lines)
    return df


def get_message_counts_participant(chat_df):
    """ Takes in the full df and returns a smaller df with only 2 columns: sender & count """
    return chat_df['sender'].value_counts().reset_index()


def get_message_counts_timestamp(chat_df):
    """
    Takes in the full dataframe and returns three dataframes:
    1. Messages per date.
    2. Messages per hour.
    3. A pivot table for messages by participant and hour for heatmap visualization.
    """
    # Convert timestamp to date-only format
    chat_df['date'] = chat_df['timestamp'].dt.date
    messages_per_date = chat_df['date'].value_counts().reset_index()  #.rename(columns={'index': 'date', 'date': 'count'})

    # Extract the hour from the timestamp
    chat_df['hour'] = chat_df['timestamp'].dt.hour
    messages_per_hour = chat_df['hour'].value_counts().reset_index()  #.rename(columns={'index': 'hour', 'hour': 'count'})

    # Create a pivot table for the heatmap (hour vs participant)
    heatmap_data = chat_df.groupby(['sender', 'hour']).size().unstack(fill_value=0)

    return messages_per_date, messages_per_hour, heatmap_data


def plot_heatmap(heatmap_data):
    """
    Uses the heatmap_data provided by get_message_counts_timestamp() to plot a heatmap.
    Rows: participants
    Columns: Hours of the day
    """
    fig, ax = plt.subplots(figsize=(10, 6))
            
    normalized_heatmap_data = heatmap_data.div(heatmap_data.max(axis=1), axis=0).fillna(0)
    sns.heatmap(normalized_heatmap_data, annot=heatmap_data, fmt="d", cmap="YlGnBu", ax=ax, cbar_kws={'label': 'Relative Intensity'})
    
    ax.set_title("Messages Heatmap (Participants vs Hours)")
    ax.set_ylabel("Participant")
    ax.set_xlabel("Hour of the Day")

    st.write("What hours of the day are the participants most active?")
    st.pyplot(fig)


def plot_top3_early_birds(heatmap_data):
    """
    """
    early_bird_hours = heatmap_data.loc[:, 6:9,]
    early_bird_totals = early_bird_hours.sum(axis=1)
    top_3_early_birds = early_bird_totals.sort_values(ascending=False).head(3)

    st.subheader("Top 3 Early Birds")
    st.write("Participants who sent the most messages between 6 AM and 9 AM:")
    st.table(top_3_early_birds.reset_index())

def plot_top3_night_owls(heatmap_data):
    """
    """
    night_owl_hours = heatmap_data.loc[:, 0:5]  # Select columns for hours 0 (midnight) to 5 (5 AM)
    night_owl_totals = night_owl_hours.sum(axis=1)  # Sum across the selected hours
    top_3_night_owls = night_owl_totals.sort_values(ascending=False).head(3)  # Get top 3 participants

    st.subheader("Top 3 Night Owls")
    st.write("Participants who sent the most messages between midnight and 6 AM:")
    st.table(top_3_night_owls.reset_index())  # Display as a table

# def combine_participants(chat_df, selected_senders, new_name):
#     """ Combines the selected senders into a single new name in the chat_df """
#     chat_df['sender'] = chat_df['sender'].replace(selected_senders, new_name)
#     return chat_df


# UI Starts Here
st.title("Chat Analysis Tool")

# STEP 1: File Selection
st.header("Step 1: Select a Chat File")
data_folder = "./data"
files = [f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f))]

if not files:
    st.error("No files found in the ./data folder.")
else:
    selected_file = st.selectbox("Select a file to analyze:", files)

    # STEP 2: Parse Chat and Display Participant Overview
    if selected_file:
        st.header("Step 2: Participant Overview")
        file_path = os.path.join(data_folder, selected_file)
        chat_df = parse_chat(file_path)
        print(chat_df)

        if chat_df.empty:
            st.error("No messages found in the selected file.")
        else:
            # Count messages per participant
            message_counts = get_message_counts_participant(chat_df)
            
            # Display in a table
            st.subheader("Message Counts by Participant")
            st.table(message_counts)

            # Bar Chart
            st.bar_chart(message_counts.set_index("sender"))

            # STEP 3: Let's see how it evolved over time
            st.header("Step 3: Messages Over Time")
            messages_per_date, messages_per_hour, heatmap_data = get_message_counts_timestamp(chat_df)
            
            # All participants, per date
            st.subheader("Number of messages per date")
            st.write("On which dates was the chat to most active?")
            st.bar_chart(messages_per_date.set_index("date"))
            
            # All participants, per hour
            st.subheader("Number of messages per hour of the day")
            st.write("What hours of the day are the participants most active?")
            st.bar_chart(messages_per_hour.set_index("hour"))

            # Heatmap, hourly patterns per participant
            st.subheader("Hourly patterns per participant")
            plot_heatmap(heatmap_data)

            # Early Birds & Night Owls
            plot_top3_early_birds(heatmap_data)
            plot_top3_night_owls(heatmap_data)


            # # Step 3: Combine Participants
            # st.subheader("Step 3: Combine Participants")
            # participants = list(message_counts['Participant'])
            # selected_senders = st.multiselect("Select participants to combine:", participants)
            
            # if selected_senders:
            #     new_name = st.text_input("Enter the new name for the combined participants:")
            #     if new_name:
            #         if st.button("Combine and Update"):
            #             chat_df = combine_participants(chat_df, selected_senders, new_name)
            #             message_counts = get_message_counts(chat_df)  # Recompute message counts
            #             st.success(f"Combined participants {selected_senders} into '{new_name}'")
                        
            #             # Display updated message counts
            #             st.table(message_counts)
            #             st.bar_chart(message_counts.set_index("Participant"))
