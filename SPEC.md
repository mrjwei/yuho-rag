# Yuho RAG Specification

## Overview
This specification outlines the requirements and design for the Yuho RAG (Retrieval-Augmented Generation) system, which is intended to facilitate the retrieval and analysis of financial documents, specifically the 有価証券報告書 (Yuho) reports. The system will leverage the EDINET API v2 to fetch the latest Yuho PDFs and provide a user-friendly interface for accessing and analyzing these documents.

## Functional Requirements
1. **Data Retrieval**: The system must be able to fetch the latest Yuho PDFs from the EDINET API v2.
2. **Data Storage**: The fetched PDFs should be stored in a structured format that allows for easy access and retrieval.
3. **User Interface**: The system should provide a user-friendly interface for users to search, view, and analyze the Yuho reports.
4. **Search Functionality**: Users should be able to search for information within the Yuho reports and ask questions about the content of the reports and receive relevant information in response.
5. **Analysis Tools**: The system should include tools for analyzing the content of the Yuho reports, including text extraction, summarization, and data visualization. These tools are used when answering questions that require analysis and/or data visualisation.

## Non-Functional Requirements
1. **Retrieval quality**: The system should ensure that the retrieved Yuho PDFs are accurate and up-to-date. Retrieval quality is measured by the accuracy and relevance of the information provided in response to user queries using recall@5, precision@5, F1 score, and MRR (Mean Reciprocal Rank).
2. **Answer quality**: The system should provide accurate and helpful answers to user questions based on the content of the Yuho reports. Answer quality is measured using a 3-point LLM-as-judge rubric for faithfulness and citation correctness.
3. **Performance**: The system should be able to handle a large number of concurrent users and provide fast response times for data retrieval and analysis.
