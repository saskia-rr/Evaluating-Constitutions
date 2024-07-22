from openai import OpenAI
import config
import os
import datetime
import json


class Agent:
    def __init__(self, client, model, temperature, system_instructions, max_tokens):
        self.client = client
        self.model = model
        self.temperature = temperature
        self.system_instructions = system_instructions
        self.max_tokens = max_tokens
        self.conversation_context = [
            {"role": "system", "content": system_instructions}
        ]
        self.agent_name = self.__class__.__name__.lower()

    def generate_response(self, messages):
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=messages,
            max_tokens=self.max_tokens
        )
        return {
            "role": "assistant", 
            "content": response.choices[0].message.content, 
            "name": self.agent_name
        }

    def add_to_context(self, response, role):
        self.conversation_context.append({"role": role, "content": response["content"]})

        
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
        for message in conversation[1:]:  # Skip the system message
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
            print(f"\n--- Iteration {iteration + 1} ---")
            dialogue.append(f"\n ## --- Iteration {iteration + 1} ---\n\n")

            dialogue.append(f"Doctor: Hello, how can I help you today? \n\n")
            
            # Reset only the patient's context
            self.patient.conversation_context = [
                {"role": "system", "content": self.patient.system_instructions},
                {"role": "user", "content": "Hello, how can I help you today?"}
            ]
            
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
            critic_context = [
                {"role": "system", "content": self.critic.system_instructions},
                {"role": "user", "content": f"Here is the complete conversation between the Doctor and Patient.\n{doctor_patient_dialogue}\n Give actionable feedback to the doctor"}
            ]
            critic_feedback = self.critic.generate_response(critic_context)
            self.critic.add_to_context(critic_feedback, "assistant")

            dialogue.append(f"\n #### Critic:\n {critic_feedback['content']}\n\n")

            critic_feedback_to_doctor = f"Here is some feedback on your previous interaction with the patient\n{critic_feedback['content']}\nThe conversation with the patient will start again. Incorporate the feedback given into your responses"
            self.doctor.add_to_context({"role": "user", "content": critic_feedback_to_doctor}, "user")
            self.doctor.add_to_context({"role": "assistant", "content": "I understand and have acknowledged the feedback. I will incorporate it into the following conversation"}, "assistant")

        return self.doctor.conversation_context, self.patient.conversation_context, dialogue


class ExperimentRunner:
    @staticmethod
    def load_instructions(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    @staticmethod
    def create_agents(client, model, temperature, max_tokens, doctor_instructions, patient_instructions, critic_instructions):
        doctor = Doctor(client, model, temperature, doctor_instructions, max_tokens)
        patient = Patient(client, model, temperature, patient_instructions, max_tokens)
        critic = Critic(client, model, temperature, critic_instructions, max_tokens)

        return doctor, patient, critic

    @staticmethod
    def run_experiment(doctor, patient, critic, max_turns, critic_frequency, model, experiment_name):
        conversation = Conversation(doctor, patient, critic)
        doctor_context, patient_context, dialogue = conversation.chat_between_agents(max_turns, critic_frequency)
        Conversation.save_full_conversation_to_markdown(dialogue, f"full_conversations/{model}/{experiment_name}", experiment_name)



def main():

    os.environ["OPENAI_API_KEY"] = config.openai_api_key
    client = OpenAI()
    model = "gpt-4o"
    temperature = 1
    max_tokens = 1000
    max_turns = 3
    critic_frequency = 5

    # Load instructions from files
    doctor_instructions = ExperimentRunner.load_instructions('doctor_instructions.json')
    patient_instructions = ExperimentRunner.load_instructions('patient_instructions.json')
    critic_instructions = ExperimentRunner.load_instructions('critic_instructions.json')

    # Create a list of experiments to run
    experiments = [
        {
            "name": "best_practices_loose",
            "doctor": doctor_instructions["default"],
            "patient": patient_instructions["carpel_tunnel"],
            "critic": critic_instructions["best_practices_loose"]
        },
        {
            "name": "pirate",
            "doctor": doctor_instructions["default"],
            "patient": patient_instructions["carpel_tunnel"],
            "critic": critic_instructions["pirate"]
        },
                {
            "name": "selfdefined",
            "doctor": doctor_instructions["default"],
            "patient": patient_instructions["carpel_tunnel"],
            "critic": critic_instructions["selfdefined"]
        }
    ]

    for experiment in experiments:
        print(f"Running experiment: {experiment['name']}")
        doctor, patient, critic = ExperimentRunner.create_agents(
            client, model, temperature, max_tokens, 
            experiment['doctor'], experiment['patient'], experiment['critic']
        )
        ExperimentRunner.run_experiment(
            doctor, patient, critic, max_turns, critic_frequency, model, experiment['name']
        )
        print(f"Experiment {experiment['name']} completed.\n")

if __name__ == "__main__":
    main()