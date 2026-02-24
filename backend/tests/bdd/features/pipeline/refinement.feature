Feature: Answer Refinement Loop
  As the refine node
  I want to improve answers that failed audit
  So that the final answer meets quality standards

  Background:
    Given the pipeline has an answer that failed audit
    And the answer has a domain classification

  Scenario: Successful refinement
    Given the current revision count is 0
    When the refine node processes the answer
    Then a new refined answer is generated
    And the revision count becomes 1
    And the refined answer is sent back for audit

  Scenario: Multiple refinement rounds
    Given the current revision count is 1
    When the refine node processes the answer
    Then the revision count becomes 2
    And the refined answer is sent back for audit

  Scenario: Refinement uses domain context
    Given the domain is "financial"
    When the refine node processes the answer
    Then the refinement prompt includes the domain
    And the refinement uses filtered context documents
