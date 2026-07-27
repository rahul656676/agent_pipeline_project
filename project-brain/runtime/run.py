import subprocess
import sys

def main():
    print("Project Brain v2 Runtime Executor")
    print("Running tests...")
    res = subprocess.run([sys.executable, "-m", "pytest", "tests/test_pipeline.py", "-v"])
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
