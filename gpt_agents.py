from openai import OpenAI

# Initialize OpenAI client
client = OpenAI()

class Agent:
    def __init__(self, role, instructions, model):
        self.role = role
        self.instructions = instructions
        self.context = [{"role": "system", "content": self.instructions}]
        self.name = role.lower()
        self.model =  model

    def add_message(self, message):
        self.context.append(message)

    def generate_response(self):
        response = client.chat.completions.create(
            model= self.model,
            temperature=1,
            messages=self.context
        )
        assistant_message = {"role": "assistant", "content": response.choices[0].message.content, "name": self.name}
        user_message = {"role": "user", "content": response.choices[0].message.content, "name": self.name}
        self.add_message(assistant_message)
        return assistant_message, user_message

class Moderator:
    @staticmethod
    def check_for_termination(conversation):
        for message in conversation:
            if if "goodbye" in message["content"].lower() or "have a great day" in message["content"].lower():
                return True
        return False

class ChatSimulation:
    def __init__(self, doctor, patient, critic, max_turns=20):
        self.doctor = doctor
        self.patient = patient
        self.critic = critic
        self.max_turns = max_turns

    def start_conversation(self):
        # Initialize agents' first messages
        initial_message = {"role": "assistant", "content": "Hello, how are you?", "name": "doctor"}
        self.doctor.add_message(initial_message)
        self.patient.add_message({"role": "user", "content": initial_message["content"], "name": "doctor"})

        for _ in range(self.max_turns):
            # Patient's turn
            patient_response = self.patient.generate_response()
            self.doctor.add_message(patient_response[1])
            print(f"Patient: {patient_response[0]['content']}")

            if Moderator.check_for_termination(self.patient.context):
                print("Moderator: Conversation ended as patient said goodbye.")
                break

            # Doctor's turn
            doctor_response = self.doctor.generate_response()
            self.patient.add_message(doctor_response[1])
            print(f"Doctor: {doctor_response[0]['content']}")

            if Moderator.check_for_termination(self.doctor.context):
                print("Moderator: Conversation ended as doctor said goodbye.")
                break

            # Critic's feedback
            critic_feedback = self.critic.generate_response()
            self.critic.add_message({"role": "user", "content": doctor_response[0]["content"], "name": "doctor"})
            print(f"Critic: {critic_feedback[0]['content']}")

        return self.doctor.context, self.patient.context


