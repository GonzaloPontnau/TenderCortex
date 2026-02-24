Feature: Financial Specialist Agent
  As the financial specialist agent
  I want to analyze budget and payment information
  So that procurement analysts get accurate financial insights

  Scenario: Generate financial analysis from context
    Given a financial question "Cual es el presupuesto total?"
    And documents contain budget information
    When the financial specialist generates an answer
    Then the answer references financial data from the documents
    And the answer is within the max character limit

  Scenario: Handle missing financial data
    Given a financial question "Cual es el monto de la garantia?"
    And documents do not contain guarantee information
    When the financial specialist generates an answer
    Then the answer indicates the information is not available
