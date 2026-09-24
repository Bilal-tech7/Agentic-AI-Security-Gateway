## Threat Model

### Security Objective

Aurelia is designed to prevent an AI agent from directly exercising
security authority over protected application operations.

The central trust assumption is:

> LLM output is untrusted input.

A tool call proposed by the model must therefore pass through independent
authorization and risk controls before execution.

### Assets Protected

Aurelia protects access to:

- insurance claim records
- customer and policy information
- claim documents
- claim history
- settlement operations
- approval records
- security audit records

The most security-sensitive operation in the prototype is settlement
approval because it changes application state and represents a privileged
business action.

### Trust Boundaries

The architecture contains several important trust boundaries:

```text
                    UNTRUSTED / PARTIALLY TRUSTED

 User Input
     |
     v
 Local LLM  <------- Retrieved / Adversarial Documents
     |
     | proposed action
     v
================ TRUST BOUNDARY =================

 Secure Agent
     |
     v
 Hybrid Security Gateway
     |
     +---- Deterministic Authorization
     |
     +---- ML Risk Analysis
     |
     v
 ALLOW / HUMAN_REVIEW / BLOCK

================ TRUST BOUNDARY =================
     |
     v
 Protected Tools
     |
     v
 Insurance Database

              + Human Approval Workflow
              + Tamper-Evident Audit Log