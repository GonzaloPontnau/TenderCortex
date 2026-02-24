Feature: Document Ingest API Endpoint
  As an API consumer
  I want to upload PDF documents for processing
  So that they are indexed and available for queries

  Scenario: Successful PDF upload
    Given the API server is running
    When I POST a PDF file to "/api/ingest"
    Then the response status is 200
    And the response contains "status" as "success"
    And the response contains "filename"
    And the response contains "chunks_processed" greater than 0

  Scenario: Upload non-PDF file
    Given the API server is running
    When I POST a non-PDF file to "/api/ingest"
    Then the response status is 400

  Scenario: Clear index
    Given the API server is running
    And documents have been ingested
    When I DELETE "/api/index"
    Then the response status is 200
    And the vector store is empty

  Scenario: Get index statistics
    Given the API server is running
    When I GET "/api/index/stats"
    Then the response status is 200
    And the response contains vector store statistics
