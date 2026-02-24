Feature: Technical Specialist Agent
  As the technical specialist agent
  I want to analyze technical requirements and architecture
  So that analysts understand implementation demands

  Scenario: Generate technical analysis from context
    Given a technical question "Que arquitectura de software se requiere?"
    And documents contain technical specifications
    When the technical specialist generates an answer
    Then the answer references technical details from the documents

  Scenario: Handle missing technical data
    Given a technical question "Que certificaciones tecnologicas se necesitan?"
    And documents do not contain certification information
    When the technical specialist generates an answer
    Then the answer indicates the information is not available
