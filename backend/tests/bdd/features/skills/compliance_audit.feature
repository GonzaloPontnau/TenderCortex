Feature: Compliance Audit Validator Skill
  As the compliance audit validator
  I want to audit requirements against company profiles
  So that bid/no-bid decisions are data-driven

  Scenario: Detect non-compliant mandatory requirement
    Given a mandatory requirement "El licitante DEBE contar con ISO 27001"
    And the company context mentions "ISO 9001, ISO 14001"
    When the compliance audit runs
    Then the status is "NON_COMPLIANT"
    And the severity is "MANDATORY"
    And the gap_analysis explains the missing certification

  Scenario: Confirm compliant desirable requirement
    Given a desirable requirement "Se valorara certificacion PMP"
    And the company context mentions "Juan Perez (PMP, 10 anos exp)"
    When the compliance audit runs
    Then the status is "COMPLIANT"
    And the severity is "DESIRABLE"

  Scenario: Missing information scenario
    Given a requirement "El licitante debe acreditar experiencia"
    And the company context is empty
    When the compliance audit runs
    Then the status is "MISSING_INFO"
