Feature: Chat API Endpoint
  As an API consumer
  I want to send questions to the chat endpoint
  So that I receive structured answers with metadata

  Scenario: Successful chat query
    Given the API server is running
    And documents have been ingested
    When I POST to "/api/chat" with question "Cual es el presupuesto?"
    Then the response status is 200
    And the response contains an "answer" field
    And the response contains "agent_metadata"
    And agent_metadata contains "domain"
    And agent_metadata contains "specialist_used"

  Scenario: Empty question returns validation error
    Given the API server is running
    When I POST to "/api/chat" with question ""
    Then the response status is 422

  Scenario: Question exceeds max length
    Given the API server is running
    When I POST to "/api/chat" with a 2001-character question
    Then the response status is 422

  Scenario: Chat with no documents returns guidance
    Given the API server is running
    And no documents have been ingested
    When I POST to "/api/chat" with question "Cual es el presupuesto?"
    Then the response status is 200
    And the answer contains upload instructions
