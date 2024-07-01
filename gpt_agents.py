import openai
import config
import time

openai.api_key = config.openai_api_key

patient_instructions= "You are a patient chatting with a doctor over an online chat interface. The doctor has never met you before.\
            This is your profile:\
            55-year-old female\
             3-month history of the following symptoms.\
            Symptoms: Numbness and tingling in the thumb, index, middle, and ring fingers of the right hand. The numbness is worse at night and wakes her up from sleep. She also has pain in the hand and wrist that radiates up the forearm. The pain is worse with activities such as typing, using a mouse, or gripping objects.\
Past Medical History: Hypertension, hypothyroidism. \
Past Surgical History: None.\
Past Social History: Works as a data entry clerk. \
Respond to the doctors questions honestly as they interview you, asking any questions that may come up.\
You should answer as the patient. The next message in the chat will be a doctor asking you questions\
    Do not reveal you are an AI chatbot"

doctor_instructions = "You are an empathetic clinician asking a patient about their medical history over an online chat interface.\
        You know nothing about the patient in advance. Respond to the patient with a single-turn response to better understand their history and symptoms.\
          Do not ask more than two questions. If the patient asks a question, be sure to answer it appropriately."

 
conversation_context = [
    {"role": "system", "content": doctor_instructions},
    {"role": "system", "content": patient_instructions}
    
]

from openai import OpenAI
client = OpenAI()


def generate_response(messages, agent_name):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages
    )
    message = response['choices'][0]['message']
    message['name'] = agent_name
    return message


# Initialize agents' first messages
doctors_first_message = {"role": "user", "content": "Hello, how are you?", "name": "doctor"}
conversation_context.append(doctors_first_message)

# Conduct the conversation
def chat_between_agents(conversation_context, max_turns=10):
    for _ in range(max_turns):
        # Agent 1's turn
        doctors_response = generate_response(conversation_context, "doctor")
        conversation_context.append(doctors_response)
        
        # Print Agent 1's response
        print(f"Doctor: {doctors_response['content']}")
        
        # Agent 2's turn
        patient_response = generate_response(conversation_context, "patient")
        conversation_context.append(patient_response)
        
        # Print Agent 2's response
        print(f"Patient: {patient_response['content']}")
        
        # Check if the conversation should end
        if len(conversation_context) >= 2 * max_turns + 2:  # system messages + turns
            break

# Start the conversation
chat_between_agents(conversation_context)

# Print the full conversation
print("\nFull conversation:")
for message in conversation_context:
    if message["role"] != "system":
        print(f"{message['name']}: {message['content']}")