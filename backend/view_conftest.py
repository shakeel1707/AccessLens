with open(r'C:\Users\Shakeel\OneDrive\Desktop\New folder\backend\tests\e2e\conftest.py', 'r') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[:40], 1):
        print(f"{i:3d}: {line.rstrip()}")
