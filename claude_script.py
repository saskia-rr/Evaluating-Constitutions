class Agent(ABC):
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

            




from abc import ABC

class Agent(ABC):
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
    def moderator_check(conversation):
        for message in conversation:
            if "goodbye" in message["content"].lower() or "have a great day" in message["content"].lower():
                return True
        return False

    def chat_between_agents(self, max_turns=10, critic_frequency=5):
        for iteration in range(max_turns):
            print(f"\n--- Iteration {iteration + 1} ---")
            
            # Reset only the patient's context
            self.patient.conversation_context = [{"role": "user", "content": "Hello, how can I help you today?"}]
            
            # If it's the first iteration, initialize the doctor's context
            if iteration == 0:
                self.doctor.conversation_context = [{"role": "assistant", "content": "Hello, how can I help you today?"}]

            for turn in range(critic_frequency):
                # Patient's turn
                patient_response = self.patient.generate_response(self.patient.conversation_context)
                self.patient.add_to_context(patient_response, "assistant")
                self.doctor.add_to_context(patient_response, "user")
                
                print(f"Patient: {patient_response['content']}")
                
                if self.moderator_check(self.patient.conversation_context):
                    print("Moderator: Conversation ended as patient said goodbye.")
                    return self.doctor.conversation_context, self.patient.conversation_context

                # Doctor's turn
                doctor_response = self.doctor.generate_response(self.doctor.conversation_context)
                self.doctor.add_to_context(doctor_response, "assistant")
                self.patient.add_to_context(doctor_response, "user")

                print(f"Doctor: {doctor_response['content']}")

            # Critic's turn
            doctor_patient_dialogue = self.conversation_to_string(self.patient.conversation_context)
            critic_context = [{"role": "user", "content": f"Here is the complete conversation between the Doctor and Patient.\n{doctor_patient_dialogue}\n Give actionable feedback to the doctor"}]
            critic_feedback = self.critic.generate_response(critic_context)
            self.critic.add_to_context(critic_feedback, "assistant")

            print(f"\nCritic: {critic_feedback['content']}")

            critic_feedback_to_doctor = f"Here is some feedback on your previous interaction with the patient\n{critic_feedback['content']}\nThe conversation with the patient will start again. Incorporate the feedback given into your responses"
            self.doctor.add_to_context({"role": "user", "content": critic_feedback_to_doctor}, "user")
            self.doctor.add_to_context({"role": "assistant", "content": "I understand and have acknowledged the feedback. I will incorporate it into the following conversation"}, "assistant")

        return self.doctor.conversation_context, self.patient.conversation_context

def main():
    client = None  # Initialize your client here
    model = "claude-3-5-sonnet-20240620"
    temperature = 1
    max_tokens = 1000

    doctor = Doctor(client, model, temperature, doctor_instructions, max_tokens)
    patient = Patient(client, model, temperature, patient_instructions, max_tokens)
    critic = Critic(client, model, temperature, critic_instructions, max_tokens)

    conversation = Conversation(doctor, patient, critic)
    doctor_context, patient_context = conversation.chat_between_agents(max_turns=3, critic_frequency=5)

if __name__ == "__main__":
    main()
