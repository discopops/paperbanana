# Multi-Format Input/Output Usage Guide

PaperBanana now supports multiple input document formats and output image formats, making it easier to work with academic papers and generate publication-ready outputs.

## Quick Start

### Basic Usage (Unchanged)

The original text → PNG workflow continues to work exactly as before:

```bash
paperbanana generate \
  --input method.txt \
  --caption "Overview of our framework"
```

### PDF Input with Auto-Detection

```bash
paperbanana generate \
  --input paper.pdf \
  --caption "System architecture diagram"
```

PaperBanana will:
1. Auto-detect the PDF format
2. Extract the methodology section automatically
3. Generate a diagram and save as PNG (default)

### Multi-Format Export

Generate multiple formats in a single run:

```bash
paperbanana generate \
  --input paper.pdf \
  --caption "Figure 1: Proposed framework" \
  --export-formats png,svg,pdf,tikz
```

This creates:
- `output.png` — Raster image (default quality)
- `output.svg` — Vector format (scalable)
- `output.pdf` — PDF document (for publications)
- `output.tex` — LaTeX/TikZ code (for embedding in papers)

## Input Formats

### Supported Formats

| Format | Extension | Auto-Extract Methodology? | Dependencies |
|--------|-----------|---------------------------|--------------|
| Plain Text | `.txt`, `.text` | No (full content) | None (built-in) |
| PDF | `.pdf` | Yes (rule-based) | `pip install paperbanana[pdf]` |
| Markdown | `.md`, `.markdown` | Yes (header-based) | None (built-in) |
| HTML | `.html`, `.htm` | No (main content) | `pip install paperbanana[html]` |
| Word | `.docx` | Yes (heading-based) | `pip install paperbanana[docx]` |

### PDF Input Examples

**Auto-extract methodology section:**
```bash
paperbanana generate --input neurips_paper.pdf --caption "Architecture"
```

**Use full PDF text (no extraction):**
```bash
paperbanana generate \
  --input paper.pdf \
  --caption "Overview" \
  --no-extract-methodology
```

**Use VLM for intelligent extraction (slower, more accurate):**
```bash
paperbanana generate \
  --input complex_paper.pdf \
  --caption "Overview" \
  --use-vlm-extraction
```

### Markdown Input

```bash
paperbanana generate \
  --input README.md \
  --caption "Project architecture"
```

Auto-detects `## Methodology` or `## Approach` sections.

### HTML Input

```bash
paperbanana generate \
  --input article.html \
  --caption "System overview"
```

Extracts main content, removing navigation and boilerplate.

### Word Document Input

```bash
paperbanana generate \
  --input thesis_chapter.docx \
  --caption "Research methodology"
```

Uses heading styles to identify methodology section.

## Output Formats

### Supported Formats

| Format | Extension | Use Case | Dependencies |
|--------|-----------|----------|--------------|
| PNG | `.png` | Web, presentations | None (built-in) |
| SVG | `.svg` | Scalable vector graphics | None (built-in) |
| PDF | `.pdf` | Print publications | `pip install paperbanana[export-pdf]` |
| TIFF | `.tiff` | High-resolution print | None (built-in) |
| TikZ | `.tex` | LaTeX papers | Requires VLM |

### Export Format Examples

**High-DPI for print:**
```bash
paperbanana generate \
  --input method.txt \
  --caption "Framework" \
  --export-formats png,tiff \
  --export-dpi 600
```

**Presentation-ready:**
```bash
paperbanana generate \
  --input paper.pdf \
  --caption "Overview" \
  --export-formats png,svg
```

**LaTeX paper workflow:**
```bash
paperbanana generate \
  --input paper.pdf \
  --caption "Figure 1: Proposed methodology" \
  --export-formats pdf,tikz
```

Then in your LaTeX document:
```latex
\begin{figure}[ht]
  \centering
  \input{output.tex}  % TikZ code
  \caption{Proposed methodology}
\end{figure}
```

## Installation

### Basic Installation (Text + PNG only)

```bash
pip install paperbanana
```

### With All Format Support

```bash
pip install paperbanana[all-formats]
```

### Individual Format Support

```bash
# PDF input
pip install paperbanana[pdf]

# HTML input
pip install paperbanana[html]

# Word documents
pip install paperbanana[docx]

# PDF export
pip install paperbanana[export-pdf]
```

## Python API

### Loading Documents

```python
from paperbanana.loaders.registry import LoaderRegistry
from paperbanana.core.types import LoaderConfig

# Auto-detect format
loader = LoaderRegistry.auto_detect("paper.pdf")
config = LoaderConfig(extract_methodology=True)
load_result = await loader.load("paper.pdf", config)

source_context = load_result.source_context
```

### Exporting to Multiple Formats

```python
from paperbanana.exporters.registry import ExporterRegistry
from paperbanana.core.types import ExportConfig
from PIL import Image

# Load generated image
image = Image.open("generated_diagram.png")

# Export to multiple formats
formats = ["png", "svg", "pdf"]
export_config = ExportConfig(dpi=600)

for fmt in formats:
    exporter = ExporterRegistry.create(fmt)
    await exporter.export(image, f"output.{fmt}", export_config)
```

