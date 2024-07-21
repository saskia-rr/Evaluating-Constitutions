import cohere
import os 

patient = cohere.Client()


patient1 = "You are a patient chatting with a doctor over an online chat interface. The doctor has never met you before.\
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

 

patientresponse = patient.chat(
            model="command-r-plus",
            message=patient1,
            temperature=0.5,  
            max_tokens=1000,
            frequency_penalty=0.2
        )

clinician = cohere.Client()
 
clinician1 = "You are an empathetic clinician asking a patient about their medical history over an online chat interface.\
        You know nothing about the patient in advance. Respond to the patient with a single-turn response to better understand their history and symptoms.\
          Do not ask more than two questions. If the patient asks a question, be sure to answer it appropriately."
 
clinicianresponse = clinician.chat(
            model="command-r-plus",
            message= clinician1,
            temperature=0.5, 
            max_tokens=1000,
            frequency_penalty=0.2
        )

patientresponselist= []
clinicianresponselist= [clinicianresponse]

for i in range(5):

    patientloop = patient.chat(
            model="command-r-plus",
            message=clinicianresponselist[i],
            temperature=0,  
            max_tokens=1000,
            frequency_penalty=0.2
        )
    patientresponselist.append(dict(patientloop)['text'])

    clinicianloop = clinician.chat(
            model="command-r-plus",
            message=patientresponselist[i],
            temperature=0, 
            max_tokens=1000,
            frequency_penalty=0.2
        )
    clinicianresponselist.append(dict(clinicianloop)['text'])

for i in range(len(clinicianresponselist)):
    print("Clinician:",clinicianresponselist[i])
    print("")
    print("")
    print("Patient:",patientresponselist[i])
    print("")
    print("")