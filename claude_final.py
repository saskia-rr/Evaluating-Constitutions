import os
import config
import anthropic
import datetime
import json


os.environ["ANTHROPIC_API_KEY"] = config.claude_api_key
client = anthropic.Anthropic()

class Agent:
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

class Moderator(Agent):
    def check_conversation_status(self, conversation, correct_diagnosis):
        moderator_context = [{
            "role": "user", 
            "content": f"""Here is a conversation between a doctor and a patient. Analyze the conversation and provide the following information:
            1. Has the conversation naturally concluded with either doctor or patient being able to say "thank you" ? (Yes/No)
            2. Has any diagnosis been reached, even if incorrect? (Yes/No)
            3. Has the correct diagnosis ({correct_diagnosis}) been reached? (Yes/No)
            
            Respond in the format: "Concluded: Yes/No, Diagnosis: Yes/No, Correct: Yes/No"
            
            Conversation:
            {Conversation.conversation_to_string(conversation)}"""
        }]
        response = self.generate_response(moderator_context)
        return self.parse_moderator_response(response['content'])
    
    def parse_moderator_response(self, response):
        response = response.lower()
        result = {
            'concluded': False,
            'diagnosis_reached': False,
            'correct_diagnosis': False
        }
        
        if 'concluded: yes' in response:
            result['concluded'] = True
        if 'diagnosis: yes' in response:
            result['diagnosis_reached'] = True
        if 'correct: yes' in response:
            result['correct_diagnosis'] = True
        
        return result

