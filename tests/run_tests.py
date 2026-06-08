import subprocess
import sys
import urllib.request

def run():
    print("Running pytest suite...")
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
        full_log = result.stdout
        if result.stderr:
            full_log += "\n=== STDERR ===\n" + result.stderr
            
        # Attempt to upload to paste.rs
        try:
            req = urllib.request.Request(
                "https://paste.rs",
                data=full_log.encode("utf-8"),
                headers={"Content-Type": "text/plain", "User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req) as response:
                paste_url = response.read().decode("utf-8").strip()
            print(f"\nUploaded test failures to: {paste_url}")
            # Output short error annotation with the URL
            print(f"::error title=Pytest Failures Link::Click here to view full test logs: {paste_url}")
        except Exception as e:
            print(f"Failed to upload logs to paste.rs: {e}")
            # Fallback to local printing
            print(f"::error title=Pytest Failures::Tests failed with exit code {result.returncode}")
            
    sys.exit(result.returncode)

if __name__ == "__main__":
    run()
