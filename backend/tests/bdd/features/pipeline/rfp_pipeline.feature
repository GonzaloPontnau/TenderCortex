Feature: RFP Pipeline End-to-End
  As a procurement analyst
  I want the multi-agent pipeline to process my questions
  So that I get accurate, audited answers from tender documents

  Background:
    Given the vector store contains indexed documents

  Scenario: Successful end-to-end query
    Given a user asks "Cual es el presupuesto total?"
    When the pipeline processes the query
    Then documents are retrieved from the vector store
    And documents are graded for relevance
    And the question is routed to a specialist domain
    And a specialist agent generates an answer
    And the risk sentinel audits the answer
    And the audit result is "pass"
    And a final answer is returned

  Scenario: No documents uploaded
    Given the vector store is empty
    And a user asks "Cual es el presupuesto?"
    When the pipeline processes the query
    Then the pipeline returns a no-documents message
    And the domain is "none"
    And the audit result is "pass"

  Scenario: Audit failure triggers refinement loop
    Given a user asks "Cuales son los requisitos tecnicos?"
    And the risk sentinel will reject the first answer
    When the pipeline processes the query
    Then the answer is sent to the refine node
    And the revision count is incremented
    And the refined answer is re-audited

  Scenario: Quantitative domain routes to QuanT node
    Given a user asks "Compara los presupuestos por partida en un grafico"
    And the question is classified as "quantitative"
    When the pipeline processes the query
    Then the quant node generates chart data
    And quant_insights are populated
    And the answer is audited by risk sentinel