class Conversation:
    def __init__(self, doctor, patient, critic, moderator, correct_diagnosis, initial_patient_response):
        self.doctor = doctor
        self.patient = patient
        self.critic = critic
        self.moderator = moderator
        self.correct_diagnosis = correct_diagnosis
        self.correct_diagnosis_reached = False
        self.initial_patient_response = initial_patient_response

    @staticmethod
    def conversation_to_string(conversation):
        readable_string = ""
        for message in conversation:
            role = "Doctor" if message['role'] == 'user' else "Patient"
            content = message['content']
            readable_string += f"{role}: {content}\n"
        return readable_string.strip()
    
    @staticmethod
    def save_full_conversation_to_markdown(dialogue, folder_path, experiment, correct_diagnosis, model_name):
        os.makedirs(folder_path, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{model_name}_{experiment}_{correct_diagnosis}_{timestamp}.md"
        file_path = os.path.join(folder_path, filename)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Full Doctor-Patient Conversation\n\n")
            for line in dialogue:
                f.write(line)
        
        print(f"Full conversation saved to: {file_path}")


    def chat_between_agents(self, max_turns=5):
        dialogue = []
        for iteration in range(max_turns):
            print(f"\n --- Iteration {iteration + 1} ---\n\n")
            dialogue.append(f"\n ## --- Iteration {iteration + 1} ---\n\n")
            
            # Reset the patient's context for each turn
            self.patient.conversation_context = [
                {"role": "user", "content": "Hello, how can I help you today?"},
                {"role": "assistant", "content": self.initial_patient_response}
            ]
            dialogue.append(f"Doctor: Hello, how can I help you today? \n\n")
            dialogue.append(f"Patient: {self.initial_patient_response}\n\n")
            
            # Add the initial patient response to the doctor's context
            self.doctor.add_to_context({"role": "user", "content": self.initial_patient_response}, "user")
            
            while True:
                # Doctor's turn
                doctor_response = self.doctor.generate_response(self.doctor.conversation_context)
                self.doctor.add_to_context(doctor_response, "assistant")
                self.patient.add_to_context(doctor_response, "user")

                dialogue.append(f"Doctor: {doctor_response['content']}\n\n")
                print(f"Doctor: {doctor_response['content']}")

                # Check if the conversation turn has ended after doctor's response
                status = self.moderator.check_conversation_status(self.patient.conversation_context, self.correct_diagnosis)
                if status['concluded']:
                    if status['diagnosis_reached']:
                        if status['correct_diagnosis']:
                            print("Moderator: Conversation concluded with correct diagnosis.")
                            self.correct_diagnosis_reached = True
                            dialogue.append("Moderator: Conversation concluded with correct diagnosis.")
                        else:
                            print("Moderator: Conversation concluded with incorrect diagnosis.")
                            self.correct_diagnosis_reached = True
                            dialogue.append("Moderator: Conversation concluded with incorrect diagnosis.")
                    else:
                        print("Moderator: Conversation concluded without a clear diagnosis.")
                        self.correct_diagnosis_reached = True
                        dialogue.append("Moderator: Conversation concluded without a clear diagnosis.")
                    break

                # Patient's turn
                patient_response = self.patient.generate_response(self.patient.conversation_context)
                self.patient.add_to_context(patient_response, "assistant")
                self.doctor.add_to_context(patient_response, "user")
                
                dialogue.append(f"Patient: {patient_response['content']}\n\n")
                print(f"Patient: {patient_response['content']}")


            # Critic's turn after each conversation turn
            doctor_patient_dialogue = self.conversation_to_string(self.patient.conversation_context)
            critic_context = [{"role": "user", "content": f"Here is the complete conversation for this turn.\n{doctor_patient_dialogue}\nGive feedback for the next turn."}]
            critic_feedback = self.critic.generate_response(critic_context)
            self.critic.add_to_context(critic_feedback, "assistant")

            dialogue.append(f"\n #### Critic:\n {critic_feedback['content']}\n\n")

            # Provide feedback to the doctor for the next turn
            critic_feedback_to_doctor = f"Here is feedback on your previous interaction with the patient:\n{critic_feedback['content']}\nIncorporate this feedback into your responses in the next turn of the conversation."
            self.doctor.add_to_context({"role": "user", "content": critic_feedback_to_doctor}, "user")
            self.doctor.add_to_context({"role": "assistant", "content": "I understand and have acknowledged the feedback. I will incorporate it into the next turn of the conversation."}, "assistant")
            self.doctor.add_to_context({"role": "user", "content": "The next round of conversation is about to start."},"user")
            self.doctor.add_to_context({"role": "assistant", "content": "Hello, how can I help you today?"}, "assistant")

            print("\n--- Full Doctor's Context ---")
            for message in self.doctor.conversation_context:
                print(f"{message['role']}: {message['content']}")
        
            print("\n--- Full Patient's Context ---")
            for message in self.patient.conversation_context:
                print(f"{message['role']}: {message['content']}")


        print("All turns completed.")
        return self.doctor.conversation_context, self.patient.conversation_context, dialogue, self.correct_diagnosis_reached

class ExperimentRunner:
    @staticmethod
    def load_instructions(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    @staticmethod
    def create_agents(client, model, doctor_temperature, patient_temperature, critic_temperature, moderator_temperature, max_tokens, doctor_instructions, patient_instructions, critic_instructions, moderator_instructions):
        doctor = Doctor(client, model, doctor_temperature, doctor_instructions, max_tokens)
        patient = Patient(client, model, patient_temperature, patient_instructions, max_tokens)
        critic = Critic(client, model, critic_temperature, critic_instructions, max_tokens)
        moderator = Moderator(client, model, moderator_temperature, moderator_instructions, max_tokens)

        return doctor, patient, critic, moderator

    @staticmethod
    def run_experiment(doctor, patient, critic, moderator, max_turns, model, model_name, experiment_name, correct_diagnosis, initial_patient_response):
        conversation = Conversation(doctor, patient, critic, moderator, correct_diagnosis, initial_patient_response)
        doctor_context, patient_context, dialogue, correct_diagnosis_reached = conversation.chat_between_agents(max_turns)
        
        if correct_diagnosis_reached:
            Conversation.save_full_conversation_to_markdown(dialogue, f"full_conversations/{model_name}/{experiment_name}/{correct_diagnosis}", experiment_name, correct_diagnosis, model_name)
            print(f"Correct diagnosis reached. Conversation saved for experiment: {experiment_name}")
        else:
            print(f"Correct diagnosis not reached. Conversation not saved for experiment: {experiment_name}")


def main():


    os.environ["ANTHROPIC_API_KEY"] = config.claude_api_key
    client = anthropic.Anthropic()

    model = "claude-3-5-sonnet-20240620"
    model_name = "claude_3_5_sonnet"
    max_tokens = 1000
    max_turns = 2


    doctor_temperature = 1
    patient_temperature = 1
    critic_temperature = 1
    moderator_temperature = 1


    # Load instructions from files
    doctor_instructions = ExperimentRunner.load_instructions('doctor_instructions.json')
    patient_instructions = ExperimentRunner.load_instructions('agent_clinic_sample_starting_prompt_claude_temp1.json')
    critic_instructions = ExperimentRunner.load_instructions('critic_instructions.json')
    moderator_instructions = ExperimentRunner.load_instructions('moderator_instructions.json')

    # Create a list of experiments to run
    experiments = []

    for key in patient_instructions:
        experiments.extend([

            {
                "name": "best_practices_detailed_patient_temp_1",
                "doctor": doctor_instructions["default"],
                "patient": patient_instructions[key][1],
                "critic": critic_instructions["best_practices_detailed"],
                "moderator": moderator_instructions["default"],
                "correct_diagnosis": patient_instructions[key][0],
                "initial_patient_response": patient_instructions[key][1]
            },
                        
            {
                "name": "empathetic_patient_temp_1",
                "doctor": doctor_instructions["default"],
                "patient": patient_instructions[key][1],
                "critic": critic_instructions["empathetic"],
                "moderator": moderator_instructions["default"],
                "correct_diagnosis": patient_instructions[key][0],
                "initial_patient_response": patient_instructions[key][1]
            },

            {
                "name": "doctor_role_patient_temp_1",
                "doctor": doctor_instructions["default"],
                "patient": patient_instructions[key][1],
                "critic": critic_instructions["doctor_role"],
                "moderator": moderator_instructions["default"],
                "correct_diagnosis": patient_instructions[key][0],
                "initial_patient_response": patient_instructions[key][1]
            },
            {
                "name": "no_constitution_patient_temp_1",
                "doctor": doctor_instructions["default"],
                "patient": patient_instructions[key][1],
                "critic": critic_instructions["no_constitution"],
                "moderator": moderator_instructions["default"],
                "correct_diagnosis": patient_instructions[key][0],
                "initial_patient_response": patient_instructions[key][1]
            }
                       
        ])
        


    for experiment in experiments:
        print(f"Running experiment: {experiment['name']}")
        doctor, patient, critic, moderator = ExperimentRunner.create_agents(
        client, model, 
        doctor_temperature, patient_temperature, critic_temperature, moderator_temperature,
        max_tokens, 
        experiment['doctor'], experiment['patient'], experiment['critic'], experiment['moderator']
        )
        ExperimentRunner.run_experiment(
            doctor, patient, critic, moderator, max_turns, model, model_name, 
            experiment['name'], experiment['correct_diagnosis'], experiment['initial_patient_response'] 
        )
        print(f"Experiment {experiment['name']} completed.\n")


if __name__ == "__main__":
    main()