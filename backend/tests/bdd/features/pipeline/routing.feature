Feature: Domain Routing
  As the pipeline router
  I want to classify questions into the correct domain
  So that the right specialist agent handles each query

  Scenario Outline: Route question to correct domain
    Given a user asks "<question>"
    When the router classifies the question
    Then the domain is "<domain>"

    Examples:
      | question                                        | domain        |
      | Cual es el presupuesto total de la licitacion?  | financial     |
      | Que clausulas penales tiene el contrato?        | legal         |
      | Que arquitectura de software se requiere?       | technical     |
      | Cual es la fecha limite de entrega?             | timeline      |
      | Que experiencia minima se requiere del equipo?  | requirements  |
      | Compara los montos por partida en un grafico    | quantitative  |
      | De que trata este documento?                    | general       |

  Scenario: Unknown domain falls back to general
    Given a user asks an ambiguous question
    When the router classifies the question
    And the LLM returns an invalid domain
    Then the domain falls back to "general"
