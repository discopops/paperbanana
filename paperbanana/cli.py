"""PaperBanana CLI — Generate publication-quality academic illustrations."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

from paperbanana.core.config import Settings
from paperbanana.core.types import DiagramType, GenerationInput

app = typer.Typer(
    name="paperbanana",
    help="Generate publication-quality academic illustrations from text.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def generate(
    input: str = typer.Option(..., "--input", "-i", help="Path to input document"),
    caption: str = typer.Option(
        ..., "--caption", "-c", help="Figure caption / communicative intent"
    ),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output image path"),
    # Input format options
    input_format: Optional[str] = typer.Option(
        None,
        "--input-format",
        help="Input format (auto-detected if not specified): text, pdf, markdown, html, docx",
    ),
    extract_methodology: bool = typer.Option(
        True, "--extract-methodology/--no-extract-methodology", help="Auto-extract methodology section"
    ),
    use_vlm_extraction: bool = typer.Option(
        False, "--use-vlm-extraction", help="Use VLM for intelligent section extraction (slower)"
    ),
    # Export format options
    export_formats: str = typer.Option(
        "png", "--export-formats", help="Comma-separated export formats: png, svg, pdf, tiff, tikz"
    ),
    export_dpi: int = typer.Option(300, "--export-dpi", help="DPI for raster exports"),
    # Pipeline options
    vlm_provider: Optional[str] = typer.Option(
        None, "--vlm-provider", help="VLM provider (gemini)"
    ),
    vlm_model: Optional[str] = typer.Option(None, "--vlm-model", help="VLM model name"),
    image_provider: Optional[str] = typer.Option(
        None, "--image-provider", help="Image gen provider"
    ),
    image_model: Optional[str] = typer.Option(None, "--image-model", help="Image gen model name"),
    iterations: Optional[int] = typer.Option(
        None, "--iterations", "-n", help="Refinement iterations"
    ),
    config: Optional[str] = typer.Option(None, "--config", help="Path to config YAML file"),
    # Agentic vision options
    enable_agentic_vision: bool = typer.Option(
        False,
        "--enable-agentic-vision",
        help="Enable agentic vision for both planning & critique (requires Gemini 3 Flash)",
    ),
    enable_reference_analysis: bool = typer.Option(
        False,
        "--enable-reference-analysis",
        help="Enable reference pattern analysis (planning phase only)",
    ),
    enable_visual_analysis: bool = typer.Option(
        False,
        "--enable-visual-analysis",
        help="Enable visual analysis (critique phase only)",
    ),
    agentic_vision_model: Optional[str] = typer.Option(
        None,
        "--agentic-vision-model",
        help="Model for agentic vision (default: gemini-3-flash-preview)",
    ),
):
    """Generate a methodology diagram from a document."""
    # Load input document using appropriate loader
    input_path = Path(input)
    if not input_path.exists():
        console.print(f"[red]Error: Input file not found: {input}[/red]")
        raise typer.Exit(1)

    from paperbanana.core.types import LoaderConfig
    from paperbanana.loaders.registry import LoaderRegistry

    # Auto-detect or use explicit format
    if input_format:
        try:
            loader = LoaderRegistry.create(input_format)
            console.print(f"[dim]Using {loader.format_name} loader[/dim]")
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)
    else:
        try:
            loader = LoaderRegistry.auto_detect(input_path)
            console.print(f"[dim]Auto-detected format: {loader.format_name}[/dim]")
        except ValueError as e:
            console.print(f"[red]Error: {e}[/red]")
            raise typer.Exit(1)

    # Load document
    loader_config = LoaderConfig(
        extract_methodology=extract_methodology,
        use_vlm_extraction=use_vlm_extraction,
    )

    async def _load_document():
        return await loader.load(input_path, loader_config)

    try:
        load_result = asyncio.run(_load_document())
        source_context = load_result.source_context

        # Show extraction metadata
        if load_result.metadata.get("extraction_method") == "rule_based":
            console.print("[dim]Extracted methodology section using rule-based detection[/dim]")
        elif load_result.metadata.get("extraction_method") == "section_extraction":
            console.print("[dim]Extracted methodology section from document structure[/dim]")
        elif load_result.metadata.get("extraction_method") == "vlm_based":
            console.print("[dim]Extracted methodology section using VLM[/dim]")

    except Exception as e:
        console.print(f"[red]Error loading document: {e}[/red]")
        raise typer.Exit(1)

    # Build settings — only override values explicitly passed via CLI
    overrides = {}
    if vlm_provider:
        overrides["vlm_provider"] = vlm_provider
    if vlm_model:
        overrides["vlm_model"] = vlm_model
    if image_provider:
        overrides["image_provider"] = image_provider
    if image_model:
        overrides["image_model"] = image_model
    if iterations is not None:
        overrides["refinement_iterations"] = iterations
    if output:
        overrides["output_dir"] = str(Path(output).parent)

    # Agentic vision settings
    if enable_agentic_vision:
        # Convenience flag: enable both planning and critique
        overrides["planner_enable_reference_analysis"] = True
        overrides["critic_enable_visual_analysis"] = True
        if agentic_vision_model:
            overrides["planner_reference_analysis_model"] = agentic_vision_model
            overrides["critic_visual_analysis_model"] = agentic_vision_model

    # Individual control flags (override convenience flag if specified)
    if enable_reference_analysis:
        overrides["planner_enable_reference_analysis"] = True
    if enable_visual_analysis:
        overrides["critic_enable_visual_analysis"] = True

    if config:
        settings = Settings.from_yaml(config, **overrides)
    else:
        from dotenv import load_dotenv

        load_dotenv()
        settings = Settings(**overrides)

    # Build generation input
    gen_input = GenerationInput(
        source_context=source_context,
        communicative_intent=caption,
        diagram_type=DiagramType.METHODOLOGY,
    )

    # Build panel info
    panel_info = (
        f"[bold]PaperBanana[/bold] - Generating Methodology Diagram\n\n"
        f"VLM: {settings.vlm_provider} / {settings.vlm_model}\n"
        f"Image: {settings.image_provider} / {settings.image_model}\n"
        f"Iterations: {settings.refinement_iterations}"
    )

    # Add agentic vision status
    agentic_features = []
    if settings.planner_enable_reference_analysis:
        agentic_features.append("Reference Analysis (Planning)")
    if settings.critic_enable_visual_analysis:
        agentic_features.append("Visual Analysis (Critique)")
    if agentic_features:
        panel_info += f"\nAgentic Vision: {', '.join(agentic_features)}"

    console.print(Panel.fit(panel_info, border_style="blue"))

    # Run pipeline
    from paperbanana.core.pipeline import PaperBananaPipeline

    async def _run():
        pipeline = PaperBananaPipeline(settings=settings)
        return await pipeline.generate(gen_input)

    with Progress(
        SpinnerColumn(spinner_name="line"),  # ASCII-safe spinner for Windows compatibility
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        progress.add_task("Generating diagram...", total=None)
        result = asyncio.run(_run())

    console.print(f"\n[green]Done![/green] Output saved to: [bold]{result.image_path}[/bold]")
    console.print(f"Run ID: {result.metadata.get('run_id', 'unknown')}")
    console.print(f"Total iterations: {len(result.iterations)}")

    # Export to additional formats if requested
    requested_formats = [fmt.strip().lower() for fmt in export_formats.split(",")]

    # Only export if formats other than PNG are requested (PNG is already saved)
    additional_formats = [fmt for fmt in requested_formats if fmt != "png"]

    if additional_formats:
        console.print("\n[bold]Exporting to additional formats...[/bold]")

        from PIL import Image

        from paperbanana.core.types import ExportConfig
        from paperbanana.exporters.registry import ExporterRegistry
        from paperbanana.providers.registry import ProviderRegistry

        # Load the generated image
        final_image = Image.open(result.image_path)
        base_output_path = Path(result.image_path)

        # Export to each requested format
        export_config = ExportConfig(dpi=export_dpi)

        for fmt in additional_formats:
            try:
                exporter = ExporterRegistry.create(fmt)

                # Special handling for TikZ (needs VLM)
                if fmt == "tikz" and hasattr(exporter, "vlm"):
                    exporter.vlm = ProviderRegistry.create_vlm(settings)

                # Determine output path
                output_path = base_output_path.with_suffix(exporter.file_extension)

                # Export
                async def _export():
                    return await exporter.export(final_image, output_path, export_config)

                exported_path = asyncio.run(_export())
                console.print(f"  ✓ [green]{fmt.upper()}[/green]: {exported_path}")

            except ValueError as e:
                console.print(f"  ✗ [yellow]{fmt.upper()}[/yellow]: {e}")
            except Exception as e:
                console.print(f"  ✗ [red]{fmt.upper()}[/red]: Unexpected error: {e}")


@app.command()
def plot(
    data: str = typer.Option(..., "--data", "-d", help="Path to data file (CSV or JSON)"),
    intent: str = typer.Option(..., "--intent", help="Communicative intent for the plot"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output image path"),
    vlm_provider: str = typer.Option("gemini", "--vlm-provider", help="VLM provider"),
    iterations: int = typer.Option(3, "--iterations", "-n", help="Number of refinement iterations"),
):
    """Generate a statistical plot from data."""
    data_path = Path(data)
    if not data_path.exists():
        console.print(f"[red]Error: Data file not found: {data}[/red]")
        raise typer.Exit(1)

    # Load data
    import json as json_mod

    if data_path.suffix == ".csv":
        import pandas as pd

        df = pd.read_csv(data_path)
        raw_data = df.to_dict(orient="records")
        source_context = (
            f"CSV data with columns: {list(df.columns)}\n"
            f"Rows: {len(df)}\nSample:\n{df.head().to_string()}"
        )
    else:
        with open(data_path) as f:
            raw_data = json_mod.load(f)
        source_context = f"JSON data:\n{json_mod.dumps(raw_data, indent=2)[:2000]}"

    from dotenv import load_dotenv

    load_dotenv()

    settings = Settings(
        vlm_provider=vlm_provider,
        refinement_iterations=iterations,
    )

    gen_input = GenerationInput(
        source_context=source_context,
        communicative_intent=intent,
        diagram_type=DiagramType.STATISTICAL_PLOT,
        raw_data={"data": raw_data},
    )

    console.print(
        Panel.fit(
            f"[bold]PaperBanana[/bold] - Generating Statistical Plot\n\n"
            f"Data: {data_path.name}\n"
            f"Intent: {intent}",
            border_style="green",
        )
    )

    from paperbanana.core.pipeline import PaperBananaPipeline

    async def _run():
        pipeline = PaperBananaPipeline(settings=settings)
        return await pipeline.generate(gen_input)

    result = asyncio.run(_run())
    console.print(f"\n[green]Done![/green] Plot saved to: [bold]{result.image_path}[/bold]")


@app.command()
def setup():
    """Interactive setup wizard — get generating in 2 minutes with FREE APIs."""
    console.print(
        Panel.fit(
            "[bold]Welcome to PaperBanana Setup[/bold]\n\n"
            "We'll set up FREE API keys so you can start generating diagrams.",
            border_style="yellow",
        )
    )

    console.print("\n[bold]Step 1: Google Gemini API Key[/bold] (FREE, no credit card)")
    console.print("This powers the AI agents that plan and critique your diagrams.\n")

    import webbrowser

    open_browser = Prompt.ask(
        "Open browser to get a free Gemini API key?",
        choices=["y", "n"],
        default="y",
    )
    if open_browser == "y":
        webbrowser.open("https://makersuite.google.com/app/apikey")

    gemini_key = Prompt.ask("\nPaste your Gemini API key")

    # Save to .env
    env_path = Path(".env")
    lines = []
    lines.append(f"GOOGLE_API_KEY={gemini_key}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    console.print(f"\n[green]Setup complete![/green] Keys saved to {env_path}")
    console.print("\nTry it out:")
    console.print(
        "  [bold]paperbanana generate --input method.txt"
        " --caption 'Overview of our framework'[/bold]"
    )


@app.command()
def evaluate(
    generated: str = typer.Option(..., "--generated", "-g", help="Path to generated image"),
    context: str = typer.Option(..., "--context", help="Path to source context text file"),
    caption: str = typer.Option(..., "--caption", "-c", help="Figure caption"),
    reference: str = typer.Option(..., "--reference", "-r", help="Path to human reference image"),
    vlm_provider: str = typer.Option(
        "gemini", "--vlm-provider", help="VLM provider for evaluation"
    ),
):
    """Evaluate a generated diagram vs human reference (comparative)."""
    from paperbanana.evaluation.judge import VLMJudge

    generated_path = Path(generated)
    if not generated_path.exists():
        console.print(f"[red]Error: Generated image not found: {generated}[/red]")
        raise typer.Exit(1)

    reference_path = Path(reference)
    if not reference_path.exists():
        console.print(f"[red]Error: Reference image not found: {reference}[/red]")
        raise typer.Exit(1)

    context_text = Path(context).read_text(encoding="utf-8")

    from dotenv import load_dotenv

    load_dotenv()

    settings = Settings(vlm_provider=vlm_provider)
    from paperbanana.providers.registry import ProviderRegistry

    vlm = ProviderRegistry.create_vlm(settings)

    judge = VLMJudge(vlm)

    async def _run():
        return await judge.evaluate(
            image_path=str(generated_path),
            source_context=context_text,
            caption=caption,
            reference_path=str(reference_path),
        )

    scores = asyncio.run(_run())

    dims = ["faithfulness", "conciseness", "readability", "aesthetics"]
    dim_lines = []
    for dim in dims:
        result = getattr(scores, dim)
        dim_lines.append(f"{dim.capitalize():14s} {result.winner}")

    console.print(
        Panel.fit(
            "[bold]Evaluation Results (Comparative)[/bold]\n\n"
            + "\n".join(dim_lines)
            + f"\n[bold]{'Overall':14s} {scores.overall_winner}[/bold]",
            border_style="cyan",
        )
    )

    for dim in dims:
        result = getattr(scores, dim)
        if result.reasoning:
            console.print(f"\n[bold]{dim}[/bold]: {result.reasoning}")


if __name__ == "__main__":
    app()
