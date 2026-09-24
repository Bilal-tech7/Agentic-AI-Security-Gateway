from src.tools import (
    get_customer,
    get_policy,
    get_claim,
    get_claim_documents,
    get_claim_history
)


print("\n========================================")
print("AURELIA INSURANCE TOOL TEST")
print("========================================\n")


# ------------------------------------------------------------
# Test 1: Customer
# ------------------------------------------------------------

print("TEST 1: Get Customer")

customer_result = get_customer(1)

print(customer_result)


# ------------------------------------------------------------
# Test 2: Policy
# ------------------------------------------------------------

print("\nTEST 2: Get Policy")

policy_result = get_policy(1)

print(policy_result)


# ------------------------------------------------------------
# Test 3: Claim
# ------------------------------------------------------------

print("\nTEST 3: Get Claim")

claim_result = get_claim(1)

print(claim_result)


# ------------------------------------------------------------
# Test 4: Claim Documents
# ------------------------------------------------------------

print("\nTEST 4: Get Claim Documents")

documents_result = get_claim_documents(1)

print(documents_result)


# ------------------------------------------------------------
# Test 5: Claim History
# ------------------------------------------------------------

print("\nTEST 5: Get Customer Claim History")

history_result = get_claim_history(1)

print(history_result)


print("\n========================================")
print("TESTS COMPLETE")
print("========================================")