![tokens](https://github.com/user-attachments/assets/7f03a0ff-c779-4e81-8adc-c05ed44107f4)


# EPUB Token Counter

A Python GUI application that helps you analyze, organize, and filter EPUB files based on their token counts. This tool is particularly useful for managing large EPUB collections and preparing texts for AI language model training or analysis.

In fact, it was created to identify those epub files that I could fit into an LLM based on token size. Some accept only 32k, others 128k, etc. I wanted to be able to quickly identify which epubs would work with which LLM.

## Features

- **Token Counting**: Accurately counts tokens in EPUB files using the OpenAI tiktoken library (cl100k_base encoding)
- **Multiple Operation Modes**:
  - Count Only: Generate a CSV report of token counts without moving files
  - Copy Files: Copy files under a specified token limit to a destination folder
  - Move Files: Move files under a specified token limit to a destination folder
- **Batch Processing**: Process entire folders of EPUB files, including subfolders
- **Progress Tracking**: Visual progress bar and detailed completion reports
- **CSV Reports**: Generates detailed reports including file titles, token counts, and processing status
- **Settings Persistence**: Remembers your last used folders and token count
- **Safety Features**: 
  - File size limits to prevent memory issues
  - Confirmation prompts for potentially destructive operations
  - Detailed logging for troubleshooting

## Why Use This Tool?

1. **AI Training Preparation**: When preparing texts for AI language model training, you often need to filter documents based on token count. This tool automates that process.

2. **Content Management**: Helps organize large EPUB collections by size/complexity (as measured by token count).

3. **Cost Estimation**: When using API services that charge by token count, this tool helps estimate costs by providing accurate token counts.

4. **Library Organization**: Easily separate large and small texts, or identify texts that fit within specific token limits.

## Installation

1. Clone this repository:
git clone https://github.com/j816/epubtokens.git

2. Install required dependencies:
pip install PyQt5 ebooklib tiktoken

## Usage

1. Run the application:
python epubtokens.py


2. Select an operation mode:
   - **Count Only**: Just counts tokens and generates a report
   - **Copy Files**: Copies files under the token limit to destination
   - **Move Files**: Moves files under the token limit to destination

3. Choose your source folder containing EPUB files

4. Enter your maximum token count

5. If copying or moving files, select a destination folder

6. Click "Start" to begin processing

## Output

The tool generates a CSV report containing:
- Book titles
- Token counts
- File paths
- Processing status ("Within Limit" or "Exceeds Limit")

CSV files are named with timestamps for easy reference: `epub_token_counts_YYYYMMDD_HHMMSS.csv`

## Technical Details

- Uses the `tiktoken` library with `cl100k_base` encoding for accurate token counting
- Processes EPUB files using the `ebooklib` library
- Built with PyQt5 for the graphical interface
- Includes a 100MB file size limit for safety
- Processes files in 8KB chunks for memory efficiency

## Limitations

- Only processes EPUB format files
- Large files (>100MB) are skipped for safety
- Token counting uses OpenAI's cl100k_base encoding, which may not match other tokenizers

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT

## Acknowledgments

- Uses OpenAI's `tiktoken` library for token counting
- Built with `ebooklib` for EPUB processing
