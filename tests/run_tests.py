import subprocess
import sys

def run():
    print("Running pytest suite...")
    # Run pytest and capture stdout and stderr
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-v", "--tb=short"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Print the full output so it remains in the console logs
    print(result.stdout)
    if result.stderr:
        print("=== STDERR ===")
        print(result.stderr, file=sys.stderr)
        
    if result.returncode != 0:
        # Extract failures section to print as a GitHub Action error annotation
        output = result.stdout
        failures_marker = "============================= FAILURES ============================="
        failures_idx = output.find(failures_marker)
        
        if failures_idx != -1:
            failures_text = output[failures_idx:]
        else:
            # Fallback to the last 2000 characters if marker isn't found
            failures_text = output[-2000:]
            
        # Format the text for GitHub Actions annotation (escape newlines)
        escaped_text = failures_text.replace("\n", "%0A").replace("\r", "")
        print(f"::error title=Pytest Failures Summary::{escaped_text}")
        
    sys.exit(result.returncode)

if __name__ == "__main__":
    run()
