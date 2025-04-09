from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import TencentVectorDB
from langchain_community.vectorstores.tencentvectordb import ConnectionParams
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.chat_models import ChatZhipuAI
from langchain_community.chat_models import ChatHunyuan
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import bs4
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv  
import os  

load_dotenv()  
api_key = os.getenv("ZHIPUAI_API_KEY")


# 设置最大历史对话记录数
DEFAULT_MAX_MESSAGES=20

# 限制聊天记录
class LimitedChatMessageHistory(ChatMessageHistory):
     max_messages: int = DEFAULT_MAX_MESSAGES

     def _init_(self,max_messages=DEFAULT_MAX_MESSAGES):
         super().__init__()
         self.max_messages=max_messages

     def add_message(self,message):
         super().add_message(message)
         #调整历史记录
         if len(self.messages)>self.messages:
            self.messages=self.messages[-self.max_messages:]

     def get_messages(self):
         return self.messages
          




class RAG:
    store = {}

    def conversation(self,question,user_id):  
        llm = ChatZhipuAI(temperature=0.01, model="glm-4-plus")
        t_vdb_embedding = "bge-base-zh"  # bge-base-zh is the default model
        embeddings = None
        conn_params = ConnectionParams(
        url="http://gz-vdb-hall4gay.sql.tencentcdb.com:8100",
        key="mw0HGppdr87iNikSQq90LqtMquxJgWTlbnBla2AY",
        username="root",
        timeout=100,
        )
        vectorstore = TencentVectorDB(
         embeddings, connection_params=conn_params,t_vdb_embedding=t_vdb_embedding)
        retriever = vectorstore.as_retriever()
        ### 整合聊天内容和检索到的文本 ###
        contextualize_q_system_prompt = (
            "给定一个聊天记录和使用者最新的问题"
            "问题可能与聊天记录的上下文有关"
            "把这个问题修改为不需要聊天记录也能被理解的形式。不要回答问题本身"
            "如果不需要修改输出问题本身"
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        ### Answer question ###
        system_prompt = (
            
            "你是问答任务的助理。使用以下检索到的上下文来回答问题。如果上下文中没有问题的答案，你可以用自己的知识回答。如果你不知道答案，就说你不知道。保持回答简明扼要。"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

        ### Statefully manage chat history ###
        def get_session_history(session_id: str) -> BaseChatMessageHistory:
           if session_id not in RAG.store:
             RAG.store[session_id] = LimitedChatMessageHistory()
           return RAG.store[session_id]
        conversational_rag_chain = RunnableWithMessageHistory(
            rag_chain,
            get_session_history,
            input_messages_key="input",
            history_messages_key="chat_history",
            output_messages_key="answer",
        )
        answer=conversational_rag_chain.invoke(
        {"input": question},
        config={
        "configurable": {"session_id": user_id}
        },  
        )["answer"]
        
        return answer  
    
  #上传文件到数据库
    def upload(self,filepath):  
        t_vdb_embedding = "bge-base-zh"  # bge-base-zh is the default model
        embeddings = None
        conn_params = ConnectionParams(
        url="http://gz-vdb-hall4gay.sql.tencentcdb.com:8100",
        key="mw0HGppdr87iNikSQq90LqtMquxJgWTlbnBla2AY",
        username="root",
        timeout=100,
        )
        vectorstore= TencentVectorDB(
            embedding = embeddings,
            connection_params=conn_params,
            database_name = "LangChainDatabase",
            collection_name = "LangChainCollection",
            drop_old = 0,
        )
        # vectorstore = TencentVectorDB(
        #  embeddings, connection_params=conn_params,t_vdb_embedding=t_vdb_embedding)
        loader=TextLoader(filepath,encoding='utf-8')
        doc = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=20)
        docs = text_splitter.split_documents(doc)
        vectorstore.add_documents(docs)

        return 'File uploaded successfully'  

 




