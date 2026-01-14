"""
Single-question runner for Rishi's POC
Adapted from agent-boiler-plate/src/rag_curation/main.py
"""
import sys
import os
import json
from pathlib import Path

# Load env FIRST before any langchain imports
from dotenv import load_dotenv
load_dotenv("/Users/raj/dhcs-intake-lab/.env")

# Add POC to path
poc_path = "/Users/raj/work/workspace/dhcs/agent-boiler-plate/src/rag_curation"
sys.path.insert(0, poc_path)

from LLMS.openaillm import OpenAILLM
from graph.graph_builder import GraphBuilder
from state.state import PolicyState
from tools.vectordb_tool import load_vectorstore
from langchain_core.tools import create_retriever_tool
from langchain_core.messages import HumanMessage

# Hardcoded prompts from main.py
task_1 = 'You will use the retrieved documents to summarize policies and find specific requirements from statutes. Specifically you will find a statute from a specified list and choose which of them apply to a given topic to answer a question.'
task_2 = "You will use the retrieved policy documents to give a summary of the context of the policy and the specific requirements."
task_3 = "Create a formatted concise summary from the following policy report and statute summary. Focus on what is most relevant for answering the question in terms of strict requirements, context for the topic the question addresses and information that has to be included for completeness, accuracy and compliance."
tasks = [task_1, task_2, task_3]

statutes = "'W&I Code § 5899', 'W&I Code § 14184', 'W&I Code § 5892', 'W&I Code § 5891', 'W&I Code § 5830', 'W&I Code § 14018', 'W&I Code Section 5891', 'W&I Code § 5840', 'W&I Code § 8255', 'W&I Code § 5963', 'W&I Code § 8256', 'W&I Code § 5604', 'W&I Code § 14124', 'W&I Code § 14197', 'W&I Code § 5600', 'W&I Code § 5835', 'W&I Code § 5964', 'W&I Code § 5350', 'W&I Code § 5887'"

def run_poc_question(question: str, topic: str = "", policy_manual_section: str = "") -> dict:
    """Run POC pipeline on single question"""

    # Initialize LLM
    user_controls_input = {
        "OPEN_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "selected_model": 'gpt-4o-mini'  # Fixed: was gpt-4.1-mini
    }

    print(f"Initializing POC with model: {user_controls_input['selected_model']}")

    LLModel = OpenAILLM(user_controls_input=user_controls_input)
    llm = LLModel.get_llm_model()
    graph_builder = GraphBuilder(llm)
    agent = graph_builder.policy_chatbot_build_graph()

    # Load vector store
    retriever_cos = load_vectorstore('ip-poicy')
    retriver_tool_cos = create_retriever_tool(
        retriever_cos,
        "cos_document_retriever",
        "Useful for looking up policies, requirements, and statutes from source policy documentation. Uses Cosine Similarity Ranking"
    )

    # Construct topic string
    if not topic:
        topic = f"Topic: {policy_manual_section if policy_manual_section else 'General'}"

    # Retrieval
    print("Retrieving statute chunks...")
    policy_req_statute = f"Statutes starting with prefix 'W&I Code' are relevant for {topic} and {question}. This is the list of statutes:{statutes}"
    statute_text = retriver_tool_cos.invoke(policy_req_statute)

    print("Retrieving policy chunks...")
    policy_req_policy = f"Policy docs for the following topic {topic} and question {question}"
    policy_text = retriver_tool_cos.invoke(policy_req_policy)

    # Create state
    state = PolicyState(
        messages=[],
        question=question,
        topic=topic
    )

    results = {}

    # Stage 1: Statute Analysis
    print("Stage 1: Statute Analysis")
    state['task'] = tasks[0]
    prompt = f"Given a question posed to a county: {question} \n Which of the following statutes are relevant for the sub-section topic: {topic}? Focus strictly on the statutes that address requirements for the question. Provide only the summary of relevant statutes for the question and the summary of their requirements. \n List of statutes: {statutes} \n This the full set of policy data for the topic: {statute_text}"
    state['messages'] = [HumanMessage(content=prompt)]
    ai_response = agent.invoke(state)
    statute_summary = ai_response['messages'][-1].content
    state['statute_summary'] = statute_summary
    results['statute_summary'] = statute_summary
    print(f"  Statute summary length: {len(statute_summary)} chars")

    # Stage 2: Policy Analysis
    print("Stage 2: Policy Analysis")
    state['task'] = tasks[1]
    prompt = f"What is the policy summary for {topic} in the context of the following question: {question}? Use the available policy docs and summarize the policy: {policy_text}"
    state['messages'] = [HumanMessage(content=prompt)]
    ai_response = agent.invoke(state)
    policy_summary = ai_response['messages'][-1].content
    state['policy_summary'] = policy_summary
    results['policy_summary'] = policy_summary
    print(f"  Policy summary length: {len(policy_summary)} chars")

    # Stage 3: Synthesis
    print("Stage 3: Synthesis")
    state['task'] = tasks[2]
    prompt = f"Given the following question that a county must answer on a topic: {topic}\n Question for County: {question} \n Summarize the following information from the policy report and statute summary: ##Policy Report {policy_summary} \n ## Statute Summary {statute_summary}"
    state['messages'] = [HumanMessage(content=prompt)]
    ai_response = agent.invoke(state)
    final_summary = ai_response['messages'][-1].content
    results['final_summary'] = final_summary
    print(f"  Final summary length: {len(final_summary)} chars")

    results['metadata'] = {
        'statute_chunks_retrieved': len(statute_text),
        'policy_chunks_retrieved': len(policy_text)
    }

    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    parser.add_argument("--topic", default="")
    parser.add_argument("--section", default="")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_poc_question(args.question, args.topic, args.section)

    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nSaved to: {args.output}")
