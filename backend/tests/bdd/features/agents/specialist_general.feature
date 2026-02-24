Feature: General Specialist Agent
  As the general specialist agent
  I want to handle questions that don't fit specific domains
  So that all user queries receive appropriate answers

  Scenario: Generate general analysis from context
    Given a general question "De que trata este documento?"
    And documents contain RFP content
    When the general specialist generates an answer
    Then the answer provides a summary based on the documents

  Scenario: Fallback for ambiguous questions
    Given an ambiguous question "Que dice sobre esto?"
    And documents contain mixed content
    When the general specialist generates an answer
    Then the answer is generated without errors
