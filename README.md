# Evaluating-Constitutions
Code for **Evaluating the role of `Constitutions' for learning from AI feedbacks** , presented at NeurIPS 2024 in the workshop on [Language Gamification](https://language-gamification.github.io//).

![dialogue generation with in-context learning from AI feedback](llm_comms_diagram.jpg)

**Evaluating the role of `Constitutions' for learning from AI feedback** explores how different "constitutions" in large language models impact the quality of text generated following AI feedback for improving patient-centered communication in doctor-patient conversations. All the code required to run the experiments for dialogue and feedback generation can be found in this repository.

The cases for patient vignettes were originally obtained from [Agent Clinic](https://agentclinic.github.io).

## How to run code

Install requirements

```
pip install -r requirements.txt
```

To create dialogue, run:

```
python claude_final.py 
```
Time stamped dialogues with the relevant critic feedback at each round from the experiments can be found in the full_conversations folder
