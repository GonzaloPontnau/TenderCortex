Feature: Document Grading Node
  As the grading node in the pipeline
  I want to filter documents by relevance
  So that only relevant documents reach the specialist

  Background:
    Given the retrieve node returned 10 documents

  Scenario: Documents are graded and filtered
    Given a user asks "Cual es el presupuesto?"
    When the grading node evaluates documents
    Then only relevant documents remain in filtered_context
    And filtered_context has fewer or equal documents than context

  Scenario: Safety net activates for data-heavy questions
    Given a user asks "Cual es el cronograma de pagos?"
    And the grader marks all documents as not_relevant
    When the grading node evaluates documents
    Then the safety net provides fallback documents
    And filtered_context is not empty

  Scenario: No relevant documents triggers fallback
    Given a user asks "Algo completamente irrelevante"
    And the grader marks all documents as not_relevant
    When the grading node evaluates documents
    Then the safety net provides fallback documents