### Complete Workflow

```python
from pathlib import Path
from paperbanana.core.pipeline import PaperBananaPipeline
from paperbanana.core.config import Settings
from paperbanana.core.types import GenerationInput, DiagramType
from paperbanana.loaders.registry import LoaderRegistry
from paperbanana.exporters.registry import ExporterRegistry

# Load document
loader = LoaderRegistry.auto_detect("paper.pdf")
load_result = await loader.load("paper.pdf")

# Generate diagram
settings = Settings()
pipeline = PaperBananaPipeline(settings=settings)

gen_input = GenerationInput(
    source_context=load_result.source_context,
    communicative_intent="System architecture",
    diagram_type=DiagramType.METHODOLOGY
)

result = await pipeline.generate(gen_input)

# Export to multiple formats
from PIL import Image
image = Image.open(result.image_path)

for fmt in ["png", "svg", "pdf", "tikz"]:
    exporter = ExporterRegistry.create(fmt)
    await exporter.export(
        image,
        Path(result.image_path).with_suffix(exporter.file_extension)
    )
```

## Batch Processing

Generate multiple diagrams from a single paper:

```python
from paperbanana.loaders.pdf import PDFLoader

# Load paper once
loader = PDFLoader()
load_result = await loader.load("neurips_paper.pdf")

captions = {
    "architecture": "System architecture overview",
    "pipeline": "Two-phase processing pipeline",
    "evaluation": "Evaluation methodology"
}

for name, caption in captions.items():
    result = await pipeline.generate(
        GenerationInput(
            source_context=load_result.source_context,
            communicative_intent=caption
        )
    )

    # Export each diagram
    image = Image.open(result.image_path)
    for fmt in ["pdf", "tikz"]:
        exporter = ExporterRegistry.create(fmt)
        await exporter.export(
            image,
            Path(f"figures/{name}.{exporter.file_extension}")
        )
```

## Troubleshooting

### Missing Dependencies

If you see an error like:
```
PDF loading requires pymupdf. Install with: pip install paperbanana[pdf]
```

Simply install the required dependency:
```bash
pip install paperbanana[pdf]
```

### PDF Methodology Extraction Failed

If the automatic extraction doesn't find the methodology section:

1. Try VLM-based extraction:
   ```bash
   paperbanana generate --input paper.pdf --caption "..." --use-vlm-extraction
   ```

2. Or use the full text:
   ```bash
   paperbanana generate --input paper.pdf --caption "..." --no-extract-methodology
   ```

3. Or manually extract to a text file and use that:
   ```bash
   paperbanana generate --input methodology.txt --caption "..."
   ```

### TikZ Export Quality

TikZ export uses VLM to generate LaTeX code from the image. This is a best-effort approach:

- **For simple diagrams:** Usually generates clean, compilable code
- **For complex diagrams:** May require manual refinement
- **Tip:** Check the generated `.tex` file and adjust as needed

## Format Availability Check

Check which formats are available:

```python
from paperbanana.loaders.registry import LoaderRegistry
from paperbanana.exporters.registry import ExporterRegistry

# Input formats
print("Available input formats:")
for name, display in LoaderRegistry.get_available_formats().items():
    print(f"  {name}: {display}")

# Output formats
print("\nAvailable export formats:")
for name, display in ExporterRegistry.get_available_formats().items():
    print(f"  {name}: {display}")

# Missing dependencies
unavailable = LoaderRegistry.get_unavailable_formats()
if unavailable:
    print("\nUnavailable formats (missing dependencies):")
    for name, hint in unavailable.items():
        print(f"  {name}: {hint}")
```

## Migration Guide

### From Previous Versions

**No changes required!** Your existing workflows continue to work:

```bash
# This still works exactly as before
paperbanana generate --input method.txt --caption "Overview"
```

To adopt new features gradually:

1. **Try PDF input:**
   ```bash
   paperbanana generate --input paper.pdf --caption "Overview"
   ```

2. **Add export formats:**
   ```bash
   paperbanana generate --input paper.pdf --caption "..." --export-formats png,pdf
   ```

3. **Enable VLM extraction for complex papers:**
   ```bash
   paperbanana generate --input paper.pdf --caption "..." --use-vlm-extraction
   ```

## Best Practices

1. **PDF Input:** Let auto-extraction work first, only use VLM extraction if needed
2. **Export Formats:** Export to SVG/PDF for publications, PNG for web/presentations
3. **High DPI:** Use `--export-dpi 600` for print-quality outputs
4. **Batch Processing:** Use Python API to process multiple diagrams from one paper
5. **TikZ:** Review and refine generated LaTeX code before including in papers

## Examples

See `examples/` directory for complete working examples:
- `examples/pdf_to_multiformat.py` — Load PDF and export to all formats
- `examples/batch_generation.py` — Generate multiple diagrams from one paper
- `examples/markdown_input.py` — Use Markdown documentation as input
