from datetime import datetime

import streamlit as st
import os
import pandas as pd
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
    Takes in the full dataframe and returns two dataframes:
    one for messages per date and another for messages per hour.
    """
    # Convert timestamp to date-only format
    chat_df['date'] = chat_df['timestamp'].dt.date
    messages_per_date = chat_df['date'].value_counts().reset_index()  #.rename(columns={'index': 'date', 'date': 'count'})

    # Extract the hour from the timestamp
    chat_df['hour'] = chat_df['timestamp'].dt.hour
    messages_per_hour = chat_df['hour'].value_counts().reset_index()  #.rename(columns={'index': 'hour', 'hour': 'count'})

    return messages_per_date, messages_per_hour


def combine_participants(chat_df, selected_senders, new_name):
    """ Combines the selected senders into a single new name in the chat_df """
    chat_df['sender'] = chat_df['sender'].replace(selected_senders, new_name)
    return chat_df


# UI Starts Here
st.title("Chat Analysis Tool")

# Step 1: File Selection
st.header("Step 1: Select a Chat File")
data_folder = "./data"
files = [f for f in os.listdir(data_folder) if os.path.isfile(os.path.join(data_folder, f))]

if not files:
    st.error("No files found in the ./data folder.")
else:
    selected_file = st.selectbox("Select a file to analyze:", files)

    # Step 2: Parse Chat and Display Participant Overview
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

            # Step 3: Let's see how it evolved over time
            st.header("Step 3: Messages Over Time")
            
            messages_per_date, messages_per_hour = get_message_counts_timestamp(chat_df)
            
            st.subheader("Number of messages per date")
            st.bar_chart(messages_per_date.set_index("date"))
            
            st.subheader("Number of messages per hour of the day")
            st.bar_chart(messages_per_hour.set_index("hour"))

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
