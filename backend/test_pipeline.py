from rag_pipeline import ask_clinical_question


question = (
    "What HbA1c target should adults with "
    "type 1 diabetes generally aim for?"
)


result = ask_clinical_question(question)


print("\nANSWER:")
print(result["answer"])

print("\nCONFIDENCE:")
print(result["confidence"])

print("\nCITATIONS:")
print(result["citations"])

print("\nEVIDENCE:")
print(result["evidence"])

print("\nSCHEMA VALID:")
print(result["is_schema_valid"])