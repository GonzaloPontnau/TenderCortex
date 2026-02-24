Feature: Document Retrieval Node
  As the retrieve node in the pipeline
  I want to fetch relevant documents from the vector store
  So that downstream nodes have context to work with

  Scenario: Successful document retrieval
    Given the vector store contains indexed documents
    And a user asks "Cual es el presupuesto?"
    When the retrieve node executes
    Then it returns documents in the context field
    And revision_count is initialized to 0

  Scenario: Empty vector store
    Given the vector store is empty
    And a user asks "Cual es el presupuesto?"
    When the retrieve node executes
    Then the no_documents flag is set to true
    And the answer contains the no-documents message
    And the domain is set to "none"

  Scenario: Vector store error is handled gracefully
    Given the vector store raises an exception
    And a user asks "Cual es el presupuesto?"
    When the retrieve node executes
    Then it returns an empty context
    And revision_count is initialized to 0
