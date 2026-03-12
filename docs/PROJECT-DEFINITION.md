# Project Definition

## One-Line Definition

A local, terminal-based FAQ chatbot that uses semantic retrieval over a curated FAQ dataset and only generates grounded answers when a relevant FAQ match exists.

## Quick Overview

- Product type: small RAG proof of concept
- Primary interface: terminal UI built with Textual
- Knowledge source: curated FAQ dataset in `data/faq.json`
- Retrieval stack: Ollama embeddings plus Qdrant vector search
- Answer generation: local Ollama model constrained to retrieved FAQ context
- Runtime style: local-first, configurable, and suitable for Docker-based execution
- Delivery goal: a clean, explainable submission project that can be demoed reliably

## Problem Statement

The project solves a narrow support problem: users want fast answers to recurring FAQ-style questions without searching a document manually. The system should answer only within the FAQ domain and should fail safely when no relevant FAQ exists.

## Product Goal

Build a robust local chatbot that:

- accepts natural-language questions in the terminal
- identifies the most relevant FAQ semantically
- produces a short answer grounded in that FAQ
- returns a fixed fallback response when relevance is too low
- runs locally with minimal operational complexity

## Non-Goals

The first version does not include:

- a web frontend
- multi-user support
- persistent chat history
- agent behavior or tool calling
- LangChain or LangGraph as a required runtime dependency
- MCP in the product runtime path
- broad open-domain assistant behavior

## Core Product Rules

- The chatbot answers only within the FAQ domain.
- No answer is generated if retrieval confidence is below the configured threshold.
- The language model only receives the relevant FAQ context, not the entire knowledge base.
- Responses must stay short, factual, polite, and easy to understand.
- Internal errors must be translated into controlled user-facing messages.

## Baseline Architecture

### 1. FAQ Data Source

A static machine-readable FAQ file stores the curated knowledge base. Each entry must include:

- `id`
- `question`
- `answer`

Optional fields may include `tags`, `category`, and `source`.

### 2. Ingestion Layer

A separate ingestion process:

- loads and validates FAQ entries
- generates embeddings for each entry
- writes payload plus vectors into Qdrant

This layer is independent from the runtime chat loop.

### 3. Retrieval Layer

At runtime the system:

- embeds the user question
- queries Qdrant for the best semantic matches
- compares the best result against a configurable threshold
- returns either the best FAQ or a fallback decision

### 4. Answer Layer

If retrieval is strong enough, the system builds a grounded prompt from:

- the user question
- the selected FAQ context
- the desired answer style

If retrieval is weak, the system returns the fallback message instead of forcing a model answer.

### 5. Application Layer

A UI-independent application service orchestrates one full chat turn:

- accept request
- run retrieval
- decide fallback or answer generation
- return a structured response to the UI

### 6. Terminal UI Layer

The Textual interface is a thin presentation layer responsible for:

- chat history display
- input collection
- loading and status indicators
- user-friendly error display

### 7. Runtime and Deployment Layer

The system is local-first. Configuration must allow:

- local Ollama access via URL
- local or containerized Qdrant access
- app execution locally or in Docker

Recommended baseline:

- application and Qdrant are Docker-ready
- Ollama is treated as an external local dependency by default
- full Ollama containerization stays optional because it increases runtime complexity

## Runtime Flow

1. User enters a question in the terminal.
2. The input is normalized.
3. The question is embedded with the configured embedding model.
4. Qdrant returns the top semantic matches.
5. The best match is evaluated against the score threshold.
6. If the score is too low, the fallback response is returned.
7. If the score is high enough, a grounded prompt is built from the selected FAQ.
8. The local generation model produces a short answer.
9. The response is displayed in the terminal UI.

## Quality Attributes

- Deterministic behavior over creativity
- Clear separation between UI, application logic, retrieval, and infrastructure
- Local processing by default for privacy and cost control
- Configuration-driven runtime behavior
- Graceful failure when Ollama or Qdrant is unavailable
- Small, reviewable modules and predictable implementation steps

## Success Criteria

The project is considered successful when:

1. The app starts in the terminal and accepts a user question.
2. FAQ data can be ingested into Qdrant from a static source file.
3. Relevant questions retrieve the correct FAQ entry.
4. Irrelevant questions reliably trigger the fallback response.
5. The answer generator stays grounded in the selected FAQ context.
6. Runtime configuration is centralized and documented.
7. The application can be run in a Docker-oriented local setup.
8. A reviewer can understand the architecture and run the project from the documentation.

## Normalized Decisions From the Source Documents

- Generation model and embedding model are separate configurable values.
- The application service is the orchestration boundary; the UI must stay thin.
- Ingestion is an explicit standalone process, not part of the chat runtime.
- Deployment is treated as its own module instead of being scattered across phases.
- Testing and documentation are explicit deliverables, not optional polish.
