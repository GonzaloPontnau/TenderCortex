Feature: RFP Document Loader Skill
  As the document loader
  I want to extract and chunk PDF documents
  So that they can be indexed for RAG retrieval

  Scenario: Load a standard PDF with text
    Given a valid PDF file with text content
    When the document loader processes the file
    Then document chunks are returned
    And each chunk has page_number metadata
    And each chunk has source metadata

  Scenario: Handle encrypted PDF
    Given an encrypted PDF file
    When the document loader processes the file
    Then an EncryptedPDFError is raised

  Scenario: Handle empty PDF
    Given a PDF file with no extractable text
    When the document loader processes the file
    Then zero chunks are returned
