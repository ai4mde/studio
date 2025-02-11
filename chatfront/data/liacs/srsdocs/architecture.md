---
id: system-architecture
title: System Architecture
description: Detailed overview of AI4MDE's system architecture and components
date: 2024-10-30
---

# System Architecture

## High-Level Architecture

AI4MDE follows a modern, microservices-based architecture with the following main components:

1. **Frontend Layer**
   - React-based web interface
   - Real-time collaboration features
   - Responsive design for all devices

2. **API Gateway**
   - Authentication and authorization
   - Request routing and load balancing
   - Rate limiting and caching

3. **Core Services**
   - Model Management Service
   - AI Processing Service
   - Collaboration Service
   - Version Control Service

4. **AI Components**
   - Natural Language Processing Engine
   - Model Analysis Engine
   - Code Generation Engine
   - Pattern Recognition Engine

## Technology Stack

- **Frontend**: React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python, SQLAlchemy
- **Database**: PostgreSQL
- **AI/ML**: PyTorch, Transformers, Scikit-learn
- **Infrastructure**: Docker, Kubernetes 

## UML Diagram

```plantuml
@startuml Database ERD

!define table(x) class x << (T,#FFAAAA) >>
!define enum(x) class x << (E,#A9DCDF) >>
!define primary_key(x) <u>x</u>
!define foreign_key(x) #x#
!define unique(x) <i>x</i>
!define nullable(x) <color:gray>x</color>

' Enums
enum(ChatRole) {
    USER
    ASSISTANT
    SYSTEM
}

enum(ConversationState) {
    INTERVIEW
    DOCUMENT
    COMPLETED
}

' Tables
table(groups) {
    primary_key(id): INTEGER
    unique(name): STRING
    nullable(description): STRING
    created_at: TIMESTAMP
    updated_at: TIMESTAMP
}

table(users) {
    primary_key(id): INTEGER
    unique(email): STRING
    unique(username): STRING
    hashed_password: STRING
    is_active: BOOLEAN
    created_at: TIMESTAMP
    updated_at: TIMESTAMP
    foreign_key(group_id): INTEGER
}

table(chat_sessions) {
    primary_key(id): INTEGER
    foreign_key(user_id): INTEGER
    foreign_key(group_id): INTEGER
    title: STRING
    state: STRING
    created_at: TIMESTAMP
    updated_at: TIMESTAMP
}

table(chat_messages) {
    primary_key(id): INTEGER
    foreign_key(session_id): INTEGER
    message_uuid: UUID
    role: ChatRole
    content: TEXT
    created_at: TIMESTAMP
    nullable(message_metadata): JSONB
}

table(chat_state) {
    primary_key(session_id): INTEGER
    current_section: INTEGER
    current_question_index: INTEGER
    state: ConversationState
    nullable(progress): FLOAT
    updated_at: TIMESTAMP
}

' Relationships
users }|--|| groups : belongs to
chat_sessions }|--|| users : belongs to
chat_sessions }o--|| groups : belongs to
chat_messages }|--|| chat_sessions : belongs to
chat_state ||--|| chat_sessions : belongs to

@enduml
```
