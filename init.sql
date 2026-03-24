-- Active: 1774294615835@@127.0.0.1@5432@chat
CREATE TABLE CHAT (
    chat_id VARCHAR(36),
    chat_name VARCHAR(200),
    creation_date TIMESTAMPTZ,
    PRIMARY KEY(chat_id)
)

CREATE TABLE CHAT_EXCHANGE (
    chat_exchange_id VARCHAR(36),
    chat_id VARCHAR(36),
    exchange_date TIMESTAMP,
    PRIMARY KEY (chat_exchange_id),
    FOREIGN KEY (chat_id) REFERENCES CHAT(chat_id)
)

CREATE TABLE CHAT_QUESTION (
    chat_question_id VARCHAR(36),
    chat_exchange_id VARCHAR(36),
    user_prompt TEXT,
    system_prompt TEXT,
    asked_date TIMESTAMP,
    PRIMARY KEY (chat_question_id),
    FOREIGN KEY (chat_exchange_id) REFERENCES CHAT_EXCHANGE(chat_exchange_id)
)

CREATE TABLE CHAT_QUESTION_HISTORY (
    chat_question_history_id VARCHAR(36),
    chat_question_id VARCHAR(36),
    user_role VARCHAR(50),
    message_content TEXT,
    history_order INT,
    PRIMARY KEY (chat_question_history_id),
    FOREIGN KEY (chat_question_id) REFERENCES CHAT_QUESTION(chat_question_id)
)

CREATE TABLE CHAT_ANSWER (
    chat_answer_id VARCHAR(36),
    chat_exchange_id VARCHAR(36),
    assistant_response TEXT,
    creation_date TIMESTAMP,
    PRIMARY KEY (chat_answer_id),
    FOREIGN KEY (chat_exchange_id) REFERENCES CHAT_EXCHANGE(chat_exchange_id)
)

CREATE TABLE CHAT_ANSWER_HISTORY (
    chat_answer_history_id VARCHAR(36),
    chat_answer_id VARCHAR(36),
    user_role VARCHAR(50),
    message_content TEXT,
    tool_name VARCHAR(200),
    thinking TEXT,
    history_order INT,
    PRIMARY KEY (chat_answer_history_id),
    FOREIGN KEY (chat_answer_id) REFERENCES CHAT_ANSWER(chat_answer_id)
)

CREATE TABLE CHAT_ANSWER_HISTORY_TOOL_CALL (
    chat_answer_history_tool_call_id VARCHAR(36),
    chat_answer_history_id VARCHAR(36),
    tool_name VARCHAR(200),
    PRIMARY KEY (chat_answer_history_tool_call_id),
    FOREIGN KEY (chat_answer_history_id) REFERENCES CHAT_ANSWER_HISTORY(chat_answer_history_id)
)

CREATE TABLE CHAT_ANSWER_HISTORY_TOOL_ARGUMENT (
    chat_answer_history_tool_argument_id VARCHAR(36),
    chat_answer_history_tool_call_id VARCHAR(36),
    argument_name VARCHAR(100),
    argument_value TEXT,
    PRIMARY KEY (chat_answer_history_tool_argument_id),
    FOREIGN KEY (chat_answer_history_tool_call_id) REFERENCES CHAT_ANSWER_HISTORY_TOOL_CALL(chat_answer_history_tool_call_id)
)