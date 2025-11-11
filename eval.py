import os
import sys
import hashlib


ORIGINAL_FILE   = "C:\Col_projects\AdvDataCompression\DnaSequence\sequence(4).fasta"
COMPRESSED_FILE = "C:\Col_projects\AdvDataCompression\DnaSequence\sequence_4(1).bin"
RESTORED_FILE   = "C:\Col_projects\AdvDataCompression\DnaSequence\sequence_4_1_restored.fasta"



def get_dna_payload(filepath):
    """
    Reads a FASTA file and returns a single string of just the
    valid DNA bases (A, C, G, T), ignoring headers and whitespace.
    This is used to verify data integrity.
    """
    payload = []
    valid_bases = {'A', 'C', 'G', 'T'}
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.startswith('>'):
                    continue
                for char in line.strip().upper():
                    if char in valid_bases:
                        payload.append(char)
        return "".join(payload)
    except FileNotFoundError:
        print(f"Error: File not found at {filepath}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error reading {filepath}: {e}", file=sys.stderr)
        return None

def calculate_string_hash(text):
    """Returns the SHA-256 hash of a given string."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

print("="*60)
print("      Compression Analysis Report")
print("="*60)
print(f"Analyzing:")
print(f"  > Original:    {ORIGINAL_FILE}")
print(f"  > Compressed:  {COMPRESSED_FILE}")
print(f"  > Restored:    {RESTORED_FILE}")
print("-"*60)

all_files_found = True
for f in [ORIGINAL_FILE, COMPRESSED_FILE, RESTORED_FILE]:
    if not os.path.exists(f):
        print(f"\n\033[91mError: File not found: {f}\033[0m")
        all_files_found = False
        
if not all_files_found:
    sys.exit(1)


print("Analyzing data integrity (comparing DNA payloads)...")
original_payload = get_dna_payload(ORIGINAL_FILE)
restored_payload = get_dna_payload(RESTORED_FILE)

if original_payload is None or restored_payload is None:
    print("\033[91mCould not analyze integrity due to file read error.\033[0m")
    sys.exit(1)

original_hash = calculate_string_hash(original_payload)
restored_hash = calculate_string_hash(restored_payload)

is_lossless = original_hash == restored_hash

print(f"  > Original Payload Hash:  {original_hash[:10]}...")
print(f"  > Restored Payload Hash:  {restored_hash[:10]}...")

if is_lossless:
    print("\n\033[92mLOSSLESS:         PASS\033[0m")
    print("  > The DNA sequence data is identical.")
else:
    print("\n\033[91mLOSS:             FAIL\033[0m")
    print("  > The DNA sequence data is different!")
    
print("\033[0m" + "-"*60) 

print("Analyzing efficiency metrics...")

try:
    original_file_size = os.path.getsize(ORIGINAL_FILE)
    compressed_file_size = os.path.getsize(COMPRESSED_FILE)
    
    sequence_length = len(original_payload)

    if original_file_size == 0 or compressed_file_size == 0 or sequence_length == 0:
        raise ValueError("File size or sequence length is zero.")

    compression_ratio = original_file_size / compressed_file_size
    bits_per_base = (compressed_file_size * 8) / sequence_length

    print(f"  > Original File Size:   {original_file_size / 1e6:.3f} MB")
    print(f"  > Compressed File Size: {compressed_file_size / 1e6:.3f} MB")
    print(f"  > DNA Sequence Length:  {sequence_length:,} bases")
    print("."*30)
    print(f"  > Compression Ratio:    \033[96m{compression_ratio:.2f} x\033[0m")
    print(f"  > Bits per Base (bpb):  \033[96m{bits_per_base:.3f}\033[0m")
    print("="*60)

except ZeroDivisionError:
    print("\033[91mError: Cannot calculate metrics. File size or sequence length is zero.\033[0m")
except Exception as e:
    print(f"\033[91mAn error occurred during metric calculation: {e}\033[0m")