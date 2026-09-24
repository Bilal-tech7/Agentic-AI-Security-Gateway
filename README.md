**# Aurelia — Secure Agentic AI Gateway**

**## Overview**

Aurelia is a prototype security gateway for an agentic AI insurance claims system.

It is designed around one core security principle:

\> **\*\*LLM proposes → Security Gateway authorizes → Protected tool executes\*\***

The language model is allowed to reason about a task and propose tool calls, but it is never treated as the authority that decides whether an action is permitted.

Instead, every protected action is independently evaluated by a security gateway before execution.

**---**

**## Problem**

Agentic AI systems can generate and execute tool calls, creating security risks when model-generated actions are trusted directly.

Potential threats include:

\- prompt injection

\- unauthorized tool access

\- unauthorized resource access

\- excessive permissions

\- malformed or manipulated requests

\- high-risk autonomous actions

\- approval tampering

\- approval replay

\- audit-log tampering

Aurelia addresses these risks by placing an independent security enforcement layer between the AI agent and protected application tools.

**---**

**## Architecture**

\`\`\`text

User

 |

 v

Local LLM (Ollama)

 |

 | proposes tool call

 v

Secure Agent Layer

 |

 v

Hybrid Security Gateway

 |

 +---- Deterministic Authorization

 |       |

 |       +---- Role permissions

 |       +---- Resource authorization

 |       +---- Argument validation

 |       +---- Business rules

 |

 +---- ML Risk Analysis

 |

 v

ALLOW / HUMAN_REVIEW / BLOCK

 |

 +---- ALLOW ----------------> Protected Tool

 |

 +---- HUMAN_REVIEW ---------> Approval Workflow

 |                                  |

 |                                  v

 |                            Human Decision

 |                                  |

 |                                  v

 |                            Re-Authorization

 |                                  |

 |                                  v

 |                            Protected Tool

 |

 +---- BLOCK ----------------> No Execution

 |

 v

Tamper-Evident Audit Log

\`\`\`

The architecture deliberately separates:

1\. **\*\*AI reasoning\*\***

2\. **\*\*security authorization\*\***

3\. **\*\*protected execution\*\***

This prevents the LLM from becoming the security authority.

**---**

**## Security Controls**

Aurelia implements:

\- Role-based access control

\- Claim-level resource authorization

\- Business-state validation

\- Argument validation

\- Protected tool execution

\- Human approval for high-risk operations

\- Approval integrity hashing

\- Approval replay protection

\- Approval identity tampering detection

\- ML-assisted security risk analysis

\- Prompt-injection risk signals

\- Fail-safe deterministic authorization

\- Tamper-evident audit logging

\- SHA-256 audit hash chaining

\- Unified security-event auditing

\- Local LLM integration through Ollama

**---**

**## Hybrid Security Model**

Aurelia combines deterministic security controls with an experimental ML risk model.

**### Deterministic Layer**

The deterministic security gateway evaluates rules such as:

\- whether a role may use a tool

\- whether the requested resource belongs to the user

\- whether required arguments are present

\- whether arguments are valid

\- whether an operation is considered high risk

\- whether human approval is required

Deterministic authorization remains authoritative.

**### ML Risk Layer**

The ML component provides an additional security signal.

It can increase enforcement when suspicious conditions are detected, but it cannot:

\- override a deterministic \`BLOCK\`

\- bypass authorization

\- bypass resource ownership checks

\- bypass required human approval

This prevents the probabilistic ML component from becoming the primary authorization mechanism.

**---**

**## Machine Learning Risk Model**

The experimental classifier evaluates security-related features including:

\- unknown tool

\- high-risk tool

\- resource scope

\- assignment status

\- role/tool mismatch

\- malformed arguments

\- missing claim ID

\- sensitive document context

\- prompt-injection signal

\- unusual access volume

The trained model achieved approximately:

\| Metric | Result |

\|---|---:|

\| Accuracy | 93.44% |

\| Precision | 96.43% |

\| Recall | 92.61% |

\| F1-score | 94.48% |

\| False-positive rate | 5.28% |

\| False-negative rate | 7.39% |

These are experimental results produced using the synthetic/generated training and evaluation data used by this project.

They should **\*\*not\*\*** be interpreted as production security guarantees.

**---**

**## Human-in-the-Loop Security**

High-risk operations such as settlement approval cannot execute directly from an agent request.

The workflow is:

\`\`\`text

Agent proposes action

        |

        v

Security Gateway

        |

        v

HUMAN_REVIEW

        |

        v

Approval Request

        |

        v

Human Approval

        |

        v

Integrity Verification

        |

        v

Gateway Re-Authorization

        |

        v

Protected Tool

        |

        v

Approval marked EXECUTED

\`\`\`

An executed approval cannot be reused.

This provides replay protection for privileged operations.

**---**

**## Prompt-Injection Defense**

Aurelia includes adversarial documents containing instructions intended to manipulate the AI agent.

For example, a malicious document may attempt to instruct the agent to ignore the normal claims workflow and export customer information.

Document content is treated as data rather than security authority.

Even if an LLM proposes an unsafe action, the proposed tool call must still pass through the independent security gateway before execution.

The project's prompt-injection security tests demonstrate that suspicious requests can be classified as high or critical risk and blocked before protected execution.

**---**

**## Tamper-Evident Audit Logging**

Security events are stored in a hash-chained audit log.

Each event can contain:

\- event identity

\- timestamp

\- event type

\- agent identity

\- user identity and role

\- requested tool

\- arguments

\- security decision

\- deterministic risk level

\- ML risk information

\- execution status

\- associated approval ID

\- previous event hash

\- integrity hash

Each event contains the SHA-256 hash of its contents and references the previous event's hash.

Conceptually:

\`\`\`text

Event 1

  hash: H1

       |

       v

Event 2

  previous_hash: H1

  hash: H2

       |

       v

Event 3

  previous_hash: H2

  hash: H3

\`\`\`

Changing an existing event invalidates its integrity hash.

Changing or removing the chain relationship causes audit-chain verification to fail.

**---**

**## Local LLM Integration**

Aurelia integrates with a locally running LLM through Ollama.

The model can interpret a user request and propose a structured tool action.

For example:

\`\`\`json

{

  "tool_name": "get_claim",

  "arguments": {

    "claim_id": 1

  }

}

\`\`\`

The proposed action is not executed directly.

Instead:

\`\`\`text

Ollama

   |

   | proposed tool call

   v

Secure Agent

   |

   v

Hybrid Security Gateway

   |

   v

Protected Tool

\`\`\`

This means the LLM is used for reasoning and tool selection while security authority remains outside the model.

**---**

**## Project Structure**

\`\`\`text

agentic-ai-security-gateway/

│

├── demo_aurelia.py

├── run_all_tests.py

├── train_risk_model.py

├── requirements.txt

├── README.md

├── .gitignore

│

├── src/

│   ├── \_\_init\_\_.py

│   ├── approval.py

│   ├── approval_executor.py

│   ├── audit.py

│   ├── database.py

│   ├── hybrid_gateway.py

│   ├── hybrid_policy.py

│   ├── ml_risk.py

│   ├── models.py

│   ├── ollama_agent.py

│   ├── protected_tools.py

│   ├── secure_agent.py

│   ├── security_gateway.py

│   ├── seed_data.py

│   └── tools.py

│

├── tests/

│   └── security, ML, approval, audit and LLM integration tests

│

├── models/

│   └── risk_model.joblib

│

└── data/

    ├── aurelia_insurance.db

    ├── pending_approvals.jsonl

    └── security_audit.jsonl

\`\`\`

Generated model, database, approval and audit artifacts are excluded from version control where appropriate.

**---**

**## Installation**

Create and activate a Python virtual environment.

Install the project dependencies:

\`\`\`bash

pip install -r requirements.txt

\`\`\`

For LLM integration, install Ollama and ensure the Ollama service is running.

The main secure-agent integration was tested with:

\`\`\`text

lfm2.5-thinking:1.2b

\`\`\`

**---**

**## Train the ML Risk Model**

Run:

\`\`\`bash

python train_risk_model.py

\`\`\`

The model is stored locally at:

\`\`\`text

models/risk_model.joblib

\`\`\`

**---**

**## Run the Demonstration**

Run:

\`\`\`bash

python demo_aurelia.py

\`\`\`

The demonstration covers:

1\. Legitimate authorized access

2\. Unauthorized resource access

3\. Prompt-injection / ML risk

4\. High-risk human review

5\. Human-approved execution

6\. Approval replay prevention

7\. Audit-log integrity

**---**

**## Testing**

Individual tests can be executed independently:

\`\`\`bash

python -m tests.test_security_gateway

python -m tests.test_ml_risk

python -m tests.test_hybrid_enforcement

python -m tests.test_approval_security

python -m tests.test_audit_tampering

python -m tests.test_ollama_secure_agent

python -m tests.test_end_to_end_workflow

python -m tests.test_unified_audit

\`\`\`

The complete regression suite can also be executed with:

\`\`\`bash

python run_all_tests.py

\`\`\`

**### Final Regression Result**

The frozen project regression run produced:

\`\`\`text

Discovered: 31

Executed:   31

Passed:     31

Failed:     0

Skipped:    0

FINAL RESULT: ALL EXECUTED SECURITY TESTS PASSED

\`\`\`

This includes deterministic security, ML risk analysis, hybrid enforcement, approval security, tamper protection, audit integrity, secure-agent behaviour and Ollama integration.

**---**

**## Security Scenarios Verified**

The project tests demonstrate:

\- legitimate assigned-resource access

\- unauthorized tool blocking

\- unauthorized resource blocking

\- unknown-tool blocking

\- malformed-argument handling

\- missing-argument handling

\- ML risk classification

\- ML security escalation

\- ML fail-safe behaviour

\- hybrid deterministic + ML enforcement

\- prompt-injection defense

\- protected tool execution

\- high-risk human review

\- approval authorization

\- approval rejection

\- approval replay prevention

\- approval tampering detection

\- approval identity tampering detection

\- audit logging

\- audit-event tampering detection

\- audit hash-chain continuity

\- unified security auditing

\- LLM tool-call generation

\- enforcement of LLM-proposed actions through the gateway

**---**

**## Security Principle**

Aurelia deliberately separates AI reasoning from security authority:

\`\`\`text

AI Agent

   |

   | proposes

   v

Security Gateway

   |

   | authorizes

   v

Protected Tool

   |

   | executes

   v

Application State

\`\`\`

The AI model can propose an action.

It cannot grant itself permission to execute that action.

This architecture reduces the ability of prompt injection, incorrect reasoning or manipulated context to directly trigger privileged application operations.

**---**

**## Limitations**

Aurelia is a prototype and is not intended to represent a production insurance or cybersecurity system.

Current limitations include:

\- synthetic/generated ML training data

\- file-based approval storage

\- file-based audit logging

\- local development database

\- manually supplied prompt-injection risk signals in some tests

\- prototype identity and authentication assumptions

\- limited protected-tool set

\- no production key-management infrastructure

\- no cryptographic signing infrastructure

\- no external immutable audit service

\- ML performance has not been validated against real-world attack telemetry

These limitations provide directions for future development.

**---**

**## Future Work**

Potential extensions include:

\- authenticated user sessions

\- database-backed approval workflows

\- cryptographically signed approvals

\- external immutable audit storage

\- automated prompt-injection detection

\- anomaly detection using historical agent activity

\- rate limiting

\- policy-as-code integration

\- production monitoring and alerting

\- expanded adversarial evaluation

\- centralized identity and access management

\- production secret and key management

**---**


---

## Public Streamlit Demo

Aurelia supports a deployment-aware demonstration mode for hosted environments
such as Streamlit Community Cloud.

When a local Ollama service is available, natural-language interpretation uses
the configured local model. When Ollama is unavailable, the application falls
back to a deterministic demo interpreter for common claims requests.

The fallback changes only the natural-language interpretation layer. It does
**not** bypass or replace Aurelia's security controls. Proposed actions still
pass through the same deterministic authorization, ML risk analysis,
human-review workflow, protected-tool boundary, and audit logging.

The hosted version is a portfolio and educational demonstration. Its local
database and file-based audit/approval state should be treated as ephemeral
demo state, not durable production storage.


**## Disclaimer**

Aurelia is an educational and experimental security prototype.

It demonstrates architectural techniques for controlling agentic AI tool execution and should not be deployed as a production insurance, authorization or cybersecurity system without substantial additional engineering, security review and validation.