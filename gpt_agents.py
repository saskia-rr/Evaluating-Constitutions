import openai
import config
import time

openai.api_key = config.openai_api_key

def format_conversation(conversation):
    turns = conversation.split("\n\n")
    formatted_conversation = []
    for turn in turns:
        role, content = turn.split(": ", 1)
        formatted_conversation.append(f"{role}:\n{content}\n")
    return "\n".join(formatted_conversation)

# System prompts
system_prompt_patient = "You are a patient chatting with a doctor over an online chat interface. The doctor has never met you before.\
respond to the doctor in single turn repsonses. \
            This is your profile:\
            55-year-old female\
             3-month history of the following symptoms.\
            Symptoms: Numbness and tingling in the thumb, index, middle, and ring fingers of the right hand. The numbness is worse at night and wakes her up from sleep. She also has pain in the hand and wrist that radiates up the forearm. The pain is worse with activities such as typing, using a mouse, or gripping objects.\
Past Medical History: Hypertension, hypothyroidism. \
Past Surgical History: None.\
Past Social History: Works as a data entry clerk. \
Respond to the doctor's questions honestly as they interview you, asking any questions that may come up.\
    DO NOT RESPOND AS A DOCTOR YOU ARE A PATIENT."

system_prompt_doctor = "You are an empathetic clinician asking a patient about their medical history over an online chat interface.\
        You know nothing about the patient in advance. Respond to the patient with a single-turn response to better understand their history and symptoms.\
          Do not ask more than two questions. If the patient asks a question, be sure to answer it appropriately."

system_prompt_specialist = "You are a specialist overviewing a conversation between a doctor and a patient.\
        ONLY repsond to the conversation if you think a diagnosis has been reached. State the diagnosis and conclude the conversation. "

# Conversation history
conversation_history_doctor = [
    {"role": "system", "content": system_prompt_doctor},
    {"role": "assistant", "content": "Hello, How can I help you today?"}
]
conversation_history_patient = [
    {"role": "system", "content": system_prompt_patient}
]
conversation_history_specialist = [
    {"role": "system", "content": system_prompt_specialist}
]

# Response
def get_response(conversation_history):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        temperature = 1,
        messages=conversation_history
    )
    return response.choices[0].message.content


num_turns = 10

# Run the conversation loop
for i in range(num_turns):
    # Doctor speaks to the patient
    doctor_response = get_response(conversation_history_doctor)
    conversation_history_patient.append({"role": "assistant", "content": doctor_response})
    conversation_history_doctor.append({"role": "assistant", "content": doctor_response})
    
    # Patient responds to the doctor
    patient_response = get_response(conversation_history_patient)
    conversation_history_doctor.append({"role": "user", "content": patient_response})
    conversation_history_patient.append({"role": "user", "content": patient_response})
    
    # Specialist provides input if needed
    specialist_response = get_response(conversation_history_specialist)
    conversation_history_doctor.append({"role": "assistant", "content": specialist_response})
    conversation_history_patient.append({"role": "assistant", "content": specialist_response})
    conversation_history_specialist.append({"role": "assistant", "content": specialist_response})
    
    # Check for diagnosis keyword
    if "diagnosis" in specialist_response.lower() or "diagnose" in specialist_response.lower():
        print("Diagnosis reached, ending conversation.")
        break

# Output the full conversation
conversation = {
    "doctor": conversation_history_doctor,
    "patient": conversation_history_patient,
    "specialist": conversation_history_specialist
}