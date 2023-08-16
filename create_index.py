import re
import os
from langchain.chains.question_answering import load_qa_chain
import openai
import pinecone
import tiktoken
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# Configure Pinecone variables and initialize
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENVIRONMENT")


# Pinecone db name and upload batch size
index_name = "master"
upsert_batch_size = 20


# Configure OpenAI variables
embed_model = os.getenv('EMBED_MODEL')
openai.api_key = os.getenv('OPENAI_API_KEY')


# OpenAI embedding and tokenizer models
titoken_encoding_model = "cl100k_base"
max_tokens_model = 8191


pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)


def get_embedding(embed_data):
    response = openai.Embedding.create(
        model=embed_model,
        input=embed_data
    )

    # Extract the AI output embedding as a list of floats
    embedding = response["data"][0]["embedding"]
    return embedding



if index_name not in pinecone.list_indexes():
    # Start Embedding Data
    embedding_data = get_embedding([
        "Sample document text goes here", "there will be several phrases in each batch"
    ])

    # Save the embedding data to  Pinecone Index
    print("Creating pinecone index: " + index_name)
    pinecone.create_index(
        index_name,
        dimension=len(embedding_data),
        metric='cosine',
        metadata_config={'indexed': ['source', 'id']}
    )


# def num_tokens_from_string(string: str) -> int:
#     # Returns the number of tokens in a text string.
#     encoding = tiktoken.get_encoding(titoken_encoding_model)
#     num_tokens = len(encoding.encode(string))
#     return num_tokens


# def extract_yaml(text: str) -> str:
#     # Returns list with all the YAML code blocks found in text.
#     matches = [m.group(1) for m in re.finditer("```yaml([\w\W]*?)```", text)]
#     return matches

# print(num_tokens_from_string("tiktoken is great!"))
