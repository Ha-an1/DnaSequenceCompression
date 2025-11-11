import sys
import argparse
import time
from collections import deque
import numpy as np
import constriction

CONTEXT_LENGTH = 10
DNA_ALPHABET = ['A', 'C', 'G', 'T']
BASE_TO_INDEX = {base: i for i, base in enumerate(DNA_ALPHABET)}
INDEX_TO_BASE = {i: base for i, base in enumerate(DNA_ALPHABET)}


class ContextModel:

    def __init__(self, context_length, alphabet_size):
        self.context_length = context_length
        self.alphabet_size = alphabet_size
        self.model = {}

    def _get_or_create_context(self, context):
        if context not in self.model:
            self.model[context] = np.ones(self.alphabet_size, dtype=np.uint32)
        return self.model[context]

    def update(self, context, symbol_index):
        counts = self._get_or_create_context(context)
        counts[symbol_index] += 1

    def get_probabilities(self, context):
        counts = self._get_or_create_context(context)
        total_count = np.sum(counts)
        return counts / total_count


def read_fasta_sequence_and_header(filepath):

    try:
        with open(filepath, 'r') as f:
            header = ""
            for line in f:
                if line.startswith('>'):
                    header = line.strip()
                    yield ("HEADER", header)
                    break 

            for line in f:
                if line.startswith('>'): 
                    continue
                for char in line.strip().upper():
                    if char in BASE_TO_INDEX:
                        yield ("BASE", char)
    except FileNotFoundError:
        print(f"Error: Input file not found at {filepath}", file=sys.stderr)
        sys.exit(1)


def compress_file(input_path, output_path):

    print(f"Reading and preparing sequence from '{input_path}'...")
    
    header = ""
    sequence = []
    for type, data in read_fasta_sequence_and_header(input_path):
        if type == "HEADER":
            header = data
        else:
            sequence.append(data)

    seq_len = len(sequence)

    if seq_len == 0:
        print("Warning: Input file is empty. Creating empty output file.")
        with open(output_path, 'wb') as f:
            f.write(b'\x00\x00\x00\x00\x00\x00\x00\x00') 
        return

    print(f"Read FASTA header: {header}")
    print(f"Sequence length: {seq_len:,} bases.")
    print(f"Initializing context model (k={CONTEXT_LENGTH})...")

    model = ContextModel(CONTEXT_LENGTH, len(DNA_ALPHABET))
    context_queue = deque(['N'] * CONTEXT_LENGTH, maxlen=CONTEXT_LENGTH)
    
    print("Pass 1/2: Analyzing sequence and generating probabilities...")
    start_time = time.time()
    states_to_encode = []

    for base in sequence:
        context_str = "".join(context_queue)
        probabilities = model.get_probabilities(context_str)
        symbol_index = BASE_TO_INDEX[base]
        states_to_encode.append((symbol_index, probabilities))
        model.update(context_str, symbol_index)
        context_queue.append(base)

    pass1_end_time = time.time()
    print(f"Analysis complete in {pass1_end_time - start_time:.3f} seconds.")

    print("Pass 2/2: Encoding data...")
    encoder = constriction.stream.stack.AnsCoder()

    for symbol_index, probabilities in reversed(states_to_encode):
        distribution = constriction.stream.model.Categorical(probabilities)
        encoder.encode_reverse(np.array([symbol_index], dtype=np.int32), distribution)

    compressed_data = encoder.get_compressed()
    pass2_end_time = time.time()
    print(f"Encoding complete in {pass2_end_time - pass1_end_time:.3f} seconds.")
    
    header_bytes = header.encode('utf-8')

    with open(output_path, 'wb') as f:
        f.write(seq_len.to_bytes(8, 'big'))
        f.write(len(header_bytes).to_bytes(2, 'big'))
        f.write(header_bytes)
        f.write(np.array(compressed_data, dtype=np.uint32).tobytes())
    
    original_size_bytes = len(sequence) / 4 # Roughly 2 bits per base
    compressed_size_bytes = len(compressed_data) * 4 + 10 + len(header_bytes)

    print("\n--- Compression Summary ---")
    print(f"Total time elapsed: {pass2_end_time - start_time:.3f} seconds.")
    '''    print(f"Original sequence size (payload): {original_size_bytes / 1e6:.3f} MB")
    print(f"Compressed file size: {compressed_size_bytes / 1e6:.3f} MB")
    if compressed_size_bytes > 0 and original_size_bytes > 0:
        ratio = original_size_bytes / compressed_size_bytes
        bits_per_base = (compressed_size_bytes * 8) / seq_len
        print(f"Compression ratio: {ratio:.2f}x")
        print(f"Bits per base (including header overhead): {bits_per_base:.3f}")'''
    print("-------------------------\n")


def decompress_file(input_path, output_path):

    print(f"Reading compressed file '{input_path}'...")
    try:
        with open(input_path, 'rb') as f:
            seq_len = int.from_bytes(f.read(8), 'big')
            header_len = int.from_bytes(f.read(2), 'big')
            header = f.read(header_len).decode('utf-8')
            compressed_data = np.frombuffer(f.read(), dtype=np.uint32)
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}", file=sys.stderr)
        sys.exit(1)

    if seq_len == 0:
        with open(output_path, 'w') as f: f.write(header)
        return

    print(f"Restoring FASTA header: {header}")
    print(f"Original sequence length: {seq_len:,} bases.")
    print(f"Initializing context model (k={CONTEXT_LENGTH})...")

    model = ContextModel(CONTEXT_LENGTH, len(DNA_ALPHABET))
    decoder = constriction.stream.stack.AnsCoder(compressed_data)
    context_queue = deque(['N'] * CONTEXT_LENGTH, maxlen=CONTEXT_LENGTH)
    
    print("Decompressing...")
    start_time = time.time()
    
    decoded_sequence = []

    for _ in range(seq_len):
        context_str = "".join(context_queue)
        probabilities = model.get_probabilities(context_str)
        distribution = constriction.stream.model.Categorical(probabilities)
        
        symbol_index = decoder.decode(distribution, 1)[0]
        
        model.update(context_str, symbol_index)
        
        base = INDEX_TO_BASE[symbol_index]
        decoded_sequence.append(base)
        context_queue.append(base)


    restored_sequence = "".join(decoded_sequence)

    with open(output_path, 'w') as f:
        f.write(header + '\n')
        for i in range(0, len(restored_sequence), 70):
            f.write(restored_sequence[i:i+70] + '\n')

    end_time = time.time()
    
    print("\n--- Decompression Summary ---")
    print(f"Time elapsed: {end_time - start_time:.3f} seconds.")
    print(f"Decompression successful! Restored to '{output_path}'.")
    print("---------------------------\n")


def main():
    parser = argparse.ArgumentParser(
        description="A DNA compression tool using a high-order context model.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parser_c = subparsers.add_parser("compress", help="Compress a DNA file.")
    parser_c.add_argument("-i", "--input", required=True, help="Input DNA file (FASTA format).")
    parser_c.add_argument("-o", "--output", required=True, help="Output path for the compressed file.")

    parser_d = subparsers.add_parser("decompress", help="Decompress a file.")
    parser_d.add_argument("-i", "--input", required=True, help="Input compressed file.")
    parser_d.add_argument("-o", "--output", required=True, help="Output path for the restored DNA file.")

    args = parser.parse_args()

    if args.command == "compress":
        compress_file(args.input, args.output)
    elif args.command == "decompress":
        decompress_file(args.input, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()