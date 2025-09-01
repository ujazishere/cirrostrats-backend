def validate_gate_returns(data):
    # Validate gates - given a list of gates
    valid_keys = [f"A{i}" for i in range(1, 31)] + [f"C{i}" for i in range(69, 140)]
    for key in data:
        if key not in valid_keys:
            print(f"Invalid key: {key}")
            # Handle invalid key, e.g., remove it from the data
