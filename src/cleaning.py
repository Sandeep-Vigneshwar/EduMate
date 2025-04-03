from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate

def clean_list(topics):
    print("clean process initiate.")
    ollama_llm = OllamaLLM(model="llama3.1:latest")
    prompt = PromptTemplate(
        input_variables=["title"],
        template="You should return only one word. 'yes' or 'no'. 'Yes' if the given input is like title of a concept, "
                 "otherwise if it's a noise or broken sentence or unelated, return 'No'.\nTitle: {title}\nAnswer:"
    )
    chatbot = prompt | ollama_llm
    clean_topics = []
    for topic in topics:
        response = chatbot.invoke({"title": topic})
        response_text = response.strip().lower()
        if response_text == "yes":
            clean_topics.append(topic)
    print("Clean process complete.")
    return clean_topics


if __name__ == "__main__":
    inputs = ['0-1 knapsack problem', 'algorithms', 'and strong connectivity', 'annamalai', 'application of these design techniques for real-world', 'applications', 'applications of bfs:', 'applications of dfs', 'as examples', 'backtracking', 'bellman ford', 'biconnected components', 'blind search', 'boyer moore', 'branch and bound 0-1 knapsack', 'bucket', 'class', 'closest pair', 'comparison of', 'connectivity and connected components and cycles in undirected graphs', 'convex hull etc', 'course development plan: 23cse214', 'course objectives:', 'course overview:', 'cuts maximum bipartite matching', 'cycles in directed graphs', 'definitions p', 'descent algorithm', 'distance', 'divide and conquer', 'dynamic programming:', 'examples', 'examples of p and np', 'faculty: dr', 'fibonacci numbers', 'flow algorithms maximum flow', "floyd warshall's", 'fractional knapsack', 'gradient', 'graph algorithms', 'graph traversal', 'greedy algorithm', 'heap', 'heuristic searching algorithms', 'hill climbing algorithm', 'huffman coding etc as examples', 'including problems incorporating combinatorics as examples', 'insertion', 'introduction', 'introduction and review-review of asymptotic notation', 'introduction to np', 'kmp', 'long integer multiplication', 'longest common subsequence', 'master', 'matrix chain multiplication', 'maximum sub array sum', 'merge sort', 'method', 'motivation and types of notations', 'n- queen problem', 'network flow and matching', 'np', 'np hard', 'optimal binary search tree and other problems', 'parallel algorithms', 'path algorithms: shortest path algorithms along with analysis', 'pivot based strategies', 'problem', 'problem solving and analysis of complexity and correctness of algorithms', 'quick select and binary search type strategies', 'quick sort', 'r', 'rabin karp', 'recurrence relations and methods to solve them: recursion tree', 'review of minimum spanning tree', 'review of sorting: bubble', 'sat problem np complete', 'scalable', 'selection', 'sorting algorithms', 'specifically in', 'string matching', 'subject name: design and analysis of algorithms', 'subset sum as some', 'substitution', 'syllabus', 'task scheduling problem', 'terms of algorithm design techniques', 'this course aims to provide the fundamentals of algorithm design and analysis', 'topological sort', 'unit 1', 'unit 2', 'unit 3', 'with analysis and']
    ans = clean_list(inputs)