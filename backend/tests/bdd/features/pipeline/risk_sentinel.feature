Feature: Risk Sentinel Audit Gate
  As the compliance auditor
  I want to evaluate every answer for quality and compliance
  So that only audited responses reach the user

  Background:
    Given the pipeline has generated a specialist answer
    And the answer has supporting documents

  Scenario: Audit passes with approved compliance
    Given the risk sentinel evaluates the answer
    When the compliance status is "approved"
    Then the gate_passed flag is true
    And the audit_result is "pass"
    And the pipeline proceeds to END

  Scenario: Audit fails with rejected compliance
    Given the risk sentinel evaluates the answer
    When the compliance status is "rejected"
    Then the gate_passed flag is false
    And the audit_result is "fail"
    And the pipeline routes to refine node

  Scenario: Refinement loop respects max revision cap
    Given the answer has been refined 2 times
    And the risk sentinel evaluates the answer
    When the compliance status is "rejected"
    Then the pipeline proceeds to END despite failure
    And the revision count equals the max_audit_revisions setting

  Scenario: Risk levels are correctly assigned
    Given the risk sentinel evaluates the answer
    Then the risk_level is one of "low", "medium", "high", "critical"
    And risk_issues is a list of strings
