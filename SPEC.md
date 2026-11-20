# Yuho RAG Specification

## Overview
This specification outlines the requirements and design for the Yuho RAG (Retrieval-Augmented Generation) system, which is intended to facilitate the retrieval and analysis of financial documents, specifically the 有価証券報告書 (Yuho) reports. The system will leverage the EDINET API v2 to fetch the latest Yuho PDFs and provide a user-friendly interface for accessing and analyzing these documents.

## Functional Requirements
1. **Data Retrieval**: The system must be able to fetch the latest Yuho PDFs from the EDINET API v2.
2. **Data Storage**: The fetched PDFs should be stored in a structured format that allows for easy access and retrieval.
3. **HTTP API (`/ask`, `/compare`) with OpenAPI docs**: The system should provide an HTTP API with endpoints for asking questions about the Yuho reports and comparing information across different companies. The API should be documented using OpenAPI specifications to ensure clarity and ease of use for developers.
4. **Search Functionality**: Users should be able to search for information within the Yuho reports and ask questions about the content of the reports and receive relevant information in response.
5. **Cross-company comparison (`/compare`)**: The system should allow users to compare information across different companies' Yuho reports.
6. **Every answer cites company + page**: All answers provided by the system should include citations that reference the specific company and page number from which the information was retrieved, ensuring transparency and traceability of the information provided.

## Non-Functional Requirements
1. **Retrieval quality**: The system should ensure that the retrieved Yuho PDFs are accurate and up-to-date. Retrieval quality is measured by the accuracy and relevance of the information provided in response to user queries using recall@5 and MRR (Mean Reciprocal Rank). precision@5 and F1 score are secondary.
2. **Answer quality**: The system should provide accurate and helpful answers to user questions based on the content of the Yuho reports. Answer quality is measured using a 3-point LLM-as-judge rubric for faithfulness and citation correctness.
3. **Performance**: The system should be able to handle p95 latency target for `/ask` (e.g. < 6 s warm), single-instance demo, and provide fast response times for data retrieval and analysis.

## Out of scope
1. Auth/accounts
2. User uploads
3. Frontend
4. XBRL
5. Fine-tuning
