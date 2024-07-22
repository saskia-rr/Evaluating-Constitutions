import os
import config
import anthropic 
import datetime

os.environ["ANTHROPIC_API_KEY"] = config.claude_api_key
client = anthropic.Anthropic()


class Agent():
    def __init__(self, client, model, temperature, system_instructions, max_tokens):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.system_instructions = system_instructions
        self.max_tokens = max_tokens
        self.conversation_context = []

    def generate_response(self, messages):
        response = self.client.messages.create(
            model=self.model,
            temperature=self.temperature,
            system=self.system_instructions,
            max_tokens=self.max_tokens,
            messages=messages
        )
        return {"role": "assistant", "content": response.content[0].text}

    def add_to_context(self, response, role):
        if role == "user":
            self.conversation_context.append({"role": "user", "content": response["content"]})
        else:
            self.conversation_context.append(response)

class Doctor(Agent):
    pass

class Patient(Agent):
    pass

class Critic(Agent):
    pass

class Conversation:
    def __init__(self, doctor, patient, critic):
        self.doctor = doctor
        self.patient = patient
        self.critic = critic

    @staticmethod
    def conversation_to_string(conversation):
        readable_string = ""
        for message in conversation:
            role = "Doctor" if message['role'] == 'user' else "Patient"
            content = message['content']
            readable_string += f"{role}: {content}\n"
        return readable_string.strip()
    
    @staticmethod
    def save_full_conversation_to_markdown(dialogue, folder_path, experiment):
        os.makedirs(folder_path, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{experiment}_{timestamp}.md"
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Full Doctor-Patient Conversation\n\n")
            for line in dialogue:
                f.write(line)
        
        print(f"Full conversation saved to: {file_path}")

    @staticmethod
    def moderator_check(conversation):
        for message in conversation:
            if "goodbye" in message["content"].lower() or "have a great day" in message["content"].lower():
                return True
        return False
    


    def chat_between_agents(self, max_turns=10, critic_frequency=5):
        dialogue = []
        for iteration in range(max_turns):
            print(f"\n --- Iteration {iteration + 1} ---\n\n")
            dialogue.append(f"\n ## --- Iteration {iteration + 1} ---\n\n")
            
            # Reset only the patient's context
            self.patient.conversation_context = [{"role": "user", "content": "Hello, how can I help you today?"}]

            dialogue.append(f"Doctor: Hello, how can I help you today? \n\n")
            
            # # If it's the first iteration, initialize the doctor's context
            # if iteration == 0:
            #     self.doctor.conversation_context = [{"role": "assistant", "content": "Hello, how can I help you today?"}]

            for turn in range(critic_frequency):
                # Patient's turn
                patient_response = self.patient.generate_response(self.patient.conversation_context)
                self.patient.add_to_context(patient_response, "assistant")
                self.doctor.add_to_context(patient_response, "user")
                
                dialogue.append(f"Patient: {patient_response['content']}\n\n")
                
                if self.moderator_check(self.patient.conversation_context):
                    print("Moderator: Conversation ended as patient said goodbye.")
                    return self.doctor.conversation_context, self.patient.conversation_context, dialogue

                # Doctor's turn
                doctor_response = self.doctor.generate_response(self.doctor.conversation_context)
                self.doctor.add_to_context(doctor_response, "assistant")
                self.patient.add_to_context(doctor_response, "user")

                dialogue.append(f"Doctor: {doctor_response['content']}\n\n")

            # Critic's turn
            doctor_patient_dialogue = self.conversation_to_string(self.patient.conversation_context)
            critic_context = [{"role": "user", "content": f"Here is the complete conversation between the Doctor and Patient.\n{doctor_patient_dialogue}\n Give actionable feedback to the doctor"}]
            critic_feedback = self.critic.generate_response(critic_context)
            self.critic.add_to_context(critic_feedback, "assistant")

            dialogue.append(f"\n #### Critic:\n {critic_feedback['content']}\n\n")

            critic_feedback_to_doctor = f"Here is some feedback on your previous interaction with the patient\n{critic_feedback['content']}\nThe conversation with the patient will start again. Incorporate the feedback given into your responses"
            self.doctor.add_to_context({"role": "user", "content": critic_feedback_to_doctor}, "user")
            self.doctor.add_to_context({"role": "assistant", "content": "I understand and have acknowledged the feedback. I will incorporate it into the following conversation"}, "assistant")

        return self.doctor.conversation_context, self.patient.conversation_context, dialogue


def main():

    os.environ["ANTHROPIC_API_KEY"] = config.claude_api_key
    client = anthropic.Anthropic()
    model = "claude-3-haiku-20240307"
    temperature = 1
    max_tokens = 1000

    max_turns = 3
    critic_frequency = 2

    patient_instructions = "You are a patient chatting with a doctor over an online chat interface. The doctor has never met you before. \
    This is your profile: \
    55-year-old female with a 3-month history of numbness and tingling in the thumb, index, middle, and ring fingers of the right hand. \
    The numbness is worse at night and wakes you up from sleep. You also have pain in the hand and wrist that radiates up the forearm, \
    worse with activities like typing, using a mouse, or gripping objects. \
    Past Medical History includes hypertension and hypothyroidism. \
    You work as a data entry clerk. \
    Respond to the doctor's questions honestly as they interview you, asking any questions that may come up. \
    You should answer as the patient. \
    Do not act as a doctor. \
    Do not reveal you are an AI chatbot.\
    Give your responses in 60 words or less"

    doctor_instructions = "You are an clinician asking a patient about their medical history over an online chat interface. \
    You know nothing about the patient in advance. Respond to the patient with a single-turn response to better understand their history and symptoms. \
    Do not ask more than two questions. If the patient asks a question, be sure to answer it appropriately. Do not tell the patient to see a healthcare provider.Do not reveal you are an AI bot. Give your repsonses in 70 words or less"

    critic_instructions = "You are an AI critic providing feedback to a doctor after they have completed a conversation with a patient. \
    All of the previous conversation is the completed conversation. \
    Give feedback as you see fit.\
    Your feedback will only be seen by the doctor. Give you feedback in 100 words or less"

    doctor = Doctor(client, model, temperature, doctor_instructions, max_tokens)
    patient = Patient(client, model, temperature, patient_instructions, max_tokens)
    critic = Critic(client, model, temperature, critic_instructions, max_tokens) 


    conversation = Conversation(doctor, patient, critic)

    doctor_context, patient_context, dialogue = conversation.chat_between_agents(max_turns, critic_frequency)

    Conversation.save_full_conversation_to_markdown(dialogue, "full_conversations/claude_haiku/selfdefined", "selfdefined")


if __name__ == "__main__":
    main()
