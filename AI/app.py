from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import streamlit as st
import os
from fuzzywuzzy import fuzz
import toml

st.title("Paperflite Chatbot")

# Function to reset the state
def reset_state():
    for key in st.session_state:
        del st.session_state[key]

# Get the API key from the environment variables or the user

# secrets_path = r".\secrets.toml"
# with open(secrets_path, "r") as f:
#     config = toml.load(f)
api_key = "KJ9jag8de6eq8RyenCvYpGlYS2WY3KED"

if not api_key:
    if "api_key" not in st.session_state:
        st.session_state["api_key"] = st.text_input("Enter your API key", type="password")
    api_key = st.session_state["api_key"]
else:
    expected_password = os.getenv("PASSWORD")
    if expected_password:
        password = st.text_input("What's the secret password?", type="password")
        # Check if the entered key matches the expected password
        if password != expected_password:
            api_key = ''
            st.error("Unauthorized access.")
            reset_state()  # This line will reset the script
        else:
            api_key = os.getenv("MISTRAL_API_KEY")

client = MistralClient(api_key=api_key)

# Initialize the model in session state if it's not already set
if "mistral_model" not in st.session_state:
    st.session_state["mistral_model"] = 'mistral-tiny'

# Always display the dropdown
model_options = ('mistral-tiny', 'mistral-small', 'mistral-medium')
st.session_state["mistral_model"] = st.selectbox('Select a model', model_options, index=model_options.index(st.session_state["mistral_model"]), key="model_select")

# Add system prompt input
if "system_prompt" not in st.session_state:
    st.session_state["system_prompt"] = ''

# Add file upload option
uploaded_file = st.file_uploader("Upload a text file", type=["txt"])

# Process uploaded file
file_contents = None
if uploaded_file is not None:
    file_contents = uploaded_file.read().decode("utf-8")

# Rest of your code...

# Display the Mistral response
if "messages" not in st.session_state:
    st.session_state.messages = []

# Add system prompt as a ChatMessage if it doesn't exist
if st.session_state["system_prompt"] and not any(message.role == "system" for message in st.session_state.messages):
    st.session_state.messages.insert(0, ChatMessage(role="system", content=st.session_state["system_prompt"]))

# Display uploaded file contents as a user message
if file_contents:
    new_message = ChatMessage(role="user", content=f"Uploaded file contents:\n```\n{file_contents}\n```")
    st.session_state.messages.append(new_message)
    with st.chat_message("user"):
        st.markdown(new_message.content)

# Rest of your code...

# Display Mistral response
if prompt := st.chat_input("What is up?"):
    new_message = ChatMessage(role="user", content=prompt)
    st.session_state.messages.append(new_message)
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check similarity between user's input and uploaded file contents
    similarity_threshold = 50  # You can adjust this threshold as needed
    if file_contents and fuzz.partial_ratio(prompt, file_contents) < similarity_threshold:
        unrelated_message = "Your question seems unrelated to the uploaded file."
        st.session_state.messages.append(ChatMessage(role="assistant", content=unrelated_message))
        with st.chat_message("assistant"):
            st.markdown(unrelated_message)
    else:
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            for response in client.chat_stream(
                model=st.session_state["mistral_model"],
                messages=st.session_state.messages,  # Pass the entire messages list
            ):
                full_response += (response.choices[0].delta.content or "")
                message_placeholder.markdown(full_response + "▌")
            message_placeholder.markdown(full_response)
        st.session_state.messages.append(ChatMessage(role="assistant", content=full_response))
