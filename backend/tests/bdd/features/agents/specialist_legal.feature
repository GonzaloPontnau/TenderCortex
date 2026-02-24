Feature: Legal Specialist Agent
  As the legal specialist agent
  I want to analyze contractual and legal clauses
  So that analysts understand legal obligations

  Scenario: Generate legal analysis from context
    Given a legal question "Que clausulas penales tiene el contrato?"
    And documents contain contract clauses
    When the legal specialist generates an answer
    Then the answer references legal clauses from the documents

  Scenario: Handle missing legal data
    Given a legal question "Que jurisdiccion aplica?"
    And documents do not contain jurisdiction information
    When the legal specialist generates an answer
    Then the answer indicates the information is not available
