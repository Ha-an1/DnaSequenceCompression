# DNA-Compress: High-Order Genomic Compression

DNA-Compress is a high-performance, command-line utility designed for the **lossless compression of DNA sequences**. Unlike general-purpose compression tools (like gzip), this application is specifically engineered to exploit the statistical properties of genomic data (A, C, G, T) to achieve superior compression ratios.

---

##  Key Features

* **Adaptive Context Modeling**
  Learns the unique patterns of a DNA sequence in real-time to predict upcoming bases.

* **ANS Arithmetic Coding**
  Utilizes the high-performance `constriction` library for state-of-the-art entropy encoding.

* **Lossless Compression**
  Guarantees 100% bit-for-bit restoration of the original sequence.

* **FASTA Support**
  Intelligently parses FASTA files, ignoring headers and whitespace to focus purely on genomic data.

* **Two-Pass Efficiency**
  Implements an analysis-and-encoding strategy to ensure mathematical synchronization between compressor and decompressor.

---

##  Installation

### Prerequisites

* Python 3.8 or higher
* pip (Python package manager)

### Setup

1. Clone or download this repository.
2. Install required dependencies:

```bash
pip install constriction numpy
```

---

##  Usage

The tool operates in two modes: `compress` and `decompress`.

### Compressing a Sequence

To compress a DNA file (FASTA format):

```bash
python dna_compressor.py compress -i input_sequence.fasta -o compressed_data.bin
```

### Decompressing a Sequence

To restore a compressed file back to its original DNA string:

```bash
python dna_compressor.py decompress -i compressed_data.bin -o restored_sequence.fasta
```

---

##  How It Works

DNA-Compress uses a **"Brain and Engine" architecture**:

### 1️ The Brain (Context Model)

The algorithm examines a window of preceding bases (context). It tracks how often 'A', 'C', 'G', or 'T' follows specific patterns. As more data is processed, the model adapts and becomes highly accurate at predicting the next base in that genome.

### 2️ The Engine (Arithmetic Coder)

Using probabilities provided by the context model, the ANS-based arithmetic coder encodes the sequence into a compact representation. Predictable bases consume very little space, while rare or surprising bases use more bits.

---

##  Performance Expectations

Compression efficiency is measured in **Bits Per Base (bpb)**.

| Scenario             | Bits Per Base    | Notes                     |
| -------------------- | ---------------- | ------------------------- |
| Uncompressed DNA     | 2.000 bpb        | 2 bits needed for 4 bases |
| Standard Compression | ~1.75 – 1.85 bpb | Typical genomic sequences |
| Theoretical Limit    | ~1.5 – 1.6 bpb   | Highly repetitive genomes |

### Expected File Size Behavior

| File Size    | Expected Result    | Reason                                       |
| ------------ | ------------------ | -------------------------------------------- |
| < 50 KB      | Larger file        | Model overhead outweighs compression benefit |
| 1 MB – 10 MB | ~10–20% savings    | Model learns genome structure effectively    |
| > 100 MB     | Maximum efficiency | Best results on large chromosomes/genomes    |

---

##  Testing

To verify lossless integrity:

1. Compress a known FASTA file.
2. Decompress the resulting `.bin` file.
3. Compare original and restored files:

```bash
diff original.fasta restored.fasta
```

Windows:

```bash
fc original.fasta restored.fasta
```
If the command returns no output, the compression was perfectly lossless.

