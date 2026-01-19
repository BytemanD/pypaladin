import subprocess

sources = ["src", "tests", "scripts"]

print("====== remove unused import =====")
subprocess.run(["ruff", "check", "--fix", "--select", "F401"] + sources, check=True)

print("====== format =====")
subprocess.run(["ruff", "format"] + sources, check=True)

print("====== ruff check and fix =====")
subprocess.run(["ruff", "check", "--fix"] + sources, check=True)
